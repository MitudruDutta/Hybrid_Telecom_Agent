<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LangGraph-1.0+-green?style=for-the-badge" alt="LangGraph">
  <img src="https://img.shields.io/badge/AWS-Bedrock%20AgentCore-orange?style=for-the-badge&logo=amazon-aws&logoColor=white" alt="AWS">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

<h1 align="center">🔀 Hybrid Telecom Agent</h1>

<p align="center">
  <strong>Production-ready AI agent combining semantic search and SQL analytics for telecom customer service</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="#-api-reference">API</a>
</p>

---

## 🎯 Overview

A hybrid retrieval agent that intelligently routes customer queries to either:
- **Vector Search** (FAISS) for policy/process questions
- **SQL Queries** (SQLite) for analytics and statistics

Built for AWS Bedrock AgentCore with conversation memory support.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Hybrid Retrieval** | Automatic routing between FAQ search and SQL queries |
| 📚 **227 FAQ Entries** | Comprehensive knowledge base: plans, billing, roaming, USSD codes |
| 👥 **7,043 Customers** | Real structured data for analytics |
| 🧠 **Conversation Memory** | Long-term memory via AWS AgentCore Memory Service |
| 🛡️ **SQL Injection Protection** | SELECT-only queries with validation |
| ✅ **12 Test Categories** | Comprehensive test coverage |

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/MitudruDutta/Hybrid_Telecom_Agent.git
cd Hybrid_Telecom_Agent

# Setup environment
cp .env.example .env
# Add your GROQ_API_KEY to .env

# Install dependencies
pip install -r requirements.txt

# Initialize data stores
python main.py init

# Run tests
python tests/test_agent.py

# Start CLI
python main.py cli
```

## 🏗️ Architecture

```
                              ┌─────────────────┐
                              │   User Query    │
                              └────────┬────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────┐
                    │    LLM (openai/gpt-oss-120b)     │
                    │         Intent Detection         │
                    └──────────────────┬───────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │   search_faq    │     │ query_customers │     │    get_stats    │
    │     (FAISS)     │     │    (SQLite)     │     │    (SQLite)     │
    └─────────────────┘     └─────────────────┘     └─────────────────┘
              │                        │                        │
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │  227 FAQ Docs   │     │ 7,043 Customers │     │   Aggregated    │
    │  Vector Index   │     │   SQL Database  │     │   Statistics    │
    └─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 📁 Project Structure

```
Hybrid_Telecom_Agent/
│
├── 📄 main.py                     # CLI entrypoint
├── 📄 requirements.txt            # Dependencies
├── 📄 .env.example                # Environment template
│
├── 📂 src/
│   ├── config.py                  # Pydantic settings
│   ├── data_loader.py             # SQLite + FAISS initialization
│   ├── tools.py                   # Agent tools
│   ├── agent.py                   # Local agent (CLI)
│   ├── agentcore_runtime.py       # AWS deployment (basic)
│   └── agentcore_memory.py        # AWS deployment (with memory)
│
├── 📂 data/
│   ├── customers.csv              # Customer records
│   ├── qna.csv                    # FAQ knowledge base
│   ├── telecom.db                 # SQLite (generated)
│   └── faiss_index/               # Vector index (generated)
│
└── 📂 tests/
    └── test_agent.py              # Test suite
```

## 🛠️ Tools Reference

### `search_faq`
Semantic search over FAQ knowledge base.

```python
# Use for: Policy, process, how-to questions
"How do I activate international roaming?"
"What is the billing cycle?"
"USSD code for balance check"
```

### `query_customers`
SQL queries on structured customer data.

```python
# Use for: Statistics, counts, analytics
"How many customers have churned?"
"Average monthly charge for fiber users?"
"Count of two-year contracts"
```

### `get_stats`
Quick overview of customer base.

```python
# Use for: Summary requests
"Give me an overview of customers"
"Customer base summary"
```

## 📊 Database Schema

<details>
<summary><strong>customers</strong> table (click to expand)</summary>

| Column | Type | Example Values |
|--------|------|----------------|
| `customer_id` | TEXT | 7590-VHVEG |
| `gender` | TEXT | Male, Female |
| `senior_citizen` | INT | 0, 1 |
| `partner` | TEXT | Yes, No |
| `dependents` | TEXT | Yes, No |
| `tenure` | INT | 0-72 (months) |
| `phone_service` | TEXT | Yes, No |
| `multiple_lines` | TEXT | Yes, No |
| `internet_service` | TEXT | DSL, Fiber optic, No |
| `online_security` | TEXT | Yes, No |
| `online_backup` | TEXT | Yes, No |
| `device_protection` | TEXT | Yes, No |
| `tech_support` | TEXT | Yes, No |
| `streaming_tv` | TEXT | Yes, No |
| `streaming_movies` | TEXT | Yes, No |
| `contract` | TEXT | Month-to-month, One year, Two year |
| `paperless_billing` | TEXT | Yes, No |
| `payment_method` | TEXT | Electronic check, Mailed check, etc. |
| `monthly_charges` | REAL | 18.25 - 118.75 |
| `total_charges` | REAL | 0 - 8684.8 |
| `churn` | TEXT | Yes, No |

</details>

## ☁️ AWS Deployment

### Prerequisites

- AWS CLI configured
- Bedrock AgentCore access enabled
- Python 3.12+

### Option 1: Basic Runtime

```bash
# Configure
agentcore configure -c \
  -e src/agentcore_runtime.py \
  -n telecom_agent \
  -rf requirements.txt \
  -r ap-south-1

# Test locally
agentcore dev --port 8080

# Deploy
agentcore deploy

# Invoke
agentcore invoke --prompt "How do I check my balance?"
```

### Option 2: With Memory Persistence

```bash
# Configure with memory-enabled runtime
agentcore configure -c \
  -e src/agentcore_memory.py \
  -n telecom_agent_memory \
  -rf requirements.txt \
  -r ap-south-1

# Deploy
agentcore deploy
```

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `GROQ_API_KEY` | ✅ | - | Groq API key |
| `HF_TOKEN` | ❌ | - | HuggingFace token |
| `AWS_REGION` | ❌ | ap-south-1 | AWS region |

## 🧪 Testing

```bash
# Run full test suite (12 categories)
python tests/test_agent.py
```

**Test Categories:**
- ✅ Config validation
- ✅ Data file integrity  
- ✅ Database operations
- ✅ Vector store search
- ✅ FAQ tool
- ✅ SQL tool
- ✅ Stats tool
- ✅ SQL injection protection
- ✅ Agent routing
- ✅ Agent memory
- ✅ Edge cases
- ✅ AgentCore handler

## 🔒 Security

- **SQL Injection Protection**: Only SELECT queries allowed
- **Input Validation**: All endpoints validated
- **Error Handling**: Graceful fallbacks, no stack traces exposed
- **No PII Exposure**: Customer IDs anonymized in responses

## 📈 Performance

| Metric | Value |
|--------|-------|
| FAQ Search Latency | ~200ms |
| SQL Query Latency | ~50ms |
| Vector Index Size | ~500KB |
| Database Size | ~1MB |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ using <a href="https://github.com/langchain-ai/langgraph">LangGraph</a> and <a href="https://aws.amazon.com/bedrock/">AWS Bedrock</a>
</p>
