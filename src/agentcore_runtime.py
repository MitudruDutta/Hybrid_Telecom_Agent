"""AgentCore Runtime - Basic deployment."""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from dotenv import load_dotenv
load_dotenv()

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from src.tools import TOOLS
from src.config import get_settings
from src.data_loader import init_sqlite_db, build_vector_store, DB_PATH, DATA_DIR

app = BedrockAgentCoreApp()
settings = get_settings()

# Initialize data on startup
if not DB_PATH.exists():
    init_sqlite_db()
if not (DATA_DIR / "faiss_index").exists():
    build_vector_store()

SYSTEM_PROMPT = """You are a telecom customer service agent with hybrid retrieval.

TOOLS:
- search_faq: Policy, process, how-to, troubleshooting questions
- query_customers: SQL queries for statistics, pricing, counts (table: customers)
- get_stats: Quick overview of customer base

ROUTING:
- "How do I..." / "What is..." / "Can I..." → search_faq
- "How many..." / "Average..." / "Count..." / numbers → query_customers
- "Overview" / "Summary" → get_stats

SQL TABLE: customers
COLUMNS: customer_id, gender, senior_citizen(0/1), partner, dependents, tenure,
phone_service, multiple_lines, internet_service(DSL/Fiber optic/No),
online_security, online_backup, device_protection, tech_support,
streaming_tv, streaming_movies, contract(Month-to-month/One year/Two year),
paperless_billing, payment_method, monthly_charges, total_charges, churn(Yes/No)

Be concise and accurate."""

model = ChatGroq(
    model=settings.llm_model,
    temperature=0,
    api_key=settings.groq_api_key
)

agent = create_agent(
    model=model,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT
)

@app.entrypoint
def handler(payload: dict, context: dict) -> dict:
    query = payload.get("prompt", "")
    if not query:
        return {"error": "No prompt provided", "result": ""}
    
    try:
        result = agent.invoke({"messages": [("human", query)]})
        return {"result": result["messages"][-1].content}
    except Exception as e:
        return {"error": str(e), "result": ""}

if __name__ == "__main__":
    app.run()
