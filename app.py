from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.llm_client import LLMClient
from src.main import analyze_case
from src.prompt_loader import load_config, load_prompts
from src.report import weakness_report
from src.storage import Store

load_dotenv()
st.set_page_config(page_title="DebugCoach", page_icon="🐞", layout="wide")

CUSTOM = "(write my own)"


@st.cache_resource
def get_resources():
    cfg = load_config()
    return cfg, load_prompts(), LLMClient(cfg["llm"])


try:
    cfg, prompts, llm = get_resources()
except RuntimeError as err:
    st.error(str(err))
    st.stop()

SAMPLES = {}
for p in sorted(Path("data/sample_cases").glob("*_problem.txt")):
    stem = p.name.replace("_problem.txt", "")
    code_file = p.with_name(f"{stem}_wrong.cpp")
    if code_file.exists():
        SAMPLES[stem.replace("_", " ").title()] = (p, code_file)

st.session_state.setdefault("problem", "")
st.session_state.setdefault("code", "")
st.session_state.setdefault("result", None)
st.session_state.setdefault("level", 0)


def load_sample():
    choice = st.session_state.sample
    if choice != CUSTOM:
        p, c = SAMPLES[choice]
        st.session_state.problem = p.read_text(encoding="utf-8")
        st.session_state.code = c.read_text(encoding="utf-8")
    st.session_state.result = None
    st.session_state.level = 0


def reveal_next():
    st.session_state.level = min(3, st.session_state.level + 1)


st.title("🐞 DebugCoach")
st.caption("An LLM tutor that teaches you to find your own bug, one hint at a time.")

tab_debug, tab_report = st.tabs(["Debug my solution", "My bug patterns"])

with tab_debug:
    st.selectbox(
        "Load a sample case", [CUSTOM, *SAMPLES], key="sample", on_change=load_sample
    )
    left, right = st.columns(2)
    left.text_area("Problem statement", key="problem", height=220)
    right.text_area("Your C++ solution", key="code", height=220)

    if st.button("Analyze", type="primary"):
        if not st.session_state.problem.strip() or not st.session_state.code.strip():
            st.warning("Please provide both the problem and your code.")
        else:
            with st.spinner("Reading your code..."):
                store = Store(cfg["storage"]["db_path"])
                try:
                    data, cached = analyze_case(
                        llm, prompts, cfg, store,
                        st.session_state.problem, st.session_state.code,
                    )
                except Exception as err:  # show API/validation errors nicely
                    st.error(f"Analysis failed: {err}")
                    st.stop()
            st.session_state.result = {"data": data, "cached": cached}
            st.session_state.level = 0

    res = st.session_state.result
    if res:
        data = res["data"]
        if res["cached"]:
            st.caption("Loaded from cache, no API call made.")
        c1, c2 = st.columns(2)
        c1.metric("Bug category", data["bug_category"])
        c2.metric("Confidence", f"{data['confidence']:.0%}")
        with st.expander("Constraints found in the problem statement", expanded=True):
            for item in data["constraints"]:
                st.write(f"- {item}")

        for i in range(st.session_state.level):
            st.info(f"**Hint {i + 1}:** {data['hints'][i]}")
        if st.session_state.level < 3:
            st.button(
                f"Reveal hint {st.session_state.level + 1} of 3", on_click=reveal_next
            )
        else:
            st.success("Now try fixing it yourself!")

with tab_report:
    counts = Store(cfg["storage"]["db_path"]).category_counts()
    if counts:
        st.bar_chart({cat: n for cat, n in counts})
    st.code(weakness_report(counts), language=None)
