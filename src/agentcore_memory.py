"""AgentCore Runtime with AWS Memory persistence."""
import os
import uuid
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.store.base import BaseStore
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore
from dotenv import load_dotenv

# Ensure we're in the right directory
os.chdir(Path(__file__).parent.parent)
load_dotenv()

from src.tools import TOOLS
from src.config import get_settings

app = BedrockAgentCoreApp()
settings = get_settings()

# Memory Configuration
MEMORY_ID = "cc_memory-XioOkX8XXH"
REGION = settings.aws_region

# Initialize memory components
checkpointer = AgentCoreMemorySaver(memory_id=MEMORY_ID, region_name=REGION)
memory_store = AgentCoreMemoryStore(memory_id=MEMORY_ID, region_name=REGION)

SYSTEM_PROMPT = """You are a telecom customer service agent with hybrid retrieval and conversation memory.

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

Remember conversation context and user preferences. Be concise and accurate."""


class MemoryMiddleware(AgentMiddleware):
    """Middleware for saving and retrieving conversation memory."""
    
    def pre_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
        """Save human messages and retrieve relevant memories before LLM call."""
        actor_id = config["configurable"].get("actor_id", "default")
        thread_id = config["configurable"].get("thread_id", "default")
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])
        
        # Save latest human message
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg.content, "type": "human"})
                
                # Try to retrieve relevant past context
                try:
                    memories = store.search(("preferences", actor_id), query=msg.content, limit=3)
                    if memories:
                        print(f"Retrieved {len(memories)} relevant memories")
                except Exception as e:
                    print(f"Memory retrieval: {e}")
                break
        
        return {"messages": messages}
    
    def post_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
        """Save AI responses after LLM call."""
        actor_id = config["configurable"].get("actor_id", "default")
        thread_id = config["configurable"].get("thread_id", "default")
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])
        
        # Save latest AI message
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg.content, "type": "ai"})
                break
        
        return state


# Initialize LLM
llm = init_chat_model(
    model=settings.llm_model,
    model_provider="groq",
    api_key=settings.groq_api_key
)

# Create agent with memory
agent = create_agent(
    model=llm,
    tools=TOOLS,
    checkpointer=checkpointer,
    store=memory_store,
    middleware=[MemoryMiddleware()],
    system_prompt=SYSTEM_PROMPT
)


@app.entrypoint
def handler(payload: dict, context: dict) -> dict:
    """Handler for agent invocation with memory support."""
    query = payload.get("prompt", "")
    if not query:
        return {"error": "No prompt provided", "result": ""}
    
    # Extract identifiers
    actor_id = payload.get("actor_id", context.get("actor_id", "default-user"))
    thread_id = payload.get("thread_id", payload.get("session_id", context.get("session_id", "default")))
    
    config = {
        "configurable": {
            "thread_id": thread_id,
            "actor_id": actor_id
        }
    }
    
    try:
        result = agent.invoke({"messages": [("human", query)]}, config=config)
        messages = result.get("messages", [])
        answer = messages[-1].content if messages else "No response"
        
        return {
            "result": answer,
            "actor_id": actor_id,
            "thread_id": thread_id,
            "memory_id": MEMORY_ID
        }
    except Exception as e:
        return {"error": str(e), "result": ""}


if __name__ == "__main__":
    app.run()
