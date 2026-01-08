import csv
import sqlite3
from pathlib import Path
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from src.config import get_settings

settings = get_settings()
DATA_DIR = Path(settings.data_dir)
DB_PATH = DATA_DIR / "telecom.db"

def init_sqlite_db():
    """Initialize SQLite with cleaned customer data."""
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            gender TEXT,
            senior_citizen INTEGER,
            partner TEXT,
            dependents TEXT,
            tenure INTEGER,
            phone_service TEXT,
            multiple_lines TEXT,
            internet_service TEXT,
            online_security TEXT,
            online_backup TEXT,
            device_protection TEXT,
            tech_support TEXT,
            streaming_tv TEXT,
            streaming_movies TEXT,
            contract TEXT,
            paperless_billing TEXT,
            payment_method TEXT,
            monthly_charges REAL,
            total_charges REAL,
            churn TEXT
        )
    """)
    
    with open(DATA_DIR / "customers.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cur.execute("""
                INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                row["customerID"], row["gender"], int(row["SeniorCitizen"]),
                row["Partner"], row["Dependents"], int(row["tenure"]),
                row["PhoneService"], row["MultipleLines"], row["InternetService"],
                row["OnlineSecurity"], row["OnlineBackup"], row["DeviceProtection"],
                row["TechSupport"], row["StreamingTV"], row["StreamingMovies"],
                row["Contract"], row["PaperlessBilling"], row["PaymentMethod"],
                float(row["MonthlyCharges"]), float(row["TotalCharges"]), row["Churn"]
            ))
    conn.commit()
    conn.close()

def load_faq_docs():
    """Load FAQ as documents."""
    docs = []
    with open(DATA_DIR / "qna.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            docs.append(Document(
                page_content=f"Q: {row['question'].strip()}\nA: {row['answer'].strip()}",
                metadata={"source": "faq"}
            ))
    return docs

def build_vector_store():
    """Build FAISS index from FAQ."""
    index_path = DATA_DIR / "faiss_index"
    if index_path.exists():
        import shutil
        shutil.rmtree(index_path)
    
    docs = load_faq_docs()
    emb = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    store = FAISS.from_documents(docs, emb)
    store.save_local(str(index_path))
    return store

def load_vector_store():
    """Load FAISS index."""
    index_path = DATA_DIR / "faiss_index"
    emb = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    if index_path.exists():
        return FAISS.load_local(str(index_path), emb, allow_dangerous_deserialization=True)
    return build_vector_store()

def get_db_connection():
    """Get SQLite connection."""
    if not DB_PATH.exists():
        init_sqlite_db()
    return sqlite3.connect(DB_PATH)
