#!/usr/bin/env python3
"""Comprehensive test suite for Hybrid Telecom Agent."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_config():
    """Test configuration loading."""
    from src.config import get_settings
    settings = get_settings()
    
    assert settings.groq_api_key, "GROQ_API_KEY not set"
    assert settings.llm_model == "openai/gpt-oss-120b", f"Wrong model: {settings.llm_model}"
    assert settings.aws_region == "ap-south-1", f"Wrong region: {settings.aws_region}"
    assert Path(settings.data_dir).exists(), "Data dir missing"
    
    print("✓ Config tests passed")

def test_data_files():
    """Test data file existence and integrity."""
    from src.config import get_settings
    import pandas as pd
    
    settings = get_settings()
    data_dir = Path(settings.data_dir)
    
    # Check customers.csv
    customers_path = data_dir / "customers.csv"
    assert customers_path.exists(), "customers.csv missing"
    df = pd.read_csv(customers_path)
    assert len(df) == 7043, f"Expected 7043 customers, got {len(df)}"
    assert df.isnull().sum().sum() == 0, "Null values in customers.csv"
    assert "customerID" in df.columns, "customerID column missing"
    
    # Check qna.csv
    qna_path = data_dir / "qna.csv"
    assert qna_path.exists(), "qna.csv missing"
    qna = pd.read_csv(qna_path)
    assert len(qna) >= 200, f"Expected 200+ FAQ, got {len(qna)}"
    assert qna.isnull().sum().sum() == 0, "Null values in qna.csv"
    assert "question" in qna.columns and "answer" in qna.columns, "Missing columns in qna.csv"
    
    # Check no "Lauki" branding
    lauki_count = qna['question'].str.contains('Lauki', case=False).sum()
    lauki_count += qna['answer'].str.contains('Lauki', case=False).sum()
    assert lauki_count == 0, f"Found {lauki_count} 'Lauki' mentions - should be removed"
    
    print("✓ Data files tests passed")

def test_database():
    """Test SQLite database."""
    from src.data_loader import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
    assert cur.fetchone(), "customers table missing"
    
    # Check row count
    cur.execute("SELECT COUNT(*) FROM customers")
    assert cur.fetchone()[0] == 7043, "Wrong customer count"
    
    # Check columns
    cur.execute("PRAGMA table_info(customers)")
    cols = [row[1] for row in cur.fetchall()]
    required = ['customer_id', 'gender', 'tenure', 'monthly_charges', 'churn']
    for col in required:
        assert col in cols, f"Column {col} missing"
    
    # Check data integrity
    cur.execute("SELECT COUNT(*) FROM customers WHERE churn='Yes'")
    churned = cur.fetchone()[0]
    assert churned == 1869, f"Expected 1869 churned, got {churned}"
    
    cur.execute("SELECT AVG(monthly_charges) FROM customers")
    avg = cur.fetchone()[0]
    assert 64 < avg < 66, f"Average monthly charges out of range: {avg}"
    
    conn.close()
    print("✓ Database tests passed")

def test_vector_store():
    """Test FAISS vector store."""
    from src.data_loader import load_vector_store
    
    store = load_vector_store()
    
    # Test search works
    results = store.similarity_search("roaming", k=3)
    assert len(results) == 3, "Should return 3 results"
    assert any("roaming" in r.page_content.lower() for r in results), "Roaming not in results"
    
    # Test different queries
    results = store.similarity_search("billing payment", k=3)
    assert len(results) == 3, "Should return 3 results for billing"
    
    results = store.similarity_search("5G network speed", k=3)
    assert len(results) == 3, "Should return 3 results for 5G"
    
    print("✓ Vector store tests passed")

def test_tools_faq():
    """Test FAQ search tool."""
    from src.tools import search_faq
    
    # Test roaming query
    result = search_faq.invoke({"query": "activate international roaming"})
    assert "roaming" in result.lower(), "Roaming not in FAQ result"
    
    # Test billing query
    result = search_faq.invoke({"query": "pay my bill"})
    assert len(result) > 50, "FAQ result too short"
    
    # Test USSD query
    result = search_faq.invoke({"query": "USSD code balance"})
    assert "*" in result or "dial" in result.lower(), "USSD info not found"
    
    # Test plan query
    result = search_faq.invoke({"query": "prepaid plans available"})
    assert "plan" in result.lower() or "prepaid" in result.lower(), "Plan info not found"
    
    print("✓ FAQ tool tests passed")

def test_tools_sql():
    """Test SQL query tool."""
    from src.tools import query_customers
    
    # Test count query
    result = query_customers.invoke({"sql": "SELECT COUNT(*) as total FROM customers"})
    assert "7043" in result, f"Wrong count: {result}"
    
    # Test churn query
    result = query_customers.invoke({"sql": "SELECT COUNT(*) FROM customers WHERE churn='Yes'"})
    assert "1869" in result, f"Wrong churn count: {result}"
    
    # Test average query
    result = query_customers.invoke({"sql": "SELECT ROUND(AVG(monthly_charges),2) FROM customers"})
    assert "64" in result, f"Wrong average: {result}"
    
    # Test group by
    result = query_customers.invoke({"sql": "SELECT contract, COUNT(*) FROM customers GROUP BY contract"})
    assert "Month-to-month" in result, f"Contract not in result: {result}"
    
    # Test filter
    result = query_customers.invoke({"sql": "SELECT COUNT(*) FROM customers WHERE internet_service='Fiber optic'"})
    assert "3096" in result, f"Wrong fiber count: {result}"
    
    print("✓ SQL tool tests passed")

def test_tools_stats():
    """Test stats tool."""
    from src.tools import get_stats
    
    result = get_stats.invoke({})
    
    assert "7043" in result, "Customer count missing"
    assert "64" in result, "Average charge missing"
    assert "Month-to-month" in result or "contract" in result.lower(), "Contract info missing"
    assert "Fiber" in result or "DSL" in result, "Internet info missing"
    assert "churn" in result.lower() or "1869" in result, "Churn info missing"
    
    print("✓ Stats tool tests passed")

def test_sql_injection():
    """Test SQL injection protection."""
    from src.tools import query_customers
    
    attacks = [
        "DROP TABLE customers",
        "DELETE FROM customers",
        "UPDATE customers SET churn='Yes'",
        "INSERT INTO customers VALUES ('x','x',0,'x','x',0,'x','x','x','x','x','x','x','x','x','x','x','x',0,0,'x')",
        "; DROP TABLE customers; --",
        "SELECT * FROM customers; DROP TABLE customers",
        "1; DROP TABLE customers",
    ]
    
    for attack in attacks:
        result = query_customers.invoke({"sql": attack})
        assert "Only SELECT" in result or "Error" in result, f"Attack not blocked: {attack}"
    
    # Verify table still exists
    result = query_customers.invoke({"sql": "SELECT COUNT(*) FROM customers"})
    assert "7043" in result, "Table was damaged by attack"
    
    print("✓ SQL injection tests passed")

def test_agent_routing():
    """Test agent routes to correct tools."""
    from src.agent import invoke
    
    # Test FAQ routing
    result = invoke("How do I activate roaming?")
    assert len(result) > 50, "FAQ response too short"
    assert "roaming" in result.lower() or "international" in result.lower(), "Roaming not addressed"
    
    # Test SQL routing
    result = invoke("How many customers have churned?")
    assert "1869" in result or "churned" in result.lower(), f"Churn count wrong: {result[:200]}"
    
    # Test stats routing
    result = invoke("Give me a summary of the customer base")
    assert "customer" in result.lower(), "Summary missing customer info"
    
    print("✓ Agent routing tests passed")

def test_agent_memory():
    """Test agent maintains conversation context."""
    from src.agent import invoke
    
    # First message
    r1 = invoke("What is the average monthly charge?", thread_id="test_memory")
    assert "64" in r1 or "monthly" in r1.lower(), "First response wrong"
    
    # Follow-up should have context
    r2 = invoke("And what about for fiber optic users specifically?", thread_id="test_memory")
    assert len(r2) > 20, "Follow-up response too short"
    
    print("✓ Agent memory tests passed")

def test_edge_cases():
    """Test edge cases and error handling."""
    from src.tools import search_faq, query_customers
    from src.agent import invoke
    
    # Empty query
    result = search_faq.invoke({"query": ""})
    assert result, "Empty query should return something"
    
    # Very long query
    long_query = "roaming " * 100
    result = search_faq.invoke({"query": long_query})
    assert result, "Long query should work"
    
    # Invalid SQL syntax
    result = query_customers.invoke({"sql": "SELECT * FORM customers"})
    assert "Error" in result, "Invalid SQL syntax should error"
    
    # Non-existent table
    result = query_customers.invoke({"sql": "SELECT * FROM nonexistent"})
    assert "Error" in result, "Non-existent table should error"
    
    # Non-existent column
    result = query_customers.invoke({"sql": "SELECT fake_column FROM customers"})
    assert "Error" in result, "Non-existent column should error"
    
    # Special characters in query
    result = invoke("What's the price for 5G? (asking for a friend)")
    assert len(result) > 20, "Special chars query failed"
    
    print("✓ Edge case tests passed")

def test_agentcore_handler():
    """Test AgentCore runtime handler."""
    from src.agentcore_runtime import handler
    
    # Normal request
    result = handler({"prompt": "What plans are available?"}, {})
    assert "result" in result, "Missing result key"
    assert len(result["result"]) > 50, "Result too short"
    assert "error" not in result or not result["error"], "Unexpected error"
    
    # Empty prompt
    result = handler({"prompt": ""}, {})
    assert "error" in result, "Empty prompt should error"
    
    # Missing prompt
    result = handler({}, {})
    assert "error" in result, "Missing prompt should error"
    
    print("✓ AgentCore handler tests passed")

def run_all():
    """Run all tests."""
    print("\n" + "="*50)
    print("HYBRID TELECOM AGENT - TEST SUITE")
    print("="*50 + "\n")
    
    tests = [
        ("Config", test_config),
        ("Data Files", test_data_files),
        ("Database", test_database),
        ("Vector Store", test_vector_store),
        ("FAQ Tool", test_tools_faq),
        ("SQL Tool", test_tools_sql),
        ("Stats Tool", test_tools_stats),
        ("SQL Injection", test_sql_injection),
        ("Agent Routing", test_agent_routing),
        ("Agent Memory", test_agent_memory),
        ("Edge Cases", test_edge_cases),
        ("AgentCore Handler", test_agentcore_handler),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"✗ {name} FAILED: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*50 + "\n")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
