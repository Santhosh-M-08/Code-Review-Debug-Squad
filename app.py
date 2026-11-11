"""Streamlit front end for the Code Review & Debug Squad.
Run: py -m streamlit run app.py
"""

import difflib
import os

import streamlit as st

from squad import config
from squad.intent import INTENTS
from squad.knowledge import KnowledgeBase
from squad.llm import get_llm
from squad.orchestrator import CodeReviewSquad
from squad.prompts import ALL_PROMPTS
from squad.report import render_report


st.set_page_config(
    page_title="Code Review & Debug Squad",
    page_icon="🛠️",
    layout="wide"
)


SAMPLE_CODE = '''import os


def average(numbers):
    total = 0
    for n in numbers:
        total += n
    return total / len(numbers)


def add_item(item, items=[]):
    items.append(item)
    return items


def find_max(values):
    max = values[0]
    for i in range(1, len(values) - 1):
        if values[i] > max:
            max = values[i]
    return max
'''


# Default models for each provider
FALLBACK_MODELS = {
    "google": "gemini-3.8-flash",
    "anthropic": "claude-3-5-sonnet-latest",
    "openai": "gpt-4o-mini",
    "ollama": "llama3.2"
}


@st.cache_resource(
    show_spinner="Loading knowledge base (first run downloads the embedding model)..."
)
def load_kb() -> KnowledgeBase:
    return KnowledgeBase()


@st.cache_resource(show_spinner=False)
def load_squad(
    provider: str,
    model: str,
    key_fingerprint: str
) -> CodeReviewSquad:
    return CodeReviewSquad(
        get_llm(provider, model or None),
        load_kb()
    )


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

with st.sidebar:

    st.header("Settings")

    # Available providers
    provider_options = [
        "google",
        "anthropic",
        "openai",
        "ollama"
    ]

    # Safely select the configured provider
    configured_provider = getattr(config, "LLM_PROVIDER", "google")

    provider_index = (
        provider_options.index(configured_provider)
        if configured_provider in provider_options
        else 0
    )

    provider = st.selectbox(
        "LLM provider",
        provider_options,
        index=provider_index
    )

    # Safely retrieve the default model
    configured_models = getattr(config, "DEFAULT_MODELS", {})

    default_model = (
        configured_models.get(provider)
        or FALLBACK_MODELS[provider]
    )

    configured_model = getattr(config, "LLM_MODEL", "")

    model = st.text_input(
        "Model",
        value=configured_model or default_model
    )

    # API key configuration
    key_var = {
        "google": "GOOGLE_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY"
    }.get(provider)

    api_key = ""

    if key_var:
        api_key = st.text_input(
            key_var,
            type="password",
            value="",
            help="Leave empty if it is already set in your environment."
        )

        if api_key:
            os.environ[key_var] = api_key.strip()

    # Intent selection
    intent_choice = st.selectbox(
        "Intent",
        ["auto (let the router decide)"] + list(INTENTS)
    )

    st.divider()

    # Knowledge base
    try:
        kb = load_kb()

        st.caption(
            f"Vector DB: ChromaDB, {kb.count()} guideline chunks"
        )

        if st.button("Re-index knowledge base"):
            n = kb.ingest()
            st.success(f"Indexed {n} chunks")

    except Exception as exc:
        st.error(f"Knowledge base unavailable: {exc}")


# ------------------------------------------------------------------
# Main application
# ------------------------------------------------------------------

st.title("🛠️ Code Review & Debug Squad")

st.caption(
    "Bug-Finder, Style/Lint, Fixer and Test-Writer agents "
    "review your Python code like a small engineering team."
)

request = st.text_input(
    "What do you need?",
    placeholder=(
        "e.g. review my code / why does it crash on empty input? "
        "/ write tests / explain this"
    )
)

code = st.text_area(
    "Python code",
    value=SAMPLE_CODE,
    height=340
)

run_clicked = st.button(
    "Run review",
    type="primary",
    disabled=not code.strip()
)


# ------------------------------------------------------------------
# Run code review
# ------------------------------------------------------------------

if run_clicked:

    try:

        squad = load_squad(
            provider,
            model,
            str(hash(api_key))
        )

        override = (
            None
            if intent_choice.startswith("auto")
            else intent_choice
        )

        with st.status(
            "Squad at work...",
            expanded=True
        ) as status:

            st.write("🚀 Starting code review...")

            result = squad.run(
                code,
                request,
                intent_override=override,
                progress=lambda message: st.write(f"🔄 {message}")
            )

            st.success("✅ Review completed!")

            status.update(
                label="Review complete",
                state="complete"
            )

        st.session_state["result"] = result

    except Exception as exc:
        st.error(f"Review failed: {exc}")


# ------------------------------------------------------------------
# Display results
# ------------------------------------------------------------------

result = st.session_state.get("result")

if result:

    tabs = st.tabs([
        "📋 Report",
        "🔧 Fixed code",
        "🧪 Tests",
        "🔎 Agent trace",
        "📝 Prompts"
    ])

    # Report tab
    with tabs[0]:

        st.markdown(
            render_report(result),
            unsafe_allow_html=True
        )

        if result.static_findings:

            with st.expander("Static-analysis tool findings"):

                for f in result.static_findings:

                    st.write(
                        f"- `{f.category}` line {f.line}: "
                        f"**{f.kind}** - {f.message}"
                    )

    # Fixed code tab
    with tabs[1]:

        if result.fixed_code is None:

            st.info(
                "The Fixer did not run for this intent. "
                "Choose 'debug' or 'full_review'."
            )

        else:

            st.subheader(
                f"Fixed code (reflection verdict: {result.fix_verdict})"
            )

            st.code(
                result.fixed_code,
                language="python"
            )

            st.download_button(
                "Download fixed_code.py",
                result.fixed_code,
                file_name="fixed_code.py"
            )

            diff = "\n".join(
                difflib.unified_diff(
                    result.original_code.splitlines(),
                    result.fixed_code.splitlines(),
                    "original.py",
                    "fixed.py",
                    lineterm=""
                )
            )

            st.subheader("Diff")

            st.code(
                diff or "(no changes)",
                language="diff"
            )

    # Tests tab
    with tabs[2]:

        if result.test_run is None:

            st.info(
                "The Test-Writer did not run for this intent."
            )

        else:

            t = result.test_run

            (st.success if t["ok"] else st.error)(
                f"{'All tests passed' if t['ok'] else 'Tests failed'}: "
                f"{t['tests_run']} run, "
                f"{t['failures']} failures, "
                f"{t['errors']} errors"
            )

            st.subheader("Generated tests")

            st.code(
                result.tests_code,
                language="python"
            )

            for entry in result.test_log:

                with st.expander(
                    f"Sandbox attempt {entry['attempt']}: "
                    f"{'PASS' if entry['run']['ok'] else 'FAIL'}"
                ):

                    st.code(
                        (
                            entry["run"]["stderr"]
                            + entry["run"]["stdout"]
                        ).strip() or "(no output)"
                    )

                    if entry["diagnosis"]:

                        st.write(
                            f"**ReAct diagnosis:** "
                            f"{entry['diagnosis']}. "
                            f"{entry['thought']}"
                        )

    # Agent trace tab
    with tabs[3]:

        st.subheader("Agent trace")

        for step in result.trace:
            st.write(f"- {step}")

        st.subheader("Agentic RAG")

        st.json(result.retrieval)

        for hit in result.retrieved:

            with st.expander(
                f"{hit['source']} > {hit['section']} "
                f"(distance {hit['distance']})"
            ):

                st.text(hit["text"])

    # Prompts tab
    with tabs[4]:

        st.caption(
            "The system and user (human) prompt templates "
            "used by each agent."
        )

        for name, prompt in ALL_PROMPTS.items():

            with st.expander(name):

                for message in prompt.messages:

                    role = (
                        "SYSTEM"
                        if "System" in type(message).__name__
                        else "USER"
                    )

                    st.markdown(f"**{role} prompt**")

                    st.code(
                        message.prompt.template,
                        language="text"
                    )