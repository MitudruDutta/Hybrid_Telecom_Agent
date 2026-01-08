"""AgentCore Runtime with AWS Memory persistence."""
import os
import sys
import uuid
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(Path(__file__).parent.parent)

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, AgentState
from langgraph.store.base import BaseStore
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from langgraph_checkpoint_aws import AgentCoreMemorySaver, AgentCoreMemoryStore

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

# Memory Configuration
MEMORY_ID = "cc_memory-7VM1d2D7Kl"

# Initialize memory components
checkpointer = AgentCoreMemorySaver(memory_id=MEMORY_ID, region_name=settings.aws_region)
memory_store = AgentCoreMemoryStore(memory_id=MEMORY_ID, region_name=settings.aws_region)

SYSTEM_PROMPT = """You are a telecom customer service agent with hybrid retrieval and conversation memory.

TOOLS:
- search_faq: Policy, process, how-to, troubleshooting questions
- query_customers: SQL queries for statistics, pricing, counts (table: customers)
- get_stats: Quick overview of customer base

Remember conversation context. Be concise and accurate."""


class MemoryMiddleware(AgentMiddleware):
    def pre_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
        actor_id = config["configurable"].get("actor_id", "default")
        thread_id = config["configurable"].get("thread_id", "default")
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])
        
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg.content, "type": "human"})
                break
        return {"messages": messages}
    
    def post_model_hook(self, state: AgentState, config: RunnableConfig, *, store: BaseStore) -> dict:
        actor_id = config["configurable"].get("actor_id", "default")
        thread_id = config["configurable"].get("thread_id", "default")
        namespace = (actor_id, thread_id)
        messages = state.get("messages", [])
        
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                store.put(namespace, str(uuid.uuid4()), {"message": msg.content, "type": "ai"})
                break
        return state


llm = init_chat_model(
    model=settings.llm_model,
    model_provider="groq",
    api_key=settings.groq_api_key
)

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
    query = payload.get("prompt", "")
    if not query:
        return {"error": "No prompt provided", "result": ""}
    
    actor_id = payload.get("actor_id", context.get("actor_id", "default-user"))
    thread_id = payload.get("thread_id", payload.get("session_id", context.get("session_id", "default")))
    
    config = {"configurable": {"thread_id": thread_id, "actor_id": actor_id}}
    
    try:
        result = agent.invoke({"messages": [("human", query)]}, config=config)
        return {
            "result": result["messages"][-1].content,
            "actor_id": actor_id,
            "thread_id": thread_id
        }
    except Exception as e:
        return {"error": str(e), "result": ""}


if __name__ == "__main__":
    app.run()
