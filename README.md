# Code Review & Debug Squad (Assignment 2)

A multi-agent assistant that reviews a pasted Python snippet like a small engineering team: it finds bugs, checks style, rewrites the code, then writes unit tests and runs them in a sandbox to verify the fix.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Pick ONE LLM option
export ANTHROPIC_API_KEY=...                            # API model (default provider "anthropic")
# export LLM_PROVIDER=openai && export OPENAI_API_KEY=...
# export LLM_PROVIDER=ollama   # local model: `ollama pull llama3.1` first, no key needed

streamlit run app.py
```

You can also paste the key into the sidebar. The first launch downloads ChromaDB's small default embedding model (about 80 MB), so it needs internet once.

Run the tests (no LLM or network needed): `pytest -q`

## Architecture

```
            +-------------------------------+
 code  ---> | Router (LLM, few-shot)        |--> intent: debug | style | explain | test | full_review
 request    +---------------+---------------+       (keyword fallback if the LLM reply is unusable)
                            v
            +-------------------------------+      +-------------------------+
            | Static analysis tool (ast)    |      | ChromaDB knowledge base |
            +---------------+---------------+      | style / bugs / testing  |
                            v                      +------------+------------+
            +-------------------------------+                   ^
            | Retrieval planner (LLM)       |-- RETRIEVE? ------+  similarity search per agent
            +---------------+---------------+       or SKIP
                            v
   Bug-Finder (CoT) -> Style/Lint -> Fixer -> Critic (reflection) -> Test-Writer <-> Sandbox (ReAct loop)
                            v
                    Consolidated report (Streamlit tabs)
```

| Intent | Agents that run |
|---|---|
| `debug` | Bug-Finder, Fixer (+reflection), Test-Writer |
| `style` | Style/Lint |
| `explain` | Explainer |
| `test` | Test-Writer (on your original code) |
| `full_review` | everything |

## How each acceptance criterion is met

| # | Criterion | Where |
|---|---|---|
| 1 | LLM integration | `squad/llm.py`: Anthropic or OpenAI (API) or Ollama (local) |
| 2 | Interactive GUI | `app.py` (Streamlit): code box, request box, tabs for report, diff, tests, trace, prompts |
| 3 | Prompt engineering | `squad/prompts.py`: few-shot (Router, Bug-Finder), CoT (Bug-Finder `reasoning` field), zero-shot (Style, Explainer, Test-Writer), reflection (Fixer -> Critic), ReAct (Test-Writer <-> sandbox). Each template has an explicit system and user message and is displayed in the **Prompts** tab |
| 4 | LangChain core | `ChatPromptTemplate` plus LCEL chains such as `prompts.BUG_PROMPT \| llm \| JsonOutputParser()` in `squad/orchestrator.py` |
| 5 | Agentic RAG | `RETRIEVAL_PROMPT` makes the agent decide RETRIEVE or SKIP and write its own query; each agent then pulls category-filtered chunks (`_context`) |
| 6 | Intent detection & routing | `CodeReviewSquad.detect_intent` + the branching in `run()`; manual override in the sidebar |
| 7 | Vector database | `squad/knowledge.py`: ChromaDB persistent collection, cosine similarity search over `knowledge_base/*.md` |

Extra tool use: `squad/analysis.py` (AST static analysis feeds the agents as evidence) and `squad/sandbox.py` (isolated execution).

## Demo script (for the viva)

1. Start the app with the pre-filled sample (it has an off-by-one, a mutable default, a division by zero, a shadowed built-in and an unused import).
2. Request: `review my code` -> Router picks `full_review`. Open **Agent trace** to show the RAG decision and retrieved chunks.
3. Show the **Fixed code** diff, then **Tests**: the fixed code passes.
4. Request: `explain this` -> router picks `explain`; the Fixer and Test-Writer are not run.
5. Request: `write tests` on the *original* code -> tests fail, and the ReAct diagnosis says the failures are genuine code bugs.

## Extending the knowledge base

Add a markdown file to `knowledge_base/` named `style_*.md`, `bugs_*.md` or `testing_*.md`, use `## ` headings (one chunk per section) and click **Re-index knowledge base**.

## Limitations

- Python only.
- The sandbox uses a separate process with a timeout, resource limits and a stripped environment. That is fine for a coursework demo but not a hard security boundary; for real deployments run it in a container with networking disabled.
- Review quality depends on the LLM you choose; small local models may produce malformed JSON (the code falls back gracefully for the router and retrieval planner, but the review itself may then fail with an error message).
