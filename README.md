# Hybrid Telecom Agent

Production-ready telecom customer service agent with hybrid retrieval combining semantic FAQ search and SQL queries on structured customer data. Deployable to AWS Bedrock AgentCore.

## Features

- **Hybrid Retrieval**: Routes queries to FAQ vector search or SQL based on intent
- **227 FAQ Entries**: Comprehensive knowledge base covering plans, billing, roaming, support, USSD codes
- **7,043 Customer Records**: Real structured data for analytics and statistics
- **Smart Tool Selection**: LLM automatically chooses appropriate retrieval method
- **AWS Bedrock AgentCore**: Production deployment with memory persistence
- **Conversation Memory**: Long-term memory via AgentCore Memory Service

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────┐
│  LLM (openai/gpt-oss-120b)  │
│      Intent Detection       │
└─────────────┬───────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│  FAQ   │ │  SQL   │ │ Stats  │
│ FAISS  │ │ SQLite │ │ SQLite │
└────────┘ └────────┘ └────────┘
```

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/MitudruDutta/Hybrid_Telecom_Agent.git
cd Hybrid_Telecom_Agent
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize data stores
python main.py init

# 4. Run tests
python tests/test_agent.py

# 5. Interactive CLI
python main.py cli

# 6. Run AgentCore server locally
python main.py serve
```

## Project Structure

```
agentcore/
├── main.py                    # CLI entrypoint (init/cli/serve)
├── src/
│   ├── config.py              # Pydantic settings
│   ├── data_loader.py         # SQLite + FAISS initialization
│   ├── tools.py               # search_faq, query_customers, get_stats
│   ├── agent.py               # Local agent for CLI
│   ├── agentcore_runtime.py   # AWS Bedrock runtime (basic)
│   └── agentcore_memory.py    # AWS Bedrock runtime (with memory)
├── data/
│   ├── customers.csv          # 7,043 customer records
│   ├── qna.csv                # 227 FAQ entries
│   ├── telecom.db             # SQLite (generated)
│   └── faiss_index/           # Vector index (generated)
├── tests/
│   └── test_agent.py          # Comprehensive test suite (12 tests)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
└── README.md
```

## Tools

| Tool | Use Case | Example |
|------|----------|---------|
| `search_faq` | Policy, process, how-to | "How do I activate roaming?" |
| `query_customers` | SQL analytics | "Average charge for fiber users?" |
| `get_stats` | Quick overview | "Customer base summary" |

## Data Schema

### customers table
| Column | Type | Values |
|--------|------|--------|
| customer_id | TEXT | Unique ID |
| gender | TEXT | Male/Female |
| senior_citizen | INT | 0/1 |
| partner | TEXT | Yes/No |
| dependents | TEXT | Yes/No |
| tenure | INT | Months (0-72) |
| phone_service | TEXT | Yes/No |
| multiple_lines | TEXT | Yes/No |
| internet_service | TEXT | DSL/Fiber optic/No |
| online_security | TEXT | Yes/No |
| online_backup | TEXT | Yes/No |
| device_protection | TEXT | Yes/No |
| tech_support | TEXT | Yes/No |
| streaming_tv | TEXT | Yes/No |
| streaming_movies | TEXT | Yes/No |
| contract | TEXT | Month-to-month/One year/Two year |
| paperless_billing | TEXT | Yes/No |
| payment_method | TEXT | Electronic check/Mailed check/Bank transfer/Credit card |
| monthly_charges | REAL | 18.25-118.75 |
| total_charges | REAL | 0-8684.8 |
| churn | TEXT | Yes/No |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| GROQ_API_KEY | Yes | Groq API key for LLM |
| HF_TOKEN | No | HuggingFace token (optional) |
| AWS_REGION | No | Default: ap-south-1 |

## AWS Deployment

### Prerequisites
- AWS CLI configured
- Bedrock AgentCore access enabled
- Python 3.12+

### Step 1: Configure AgentCore
```bash
agentcore configure -c \
  -e src/agentcore_runtime.py \
  -n telecom_agent \
  -rf requirements.txt \
  -r ap-south-1
```

### Step 2: Test Locally
```bash
agentcore dev --port 8080
```

### Step 3: Deploy
```bash
agentcore deploy
```

### Step 4: Invoke
```bash
agentcore invoke --prompt "How do I check my balance?"
```

### With Memory (for conversation persistence)
Use `src/agentcore_memory.py` as entrypoint:
```bash
agentcore configure -c \
  -e src/agentcore_memory.py \
  -n telecom_agent_memory \
  -rf requirements.txt \
  -r ap-south-1
```

## Testing

```bash
# Run all 12 test categories
python tests/test_agent.py

# Test categories:
# - Config validation
# - Data file integrity
# - Database operations
# - Vector store search
# - FAQ tool
# - SQL tool
# - Stats tool
# - SQL injection protection
# - Agent routing
# - Agent memory
# - Edge cases
# - AgentCore handler
```

## Safety Features

- SQL injection blocked (SELECT only)
- Input validation on all endpoints
- Error handling with graceful fallbacks
- No PII exposure in responses

## License

MIT
