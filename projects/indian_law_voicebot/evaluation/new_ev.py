import os
import json
import sqlite3
import re
import time
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from evaluate import load
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Optional: Enable BERTScore
USE_BERTSCORE = True
if USE_BERTSCORE:
    from bert_score import score as bert_score

# Set OpenAI API Key
#openai.api_key = "YOUR_OPENAI_API_KEY_HERE"  # Replace with your real key

# Constants
CHROMA_DB_PATH = "../chroma_db_"
REFERENCE_FILE = "reference_answers.jsonl"
DB_PATH = "../law_buddy.db"
TOP_K = 3

# Load scorers
bleu = load("bleu")
rouge = load("rouge")
exact_match = load("exact_match")

# Load embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Load Chroma vector DB
embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)
vectordb = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=embedding_function,
    collection_name="vector_database"
)

# Load reference answers
ref_answers = {}
with open(REFERENCE_FILE, "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        query_key = item["query"].strip().lower()
        ref_answers[query_key] = item["ideal_answer"].strip()

# Load responses from DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT query, response FROM conversations")
data = cursor.fetchall()

# Clean text function
def clean(text):
    text = re.sub(r"\*\*.*?\*\*", "", text)
    text = re.sub(r"Disclaimer:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\n\t\r\u2022\*\u2192\-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# GPT-based scoring
def gpt_eval(query, answer, reference):
    prompt = f"""
Query: {query}
Answer: {answer}
Reference: {reference}

Give a JSON object with these fields between 0 and 1:
{{
  "relevance": float,
  "groundedness": float,
  "context_relevance": float
}}
"""
    try:
         
         client = OpenAI(api_key="YOUR_OPENAI_API_KEY_HERE")  # Your real key here

         res = client.chat.completions.create(
         model="gpt-3.5-turbo",
         messages=[
         {"role": "system", "content": "You are a legal QA evaluator."},
         {"role": "user", "content": prompt}
           ]     ,
           temperature=0
            )
         content = res.choices[0].message.content
         scores = json.loads(content)
         return {
            "relevance": float(scores.get("relevance", 0)),
            "groundedness": float(scores.get("groundedness", 0)),
            "context_relevance": float(scores.get("context_relevance", 0))
        }
    except Exception as e:
        print(f"⚠️ GPT error: {e}")
        return {"relevance": 0, "groundedness": 0, "context_relevance": 0}

# Run evaluation
results = []

for query, response in tqdm(data):
    q_key = query.strip().lower()
    if q_key not in ref_answers:
        continue

    ref = clean(ref_answers[q_key])
    pred = clean(response)

    # Embedding-based Cosine Similarity
    q_vec = embedder.encode(query, convert_to_tensor=True)
    a_vec = embedder.encode(pred, convert_to_tensor=True)
    cosine_sim = util.pytorch_cos_sim(a_vec, q_vec).item()

    # BLEU, ROUGE, EM
    bleu_score = bleu.compute(predictions=[pred], references=[[ref]])["bleu"]
    rouge_score = rouge.compute(predictions=[pred], references=[ref])
    em_score = exact_match.compute(predictions=[pred], references=[ref])["exact_match"]

    # Token overlap
    pred_tokens = set(pred.split())
    ref_tokens = set(ref.split())
    token_acc = len(pred_tokens & ref_tokens) / max(1, len(ref_tokens))

    # Chroma Hit@3 and MRR
    retrieved = vectordb.similarity_search_with_score(query, k=TOP_K)
    hit = any(ref[:20].lower() in doc.page_content.lower() for doc, _ in retrieved)
    mrr = 0
    for i, (doc, _) in enumerate(retrieved):
        if ref[:20].lower() in doc.page_content.lower():
            mrr = 1 / (i + 1)
            break

    # GPT scores
    print(f"\n🔍 Evaluating: {query[:80]}...")
    gpt_scores = gpt_eval(query, pred, ref)

    # Optional BERTScore
    bert_p, bert_r, bert_f1 = 0, 0, 0
    if USE_BERTSCORE:
        P, R, F1 = bert_score([pred], [ref], lang="en", verbose=False)
        bert_p, bert_r, bert_f1 = P.item(), R.item(), F1.item()

    results.append({
        "Query": query,
        "Prediction": response,
        "Reference": ref,
        "Cosine Similarity": cosine_sim,
        "BLEU": bleu_score,
        "ROUGE-1": rouge_score["rouge1"],
        "ROUGE-2": rouge_score["rouge2"],
        "ROUGE-L": rouge_score["rougeL"],
        "Exact Match": em_score,
        "Token Overlap Accuracy": token_acc,
        "Hit@3": int(hit),
        "MRR@3": mrr,
        "Answer Relevance (GPT)": gpt_scores["relevance"],
        "Groundedness (GPT)": gpt_scores["groundedness"],
        "Context Relevance (GPT)": gpt_scores["context_relevance"],
        "BERTScore-F1": bert_f1,
        "BERTScore-P": bert_p,
        "BERTScore-R": bert_r
    })

# Save report
df = pd.DataFrame(results)
df.to_csv("evaluation_report_chroma.csv", index=False)
print("✅ Saved to evaluation_report_chroma.csv")
