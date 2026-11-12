# 🛠️ Code Review & Debug Squad

An intelligent multi-agent Python code review assistant that works like a small software engineering team. It analyzes submitted code, identifies bugs, checks coding standards, generates corrected code, and creates and executes unit tests to verify the improvements.

Built with **Python, Streamlit, LangChain, Ollama, and ChromaDB**, the application uses multiple specialized AI agents to provide a complete code review workflow using locally hosted language models.

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Code-Review-Debug-Squad
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```powershell
# Windows
.venv\Scripts\activate
```

```bash
# Linux / macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and configure Ollama

Download and install Ollama from [https://ollama.com](https://ollama.com).

Pull one of the supported local models:

```bash
ollama pull qwen2.5-coder:3b
ollama pull llama3.2:3b
ollama pull gemma3:1b
```

Make sure Ollama is running before starting the application.

### 5. Launch the application

```bash
python -m streamlit run app.py
```

The application opens in your browser. Select a local model, enter your Python code, describe what you need, and click **Run Review**.

**No cloud API keys are required.** All LLM inference is performed locally through Ollama.

### 6. Run the tests

```bash
pytest -q
```

Tests can be run independently of the LLM if they do not require model access.

---

## Architecture

The project follows a multi-agent architecture in which specialized agents collaborate to analyze and improve Python code.

```text
                  Python Code + User Request
                            |
                            v
                  +---------------------+
                  |   Intent Detection  |
                  |  Debug / Style /    |
                  | Explain / Test /    |
                  |    Full Review     |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |   Static Analysis   |
                  |    Python AST       |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |  Retrieval Planner  |
                  |    RETRIEVE / SKIP  |
                  +----------+----------+
                             |
                     +-------+-------+
                     |               |
                  RETRIEVE          SKIP
                     |               |
                     v               |
              +--------------+       |
              |   ChromaDB   |       |
              | Coding Docs  |       |
              +------+-------+       |
                     |               |
                     +-------+-------+
                             |
                             v
                  +---------------------+
                  |     Bug-Finder      |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |     Style / Lint    |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |       Fixer         |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |  Critic / Reflection|
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |    Test-Writer      |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |  Sandbox Execution  |
                  |   ReAct Repair Loop |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  | Consolidated Report |
                  |   Streamlit GUI     |
                  +---------------------+
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application and backend logic |
| Streamlit | Interactive frontend |
| Ollama | Runs local language models |
| Qwen 2.5 Coder / Llama 3.2 / Gemma 3 | Local LLM options |
| LangChain | Agent orchestration and prompt management |
| LCEL | Connects prompts, models, and output parsers |
| ChromaDB | Vector database for coding knowledge |
| Python AST | Static code analysis |
| Pytest | Unit testing |
| Isolated Sandbox | Executes generated tests with safety limits |

## AI Agents and Responsibilities

| Agent | Responsibility |
|---|---|
| Bug-Finder | Identifies logical errors, runtime issues, and edge cases |
| Style/Lint | Checks naming conventions, readability, and coding practices |
| Fixer | Generates corrected and improved Python code |
| Critic / Reflection | Evaluates the Fixer's proposed solution |
| Test-Writer | Generates unit tests and verifies the implementation |
| Explainer | Explains code functionality and logic |
| Intent Router | Determines the user's request and selects the appropriate workflow |
| Retrieval Planner | Decides whether external coding knowledge should be retrieved from the knowledge base |

## Intent Detection and Agent Routing

The application supports five types of user intent:

| Intent | Agents Executed |
|---|---|
| `debug` | Bug-Finder, Fixer, Critic, Test-Writer |
| `style` | Style/Lint |
| `explain` | Explainer |
| `test` | Test-Writer |
| `full_review` | All applicable agents |

Users can either allow automatic intent detection or manually select an intent from the sidebar.

## Key Features

### 1. Multi-Agent Code Review
Multiple specialized agents analyze different aspects of the submitted code and contribute to a consolidated review.

### 2. Local LLM Integration
Uses Ollama to run language models locally without depending on external LLM APIs.

Supported models:

- **Qwen 2.5 Coder 3B** – Specialized for programming and code-related tasks.
- **Llama 3.2 3B** – General-purpose language model.
- **Gemma 3 1B** – Lightweight model option.

### 3. Agentic RAG
Uses a Retrieval-Augmented Generation approach with ChromaDB.

The Retrieval Planner decides whether coding guidelines, debugging examples, or testing documentation are needed. Relevant knowledge is retrieved through similarity search and passed to the appropriate agents.

### 4. Code Correction and Reflection
The Fixer generates improved code, while the Critic evaluates the proposed changes to improve reliability.

### 5. Automated Test Generation
The Test-Writer generates unit tests to validate the submitted or corrected implementation.

### 6. ReAct-Based Sandbox Testing
Generated tests are executed in an isolated process with execution timeouts and resource restrictions. Failed test runs can trigger diagnosis and repair attempts.

### 7. Interactive Streamlit Interface
The frontend provides:

- Python code editor/input area.
- User request and intent selection.
- Local model selection.
- Consolidated review report.
- Corrected code with downloadable output.
- Original-versus-fixed code diff.
- Generated tests and execution logs.
- Agent execution trace and RAG information.
- Agent prompt templates.

## How the Acceptance Criteria Are Met

| # | Acceptance Criterion | Implementation |
|---|---|---|
| 1 | LLM Integration | `squad/llm.py` – Ollama integration |
| 2 | Interactive GUI | `app.py` – Streamlit frontend |
| 3 | Prompt Engineering | `squad/prompts.py` – Few-shot, CoT, zero-shot, reflection, and ReAct prompting |
| 4 | LangChain Core | `ChatPromptTemplate`, LCEL chains, and output parsers |
| 5 | Agentic RAG | Retrieval Planner, ChromaDB, and category-filtered retrieval |
| 6 | Intent Detection and Routing | `squad/intent.py` and `squad/orchestrator.py` |
| 7 | Vector Database | `squad/knowledge.py` – Persistent ChromaDB collection |

## Demo Workflow

1. Launch the application and load the pre-filled sample Python code.
2. Enter `review my code` and select automatic intent detection.
3. Run the review and demonstrate how the agents identify bugs and style issues.
4. Open **Agent Trace** to demonstrate intent routing and the RAG retrieval decision.
5. Open **Fixed Code** to show the corrected implementation and code differences.
6. Open **Tests** to demonstrate generated test cases and sandbox execution.
7. Enter `explain this` to demonstrate the Explainer agent.
8. Enter `write tests` to demonstrate automated test generation and execution.

## Extending the Knowledge Base

The knowledge base can be expanded by adding Markdown files inside the `knowledge_base/` directory.

Use the following naming conventions:

- `bugs_*.md` – Debugging guidelines and common programming errors.
- `style_*.md` – Python coding standards and style guidelines.
- `testing_*.md` – Unit testing techniques and testing practices.

Organize content using Markdown headings (`##`). Each section is treated as a separate knowledge chunk.

After adding new documents, click **Re-index knowledge base** in the application sidebar to update ChromaDB.

## Project Limitations

- Currently supports Python code review and testing.
- Review quality depends on the selected local language model.
- Smaller models may occasionally generate malformed structured responses or inaccurate suggestions.
- First-time ChromaDB initialization may download an embedding model, requiring an internet connection.
- The sandbox provides process isolation, timeouts, and resource restrictions but is not a complete security boundary. Production deployments should use stronger isolation, such as network-disabled containers.

---

**Code Review & Debug Squad** demonstrates how multi-agent systems, prompt engineering, local language models, Agentic RAG, and automated testing can work together to build an intelligent software development assistant.