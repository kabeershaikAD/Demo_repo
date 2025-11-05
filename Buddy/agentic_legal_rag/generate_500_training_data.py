#!/usr/bin/env python3
"""
Generate 500+ training examples for query booster
"""

import os
import sys
import json
import random
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bootstrap_dataset import QueryBootstrapGenerator

def generate_500_training_examples():
    """Generate 500+ training examples for query booster"""
    print("🚀 Generating 500+ Training Examples for Query Booster")
    print("=" * 60)
    
    # Comprehensive list of Indian legal queries
    legal_queries = [
        # Constitutional Law
        "377 rights", "privacy article", "fundamental rights", "article 21 right to life",
        "article 14 equality", "article 19 freedom of speech", "article 32 writ jurisdiction",
        "constitutional validity", "basic structure doctrine", "emergency provisions",
        "president powers", "parliamentary privileges", "judicial review",
        
        # Criminal Law - IPC
        "murder punishment", "theft ipc", "fraud criminal", "assault battery",
        "criminal conspiracy", "abetment", "attempt to murder", "culpable homicide",
        "kidnapping abduction", "rape laws", "dowry death", "domestic violence",
        "cyber crime", "money laundering", "terrorism laws", "sedition law",
        "contempt of court", "perjury", "forgery", "cheating",
        
        # Criminal Procedure
        "bail provisions", "anticipatory bail", "arrest procedure", "police custody",
        "judicial custody", "remand", "charge sheet", "criminal trial",
        "evidence collection", "witness protection", "plea bargaining", "appeal process",
        "revision petition", "criminal revision", "quashing of FIR",
        
        # Civil Law
        "contract breach", "specific performance", "damages", "injunction",
        "civil procedure", "limitation period", "res judicata", "lis pendens",
        "execution proceedings", "attachment", "receiver appointment",
        
        # Family Law
        "divorce grounds", "alimony maintenance", "child custody", "adoption laws",
        "guardianship", "marriage registration", "nullity of marriage", "restitution of conjugal rights",
        "domestic violence act", "dowry prohibition", "maintenance under 125 crpc",
        
        # Property Law
        "property transfer", "sale deed", "gift deed", "will probate",
        "succession law", "inheritance rights", "partition suit", "adverse possession",
        "easement rights", "lease agreement", "mortgage foreclosure",
        
        # Labour Law
        "industrial disputes", "worker rights", "minimum wages", "bonus payment",
        "gratuity", "provident fund", "maternity benefits", "termination of employment",
        "retrenchment", "layoff", "strike lockout", "trade union rights",
        
        # Consumer Law
        "consumer protection", "defective goods", "deficiency in service", "unfair trade practices",
        "consumer forum", "compensation claim", "product liability", "warranty rights",
        
        # Tax Law
        "income tax", "gst compliance", "tax evasion", "tax assessment",
        "appeal against assessment", "penalty proceedings", "tax deduction", "tds provisions",
        "advance tax", "refund claim", "tax audit", "transfer pricing",
        
        # Environmental Law
        "environmental protection", "pollution control", "forest conservation", "wildlife protection",
        "environmental clearance", "carbon credits", "renewable energy", "climate change laws",
        
        # Corporate Law
        "company incorporation", "board meetings", "shareholder rights", "merger acquisition",
        "insolvency bankruptcy", "winding up", "director liability", "corporate governance",
        "securities law", "stock exchange", "mutual funds", "insurance law",
        
        # Intellectual Property
        "patent law", "trademark registration", "copyright protection", "design registration",
        "geographical indication", "trade secrets", "infringement", "licensing agreement",
        
        # Administrative Law
        "administrative tribunals", "quasi judicial", "administrative discretion", "bias in decision making",
        "natural justice", "audi alteram partem", "nemo judex in causa sua", "legitimate expectation",
        
        # Banking Law
        "banking regulations", "rbi guidelines", "loan recovery", "sarfesi act",
        "banking ombudsman", "credit card disputes", "home loan", "personal loan",
        
        # Real Estate Law
        "real estate regulation", "rera act", "builder buyer agreement", "possession delay",
        "construction defects", "maintenance charges", "society formation", "flat purchase",
        
        # Medical Law
        "medical negligence", "consumer protection medical", "clinical trials", "drug regulations",
        "medical ethics", "patient rights", "informed consent", "medical malpractice",
        
        # Education Law
        "right to education", "reservation policy", "admission process", "examination malpractices",
        "university regulations", "student rights", "teacher appointment", "academic freedom",
        
        # Media Law
        "freedom of press", "defamation", "contempt of court", "obscenity laws",
        "broadcasting regulations", "social media laws", "fake news", "privacy rights",
        
        # International Law
        "extradition", "refugee law", "international treaties", "diplomatic immunity",
        "human rights", "international arbitration", "trade agreements", "investment protection",
        
        # Technology Law
        "data protection", "privacy laws", "cyber security", "digital signatures",
        "e-commerce", "online contracts", "cryptocurrency", "blockchain law",
        
        # Specific Acts and Sections
        "section 302 ipc", "section 124a ipc", "section 498a ipc", "section 420 ipc",
        "section 138 negotiable instruments", "section 138 ni act", "section 138 cheque bounce",
        "article 21 constitution", "article 14 constitution", "article 19 constitution",
        "section 125 crpc", "section 438 crpc", "section 439 crpc", "section 482 crpc",
        "section 138 negotiable instruments act", "section 138 ni act", "section 138 cheque",
        
        # Court Procedures
        "supreme court", "high court", "district court", "family court",
        "consumer court", "labour court", "industrial tribunal", "administrative tribunal",
        "writ petition", "special leave petition", "civil appeal", "criminal appeal",
        "revision petition", "review petition", "curative petition",
        
        # Legal Concepts
        "burden of proof", "standard of proof", "presumption of innocence", "beyond reasonable doubt",
        "preponderance of probability", "res ipsa loquitur", "stare decisis", "obiter dicta",
        "ratio decidendi", "per incuriam", "sub silentio", "distinguishing cases",
        
        # Remedies
        "injunction", "specific performance", "damages", "restitution",
        "declaratory relief", "mandatory injunction", "prohibitory injunction", "temporary injunction",
        "permanent injunction", "interim relief", "stay order", "status quo",
        
        # Evidence
        "documentary evidence", "oral evidence", "expert evidence", "circumstantial evidence",
        "hearsay evidence", "dying declaration", "confession", "admission",
        "burden of proof", "onus of proof", "presumption", "rebuttable presumption",
        
        # Limitation
        "limitation period", "limitation act", "time barred", "condonation of delay",
        "sufficient cause", "acknowledgment", "part payment", "fresh period",
        
        # Specific Legal Terms
        "locus standi", "cause of action", "joinder of parties", "misjoinder",
        "non-joinder", "necessary parties", "proper parties", "representative suit",
        "class action", "public interest litigation", "pil", "writ jurisdiction",
        
        # Property Rights
        "easement", "license", "lease", "tenancy", "rent control", "eviction",
        "adverse possession", "prescription", "customary rights", "tribal rights",
        
        # Human Rights
        "right to life", "right to liberty", "right to equality", "right to dignity",
        "right to privacy", "right to information", "right to education", "right to work",
        "right to health", "right to housing", "right to food", "right to water",
        
        # Gender Laws
        "sexual harassment", "domestic violence", "dowry prohibition", "equal pay",
        "maternity benefits", "paternity leave", "gender equality", "women's rights",
        
        # Child Rights
        "child protection", "child labor", "juvenile justice", "adoption",
        "guardianship", "custody", "maintenance", "education rights",
        
        # Senior Citizen Rights
        "senior citizen act", "maintenance of parents", "elder abuse", "pension rights",
        "healthcare rights", "housing rights", "social security", "welfare schemes",
        
        # Disability Rights
        "persons with disabilities act", "accessibility rights", "employment reservation",
        "education rights", "healthcare rights", "social security", "reasonable accommodation",
        
        # Minority Rights
        "minority rights", "religious freedom", "cultural rights", "educational rights",
        "linguistic rights", "constitutional safeguards", "special provisions", "reservation",
        
        # Tribal Rights
        "tribal rights", "forest rights act", "panchayat extension", "scheduled areas",
        "tribal land", "traditional rights", "customary law", "tribal autonomy",
        
        # Rural Development
        "panchayati raj", "rural development", "agricultural laws", "land reforms",
        "cooperative societies", "rural employment", "mgnrega", "pradhan mantri schemes",
        
        # Urban Development
        "municipal laws", "urban planning", "building regulations", "zoning laws",
        "environmental clearance", "traffic laws", "public transport", "infrastructure",
        
        # Health Laws
        "public health", "epidemic diseases act", "food safety", "drug control",
        "clinical trials", "medical ethics", "patient rights", "healthcare regulation",
        
        # Education Laws
        "right to education act", "education policy", "reservation in education",
        "private education", "deemed universities", "technical education", "vocational training",
        
        # Employment Laws
        "employment law", "labor relations", "industrial relations", "trade unions",
        "collective bargaining", "strike rights", "lockout", "retrenchment",
        
        # Social Security
        "social security", "pension schemes", "provident fund", "gratuity",
        "maternity benefits", "sick leave", "annual leave", "overtime",
        
        # Financial Laws
        "banking law", "securities law", "insurance law", "mutual funds",
        "pension funds", "credit rating", "financial markets", "derivatives",
        
        # Competition Law
        "competition act", "anti-competitive practices", "abuse of dominance",
        "cartel", "merger control", "competition commission", "fair trade",
        
        # Consumer Protection
        "consumer rights", "defective products", "deficiency in service",
        "unfair trade practices", "consumer forum", "compensation", "product liability",
        
        # Environmental Protection
        "environmental law", "pollution control", "forest conservation",
        "wildlife protection", "climate change", "renewable energy", "carbon credits",
        
        # Technology and Digital
        "cyber law", "data protection", "privacy rights", "digital signatures",
        "e-commerce", "online contracts", "cryptocurrency", "blockchain",
        
        # International Law
        "international treaties", "extradition", "refugee law", "human rights",
        "international arbitration", "trade law", "investment protection", "diplomatic law",
        
        # Alternative Dispute Resolution
        "arbitration", "mediation", "conciliation", "negotiation",
        "lok adalat", "fast track courts", "online dispute resolution", "adr mechanisms",
        
        # Legal Aid
        "legal aid", "free legal services", "legal aid society", "pro bono",
        "legal awareness", "legal literacy", "access to justice", "legal empowerment",
        
        # Court Management
        "case management", "docket management", "judicial administration", "court procedures",
        "case flow management", "judicial statistics", "court technology", "e-courts",
        
        # Legal Profession
        "advocate act", "bar council", "professional ethics", "disciplinary proceedings",
        "legal education", "law schools", "bar examination", "continuing legal education",
        
        # Legal Research
        "legal research", "case law", "statutory interpretation", "precedent",
        "legal writing", "legal citation", "legal databases", "legal technology",
        
        # Legal Ethics
        "legal ethics", "professional conduct", "conflict of interest", "attorney-client privilege",
        "confidentiality", "duty of care", "fiduciary duty", "professional responsibility",
        
        # Legal Reform
        "legal reform", "law commission", "legislative process", "policy making",
        "regulatory framework", "compliance", "governance", "transparency",
        
        # Access to Justice
        "access to justice", "legal aid", "pro bono services", "legal awareness",
        "judicial activism", "public interest litigation", "social justice", "equality before law"
    ]
    
    # Generate additional queries by combining terms
    additional_queries = []
    legal_terms = ["rights", "laws", "act", "provisions", "punishment", "procedure", "court", "judgment"]
    subjects = ["criminal", "civil", "constitutional", "family", "property", "labour", "consumer", "tax"]
    
    for subject in subjects:
        for term in legal_terms:
            additional_queries.append(f"{subject} {term}")
    
    # Combine all queries
    all_queries = legal_queries + additional_queries
    
    # Remove duplicates and shuffle
    unique_queries = list(set(all_queries))
    random.shuffle(unique_queries)
    
    # Take first 500 queries
    selected_queries = unique_queries[:500]
    
    print(f"📊 Selected {len(selected_queries)} unique queries for training data generation")
    
    # Initialize generator
    generator = QueryBootstrapGenerator(use_gpt_refinement=False)
    
    # Generate training data
    print("🔄 Generating training data...")
    training_data = []
    
    for i, query in enumerate(selected_queries, 1):
        try:
            decision = generator.process_query(query)
            training_data.append(decision)
            if i % 50 == 0:
                print(f"Processed {i}/{len(selected_queries)} queries...")
        except Exception as e:
            print(f"Error processing query '{query}': {e}")
            continue

    # Save the dataset
    output_file = "data/query_booster_500.jsonl"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in training_data:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"✅ Generated {len(training_data)} training examples")
    print(f"💾 Saved to data/query_booster_500.jsonl")
    
    # Analyze the generated data
    print("\n📈 Training Data Analysis:")
    
    # Count by retrieval mode
    modes = {}
    boost_ratios = []
    confidence_scores = []
    
    for item in training_data:
        mode = item.get('retrieval_mode', 'unknown')
        modes[mode] = modes.get(mode, 0) + 1
        
        if item.get('need_boost', False):
            boost_ratios.append(1)
        else:
            boost_ratios.append(0)
        
        confidence_scores.append(item.get('confidence', 0))
    
    print(f"   Retrieval Modes: {modes}")
    print(f"   Boost Ratio: {sum(boost_ratios)/len(boost_ratios):.2%}")
    print(f"   Average Confidence: {sum(confidence_scores)/len(confidence_scores):.2f}")
    
    # Show sample entries
    print(f"\n📋 Sample Training Entries:")
    for i, item in enumerate(training_data[:5]):
        print(f"   {i+1}. Query: {item['query']}")
        print(f"      Boosted: {item['boosted_query'][:60]}...")
        print(f"      Mode: {item['retrieval_mode']}, K: {item['top_k']}")
        print()
    
    return training_data

if __name__ == "__main__":
    generate_500_training_examples()
