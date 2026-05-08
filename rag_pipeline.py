# ============================================================
# 1. Imports & Configuration
# ============================================================
# standard
import os
import re

# third-party
import numpy as np
import faiss
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, CrossEncoder
from rank_bm25 import BM25Okapi

# local
from cause import CAUSE_KEYWORDS

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"
FAISS_WEIGHT = 0.6
BM25_WEIGHT = 0.4
DEBUG = True
# ============================================================
# 2. Load & Read HTML
# ============================================================
def extract_text_from_html(file_path):
    # Added errors="ignore" so weird web characters don't crash your script
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    # remove useless UI elements (added noscript, svg, form, button)
    for tag in soup(["nav", "footer", "header", "aside", "script", "style", "noscript", "svg", "form", "button"]):
        tag.decompose()

    # focus on main content: target WHO format first, then fallback
    main = soup.find("article", class_="sf-detail-body-wrapper") 
    if not main:
        main = soup.find("main") or soup.find("div", {"role": "main"}) or soup
    return main

def extract_structured_content(soup):
    content = {}
    current_section = "overview"

    # Added 'li' to make sure we extract bullet-point symptoms and prevention steps!
    for tag in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)

        if tag.name in ["h1", "h2", "h3"]:
            current_section = re.sub(r'[^a-z ]', '', text.lower()).strip()
            if current_section not in content:
                content[current_section] = []
        elif current_section:
            # Ignore tiny UI text fragments masquerading as paragraphs
            if len(text.split()) > 3:
                if tag.name == "li" and not text.endswith((".", "!", "?")):
                    text += "."
                if current_section not in content:
                    content[current_section] = []
                content[current_section].append(text)

    return {k: v for k, v in content.items() if v}

# ============================================================
# 3. Text Cleaning & Normalization
# ============================================================
def clean_text(text):
    text = text.replace("\xa0", " ")
    text = text.strip()
    return text


def normalize_text(text: str) -> str:
    text = text.replace("•", " ")
    text = text.replace("–", " ")
    text = text.replace("-", " ")

    # FIX BROKEN SPACED LETTERS
    text = re.sub(r'(?<=\b\w) (?=\w\b)', '', text)

    text = re.sub(r"\d+\.\d+(\.\d+)?", "", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()

def split_sentences(text: str):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]
# ============================================================
# 4. valid chunk filtering (remove very short or irrelevant chunks)
# ============================================================

def is_valid_chunk(text):
    text_lower = text.lower()

    # Lowered from 30 to 15 because medical bullet points can be short but highly relevant
    if len(text.split()) < 15:
        return False

    # Swapped Python keywords for public health website junk keywords
    bad_keywords = [
        "table of contents",
        "subscribe",
        "newsletter",
        "all rights reserved",
        "privacy policy",
        "terms of use",
        "cookie policy",
        "follow us",
        "click here",
        "read more",
        "download pdf",
        "share on",
        "related pages",
        "on this page",
        "content source",
        "page last reviewed",
        "page last updated",
        "skip directly to",
        "share to facebook",
        "share to twitter",
        "official website of the united states"
    ]
    for word in bad_keywords:
        if word in text_lower:
            return False

    return True

# ============================================================
# 5. Chunking Strategy (sentence-based with overlap)
# ============================================================

def build_sentence_chunks(sentences, max_chars=1500, overlap_sentences=3):
    chunks = []
    current = []

    for sent in sentences:
        current.append(sent)

        if len(" ".join(current)) >= max_chars:
            chunks.append(" ".join(current))
            current = current[-overlap_sentences:]

    if current:
        chunks.append(" ".join(current))

    return chunks


chunks = []

HTML_FOLDER = r"C:\projectsforgithub\projectsforgithub\sih_projects.py\health_data"

if os.path.exists(HTML_FOLDER):
    print(f"[*] Reading files from: {HTML_FOLDER}...")
    
    for file in os.listdir(HTML_FOLDER):
        # Handle both .html and .htm files automatically
        if not file.endswith((".html", ".htm")):
            continue

        path = os.path.join(HTML_FOLDER, file)
        
        # Step A: Extract main content area
        main_soup = extract_text_from_html(path)
        if not main_soup:
            continue

        # Step B: Get text organized by headers (Symptoms, Treatment, etc.)
        structured_data = extract_structured_content(main_soup)

        for section, texts_in_section in structured_data.items():
            # Join section text, clean, and normalize
            combined_text = " ".join(texts_in_section)
            normalized = normalize_text(clean_text(combined_text))

            # Step C: Break into sentences then into overlapping chunks
            sentences = split_sentences(normalized)
            page_chunks = build_sentence_chunks(sentences)

            for text_fragment in page_chunks:
                # Step D: Only keep "Valid" medical data
                if is_valid_chunk(text_fragment):
                    chunks.append({
                        # Combine section and text for better embedding search
                        "text": f"Section: {section}. Content: {text_fragment}",
                        "section": section,
                        "source": file
                    })

    #assign IDs ONLY after all valid chunks are collected.                
    for i, chunk in enumerate(chunks):
        chunk["id"] = i
    
    # Create the mapping dictionary for the retriever
    id_to_chunk = {chunk["id"]: chunk for chunk in chunks}
    
    # Extract clean list of strings for FAISS/BM25 indexing
    texts = [c["text"] for c in chunks]

    print(f"[✓] Successfully loaded and indexed {len(chunks)} medical chunks.")

else:
    print(f"[!] ERROR: Folder {HTML_FOLDER} not found. Please create it.")
# ============================================================
# 7. prepare BM25 (for comparison) 
# ============================================================

# Tokenize chunks
def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())
# Build BM25 index
tokenized_chunks = [tokenize(chunk["text"]) for chunk in chunks]
bm25 = BM25Okapi(tokenized_chunks)

print("BM25 index built")

# ============================================================
# 8. Embedding Model For Query and Chunks
# ============================================================
embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME,device="cpu")

def embed_query(text: str):
    return embed_model.encode(
        text,
        normalize_embeddings=True
    )

def embed_chunks(texts: list):
    return embed_model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True
    )


# ============================================================
# 9. Prepare Chunk Texts
# ============================================================
texts = []
valid_chunks = []

for chunk in chunks:
    text = chunk["text"].strip()
    if not text or len(text.split()) < 3:
        continue
    texts.append(text)
    valid_chunks.append(chunk)

if len(texts) == 0:
    raise ValueError("No valid text found — check filtering")

# 👇 THE FIX: Reassign IDs sequentially after filtering!
for i, chunk in enumerate(valid_chunks):
    chunk["id"] = i



# ============================================================
# 10. Embed Chunks
# ============================================================
embeddings = embed_chunks(texts)
embeddings = list(embeddings)

chunks = valid_chunks
id_to_chunk = {chunk["id"]: chunk for chunk in chunks}
assert len(embeddings) == len(chunks)

print(f"Embedded {len(embeddings)} chunks")


# ============================================================
# 8. faiss Index Creation
# ============================================================

# Convert list → numpy matrix
embedding_matrix = np.array(embeddings).astype("float32")

# Get dimension
dim = embedding_matrix.shape[1]

# Create FAISS index (cosine similarity via inner product)
index = faiss.IndexFlatIP(dim)

# Add embeddings to index
index.add(embedding_matrix)              #embedding_matrix[i] ↔ chunks[i]

print(f"FAISS index built with {index.ntotal} vectors")

# ============================================================
# 9. Retrieval (faiss search)
# ============================================================
def retrieve_top_chunks(question, all_chunks, index, top_k=30):
    query_embedding = embed_query(question)
    query_embedding = np.array([query_embedding]).astype("float32")

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx == -1:
            continue
        results.append((all_chunks[idx], score))  # 👈 THIS LINE

    return results

# ============================================================
# 10. STOPWORDS 
# ============================================================

STOPWORDS = {
    "the", "is", "in", "what", "a", "an", "of", "to", "and", "for", "on"
}

# ============================================================
# 11. bm25 search function
# ============================================================

def bm25_search(question, chunks, bm25, top_k=30):
    tokenized_query = [
    word for word in tokenize(question)
    if word not in STOPWORDS
]
    
    scores = bm25.get_scores(tokenized_query)

    if np.max(scores) != 0:
        scores = scores / np.max(scores)

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = [
        (chunks[i], scores[i])
        for i in top_indices
        if i != -1
    ]
    return results


# ============================================================
# 13. Hybrid Retrieval (Combine FAISS + BM25)
# ============================================================

def hybrid_search(question, chunks, index, bm25, id_to_chunk, retrieval_k=30, final_k=10, cause_type=None):
    
    faiss_results = retrieve_top_chunks(question, chunks, index, top_k=retrieval_k)
    bm25_results = bm25_search(question, chunks, bm25, top_k=retrieval_k)

    combined = {}
    seen_ids = set()

    query_lower = question.lower()
    query_words = [
        word for word in tokenize(question)
        if word not in STOPWORDS
    ]

    # Add FAISS scores
    for chunk, score in faiss_results:
        chunk_id = chunk["id"]
        if chunk_id in seen_ids:
            continue
        seen_ids.add(chunk_id)
        combined[chunk_id] = FAISS_WEIGHT * score

    # Add BM25 scores
    for chunk, score in bm25_results:
        chunk_id = chunk["id"]
        if chunk_id in seen_ids:
            if chunk_id in combined:
                combined[chunk_id] += BM25_WEIGHT * score
            continue
        seen_ids.add(chunk_id)
        combined[chunk_id] = combined.get(chunk_id, 0) + BM25_WEIGHT * score
    # boosting +query logic 
    for chunk_id in combined:
        chunk_data = id_to_chunk[chunk_id]
        text_lower = chunk_data["text"].lower()
        section = chunk_data.get("section", "").lower()
        
        # --- STRONG keyword boost ---
        for word in query_words:
            if word in text_lower:
                if word in ["treatment", "therapy", "management"]:
                    combined[chunk_id] += 0.15
                elif word in ["symptoms", "signs"]:
                    combined[chunk_id] += 0.12
                elif word in ["prevention", "prevent"]:
                    combined[chunk_id] += 0.12
                elif word in ["cause", "infection", "virus", "bacteria"]:
                    combined[chunk_id] += 0.1
                else:
                    combined[chunk_id] += 0.05
        
        #  Cause-based boost
        if cause_type:
            for keyword in CAUSE_KEYWORDS.get(cause_type, []):
                if keyword in text_lower:
                    combined[chunk_id] += 0.1

        #  🔥 SECTION BOOST (Massive upgrade) 🔥
        if "symptom" in query_lower and "symptom" in section:
            combined[chunk_id] += 0.2
        if "prevent" in query_lower and "prevention" in section:
            combined[chunk_id] += 0.2
        if "treat" in query_lower and "treatment" in section:
            combined[chunk_id] += 0.2

    # --- FILTERING ---
    filtered = {}
    for chunk_id, score in combined.items():
        text = id_to_chunk[chunk_id]["text"].strip().lower()
        bad_starts = ("and", "but", "so", "or", "however", "thus", "therefore")
        
        if not text or text.startswith(bad_starts) or len(text.split()) < 20:
            continue
        filtered[chunk_id] = score

    if filtered:
        combined = filtered

    # Sort and return
    sorted_ids = sorted(combined.items(), key=lambda x: x[1], reverse=True)            
    final = [(id_to_chunk[chunk_id], score) for chunk_id, score in sorted_ids[:final_k]]
    return final

# ============================================================
# 13. Reranking with Cross-Encoder
# ============================================================

reranker = CrossEncoder(RERANKER_MODEL_NAME,device="cpu")
def rerank_chunks(question, retrieved_results, top_k=5):
    pairs = [
        (question, chunk["text"])
        for chunk, _ in retrieved_results
    ]

    scores = reranker.predict(pairs)

    reranked = list(zip(retrieved_results, scores))

    reranked.sort(key=lambda x: x[1], reverse=True)

    final = [
        (chunk, score)
        for (chunk, _), score in reranked[:top_k]
    ]

    return final


# ============================================================
# 14. Good Prompt Construction 
# ============================================================
def build_health_prompt(query, retrieved_chunks):
    context = ""
    for chunk, _ in retrieved_chunks:
        context += chunk["text"] + "\n\n"

    return f"""
You are a health assistant.

Provide:
- symptoms
- causes
- prevention
- immediate actions

Context:
{context}

Situation:
{query}

Answer clearly and practically.
"""


# ============================================================
# 15. Local LLM Interface (Ollama)
# ============================================================
def ask_llm(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
    ,timeout=60)

    data = response.json()

    if "response" in data:
        return data["response"]

    if "error" in data:
        raise RuntimeError(f"Ollama error: {data['error']}")

    raise RuntimeError(f"Unexpected Ollama response format: {data}")

# ============================================================
# 15. Query Construction for RAG
# ============================================================
def build_query_single(disease, count, location, cause_type):
    query = f"Medical protocol and treatment for {disease}. "

    if cause_type and cause_type != "unknown":
        query += f"The suspected cause is related to {cause_type}. "

    query += f"There are {count} reported cases in {location}. "
    
    # 🔥 KEYWORD BOOST BUILT INTO QUERY
    query += (
        f"Focus on symptoms, causes, prevention, treatment, emergency response, "
        f"outbreak control, and patient management for {disease}."
    )

    return query
# ============================================================
# 15. Query analysis 
# ============================================================
def build_query_from_analysis(user_diseases, predicted_diseases, analysis):
    lines = []

    for d in analysis.get("diseases", []):
        line = "- " + d["standard"] + ": " + str(d["count"])
        lines.append(line)

    counts_text = "\n".join(lines)

    dominant = analysis.get("dominant_disease", {}).get("standard", "")
    location = analysis.get("location", "unknown")
    risk = analysis.get("risk_level", "unknown")

    remaining_user = [d for d in user_diseases if d != dominant]
    remaining_text = ", ".join(remaining_user) if remaining_user else "None"

    predicted_text = ", ".join(predicted_diseases) if predicted_diseases else "None"

    return f"""
Public health situation:

Location: {location}
Risk Level: {risk}

Disease counts:
{counts_text}

PRIMARY DISEASE (system determined):
{dominant}

USER-REPORTED DISEASES (excluding primary):
{remaining_text}

SYSTEM-PREDICTED ADDITIONAL RISKS:
{predicted_text}

Generate a structured response EXACTLY like this:

PRIMARY THREAT:
- Disease: {dominant}
- MUST use this disease
- Symptoms:
- Prevention:
- Immediate Actions:

USER-REPORTED DISEASES:
- Cover ALL diseases listed above
- Each must include:
  - Symptoms
  - Prevention
  - Actions

PREDICTED RISKS:
- Cover ALL predicted diseases
- Short explanation
- Clearly mark them as predicted

RULES:
- DO NOT skip any disease
- DO NOT repeat diseases
- DO NOT change primary disease
- DO NOT mix sections
"""
# ============================================================
# 15. End-to-End RAG Execution
# ============================================================
def run_rag_pipeline(question,cause_type=None):
    # Step 1: Get candidate chunks using hybrid search (FAISS + BM25)
    hybrid_results = hybrid_search(
        question=question,
        chunks=chunks,
        index=index,
        bm25=bm25,
        id_to_chunk=id_to_chunk,
        retrieval_k=30,
        final_k=4,
        cause_type = cause_type
    )
    
    # Step 2: Rerank those candidates using cross-encoder for better relevance
    reranked_results = rerank_chunks(
        question=question,
        retrieved_results=hybrid_results,
        top_k=5
    )

    # =========================
    # RERANKER CONFIDENCE CHECK
    # =========================
    top_scores = [score for _, score in reranked_results[:3]]


    if DEBUG:
        print("\n--- HYBRID RESULTS ---")

        for i, (chunk, score) in enumerate(hybrid_results):
            print(f"\n[{i+1}] Score: {score:.4f}")
            print(f"Source: {chunk['source']}")
            print(f"Section: {chunk.get('section', 'unknown')}")
            print(chunk["text"][:500])

        print("\n--- RERANKED RESULTS ---")

        for i, (chunk, score) in enumerate(reranked_results):
            print(f"\n[{i+1}] Score: {score:.4f}")
            print(f"Source: {chunk['source']}")
            print(f"Section: {chunk.get('section', 'unknown')}")
            print(chunk["text"][:500])

    # --- retrieval quality check ---
    top_scores = [score for _, score in reranked_results[:3]]

    if not reranked_results:
        retrieval_status = "none"

    elif len(top_scores) > 1 and abs(top_scores[0] - top_scores[1]) < 0.2:
        retrieval_status = "weak"

    else:
        retrieval_status = "good"
    # --- prompt selection & LLM call ---
    if retrieval_status == "none":
        prompt = f"""
        A health situation has been reported: {question}
        Provide: possible causes, risks, and immediate actions based on general medical knowledge.
        """
        answer = ask_llm(prompt)
        return answer, []

    elif retrieval_status == "weak":
        context = "\n\n".join([chunk["text"] for chunk, _ in reranked_results])
        prompt = f"""
        You are a health assistant. Use the context if helpful, but you may also use your own knowledge.
        
        Context: 
        {context}
        
        Situation: {question}
        Provide: symptoms, causes, prevention, immediate actions.
        """
        answer = ask_llm(prompt)
        return answer, reranked_results

    else: # "good" status
        prompt = build_health_prompt(question, reranked_results)
        answer = ask_llm(prompt)
        return answer, reranked_results
        
if __name__ == "__main__":

    query = """
    Multiple cholera cases reported after flood contamination.
    Patients show diarrhea, vomiting, and dehydration.
    """

    answer, results = run_rag_pipeline(
        question=query,
        cause_type="flood"
    )

    print("\n=== FINAL ANSWER ===\n")
    print(answer)
