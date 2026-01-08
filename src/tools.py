from langchain_core.tools import tool
from src.data_loader import load_vector_store, get_db_connection

_store = None

def _get_store():
    global _store
    if _store is None:
        _store = load_vector_store()
    return _store

@tool
def search_faq(query: str) -> str:
    """Search FAQ for policy, process, how-to, troubleshooting questions.
    
    Args:
        query: Natural language question
    """
    results = _get_store().similarity_search(query, k=3)
    if not results:
        return "No relevant FAQ found."
    return "\n---\n".join([d.page_content for d in results])

@tool  
def query_customers(sql: str) -> str:
    """Execute SQL on customers table for statistics, pricing, counts.
    
    Table: customers
    Columns: customer_id, gender, senior_citizen(0/1), partner(Yes/No), dependents(Yes/No),
    tenure(months), phone_service(Yes/No), multiple_lines(Yes/No), 
    internet_service(DSL/Fiber optic/No), online_security(Yes/No), online_backup(Yes/No),
    device_protection(Yes/No), tech_support(Yes/No), streaming_tv(Yes/No), 
    streaming_movies(Yes/No), contract(Month-to-month/One year/Two year),
    paperless_billing(Yes/No), payment_method, monthly_charges, total_charges, churn(Yes/No)
    
    Args:
        sql: SQLite SELECT query
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Only SELECT queries allowed."
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        conn.close()
        
        if not rows:
            return "No results."
        
        result = " | ".join(cols) + "\n"
        for row in rows[:15]:
            result += " | ".join(str(v) for v in row) + "\n"
        if len(rows) > 15:
            result += f"... ({len(rows)} total rows)"
        return result
    except Exception as e:
        return f"SQL Error: {e}"

@tool
def get_stats() -> str:
    """Get customer base overview statistics."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    stats = []
    cur.execute("SELECT COUNT(*) FROM customers")
    stats.append(f"Total: {cur.fetchone()[0]} customers")
    
    cur.execute("SELECT ROUND(AVG(monthly_charges),2), MIN(monthly_charges), MAX(monthly_charges) FROM customers")
    r = cur.fetchone()
    stats.append(f"Monthly charges: avg ${r[0]}, range ${r[1]}-${r[2]}")
    
    cur.execute("SELECT contract, COUNT(*) FROM customers GROUP BY contract")
    stats.append(f"Contracts: {dict(cur.fetchall())}")
    
    cur.execute("SELECT internet_service, COUNT(*) FROM customers GROUP BY internet_service")
    stats.append(f"Internet: {dict(cur.fetchall())}")
    
    cur.execute("SELECT churn, COUNT(*) FROM customers GROUP BY churn")
    stats.append(f"Churn: {dict(cur.fetchall())}")
    
    conn.close()
    return "\n".join(stats)

TOOLS = [search_faq, query_customers, get_stats]
