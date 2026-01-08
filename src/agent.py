"""Local agent for CLI testing."""
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from src.config import get_settings
from src.tools import TOOLS

settings = get_settings()

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

_agent = None
_memory = None

def get_agent():
    global _agent, _memory
    if _agent is None:
        model = ChatGroq(
            model=settings.llm_model,
            api_key=settings.groq_api_key,
            temperature=0
        )
        _memory = MemorySaver()
        _agent = create_agent(
            model=model,
            tools=TOOLS,
            checkpointer=_memory,
            system_prompt=SYSTEM_PROMPT
        )
    return _agent

def invoke(query: str, thread_id: str = "default") -> str:
    config = {"configurable": {"thread_id": thread_id}}
    result = get_agent().invoke({"messages": [("human", query)]}, config=config)
    return result["messages"][-1].content
