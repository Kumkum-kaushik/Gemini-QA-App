import requests
from bs4 import BeautifulSoup
from typing import List
from dotenv import load_dotenv
import os
import google.generativeai as genai

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


# -------------------------
# 1. Gemini Setup
# -------------------------
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please add it in your .env file.")

genai.configure(api_key=GEMINI_KEY)


def query_gemini(prompt: str) -> str:
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text


# -------------------------
# 2. Simple Web Loader (FIXED with User-Agent)
# -------------------------
def load_urls_simple(urls: List[str]):
    docs = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()  # ensure valid response

            soup = BeautifulSoup(r.text, "html.parser")
            content = soup.get_text(" ", strip=True)

            docs.append(Document(page_content=content, metadata={"source": url}))

        except Exception as e:
            print(f"Error loading {url}: {e}")

    return docs


# -------------------------
# 3. Retriever Builder
# -------------------------
def build_retriever(urls: List[str]):
    docs = load_urls_simple(urls)
    if not docs:
        return None

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(docs, embeddings)
    return vectorstore.as_retriever()


# -------------------------
# 4. Full QA Pipeline
# -------------------------
def answer_question(question: str, retriever):
    if retriever is None:
        return "Retriever not ready.", []

    # New LangChain API
    retrieved = retriever.invoke(question)

    if not retrieved:
        return "No relevant context found.", []

    context = "\n".join([doc.page_content for doc in retrieved])

    prompt = f"""
You are an AI that answers questions using the given context.

Context:
{context}

Question: {question}
Answer clearly:
"""

    answer = query_gemini(prompt)
    sources = [doc.metadata["source"] for doc in retrieved]

    return answer, sources
