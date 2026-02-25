import os
import json
import sqlite3
import re
import time
import pandas as pd
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from evaluate import load
import openai

from langchain_chroma import Chroma  # ✅ UPDATED IMPORT
from langchain_huggingface import HuggingFaceEmbeddings

# ========== CONFIG ========== #
openai.api_key = "your_openai_key"  # ✅ Put your real key here
DB_PATH = os.path.abspath("../law_buddy.db")  # ✅ Ensure correct path
CHROMA_DB_PATH = os.path.abspath("../chroma_db_")
TOP_K = 3

# ========== LOAD MODELS ========== #
bleu = load("bleu")
rouge = load("rouge")
exact_match = load("exact_match")

embedder = SentenceTransformer("all-MiniLM-L6-v2")

embedding_function = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)

vectordb = Chroma(
    persist_directory=CHROMA_DB_PATH,
    embedding_function=embedding_function,
    collection_name="vector_database"
)

# ========== Ensure DB Exists & Table ========== #
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create table if missing
cursor.execute("""
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    query TEXT,
    response TEXT,
    timestamp DATETIME,
    is_voice BOOLEAN,
    category TEXT,
    satisfaction_score INTEGER,
    response_time REAL
)
""")
conn.commit()

cursor.execute("SELECT query, response FROM conversations")
data = cursor.fetchall()

if not data:
    print("⚠️ No data found in 'conversations'. Make sure to interact with Law Buddy first.")
    exit()

# ========== Load Reference Answers ========== #
ref_answers = {}
with open("reference_answers.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        ref_answers[item["query"].strip().lower()] = item["ideal_answer"].strip()

# ========== Utilities ========== #
def clean(text):
    text = re.sub(r"\*\*.*?\*\*", "", text)
    text = re.sub(r"Disclaimer:.*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[\n\t\r•*→-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def gpt_eval(query, answer, reference):
    prompt = f"""Rate the following answer.

Query: {query}
Answer: {answer}
Reference: {reference}

Give a JSON like:
{{
"relevance": 0-1,
"groundedness": 0-1,
"context_relevance": 0-1
}}"""
    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a legal QA evaluator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return json.loads(res["choices"][0]["message"]["content"])
    except Exception as e:
        print("⚠️ GPT error:", e)
        return {"relevance": None, "groundedness": None, "context_relevance": None}

# ========== Evaluation ========== #
results = []

for query, response in tqdm(data, desc="Evaluating"):
    q = query.strip().lower()
    if q not in ref_answers:
        continue

    ref = clean(ref_answers[q])
    pred_clean = clean(response)

    # Cosine sim
    query_vec = embedder.encode(query, convert_to_tensor=True)
    pred_vec = embedder.encode(pred_clean, convert_to_tensor=True)
    sim = util.pytorch_cos_sim(pred_vec, query_vec).item()

    # BLEU, ROUGE, EM
    bleu_score = bleu.compute(predictions=[pred_clean], references=[[ref]])["bleu"]
    rouge_score = rouge.compute(predictions=[pred_clean], references=[ref])
    em_score = exact_match.compute(predictions=[pred_clean], references=[ref])["exact_match"]

    # Token overlap
    pred_tokens = set(pred_clean.split())
    ref_tokens = set(ref.split())
    token_acc = len(pred_tokens & ref_tokens) / max(1, len(ref_tokens))

    # Vector search metrics
    retrieved = vectordb.similarity_search_with_score(query, k=TOP_K)
    hit = any(ref[:20].lower() in doc.page_content.lower() for doc, _ in retrieved)
    mrr = 0
    for i, (doc, _) in enumerate(retrieved):
        if ref[:20].lower() in doc.page_content.lower():
            mrr = 1 / (i + 1)
            break

    # GPT Evaluation
    gpt_scores = gpt_eval(query, pred_clean, ref)

    results.append({
        "Query": query,
        "Prediction": response,
        "Reference": ref,
        "Cosine Similarity": sim,
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
        "Context Relevance (GPT)": gpt_scores["context_relevance"]
    })

# ========== Save ========== #
df = pd.DataFrame(results)
filename = "evaluation_report_chroma.csv"

# Check if file exists, then append or write
if os.path.exists(filename):
    existing_df = pd.read_csv(filename)
    combined_df = pd.concat([existing_df, df], ignore_index=True)
    combined_df.to_csv(filename, index=False)
    print(f"✅ Appended to existing evaluation file: {filename}")
else:
    df.to_csv(filename, index=False)
    print(f"✅ Created new evaluation file: {filename}")

print("✅ Evaluation report saved as evaluation_report_chroma.csv")
