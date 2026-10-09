# DebugCoach: an LLM hint-ladder tutor for coding problems

**Goal:** paste a problem statement and your failing C++ solution. DebugCoach tells you *what kind* of bug you made and reveals three progressively stronger hints, without giving away the fix. It also tracks which bug types you repeat.

## NLP tasks performed by the LLM
1. **Information extraction**: pulls constraints (input size, value ranges, time limit) out of the natural-language problem statement.
2. **Text classification**: assigns the bug to one of a fixed set of categories (see `config.yaml`).
3. **Controlled text generation**: writes a 3-level hint ladder that obeys strict rules (no code in hints 1-2, specific to the student's code).

## Architecture
```
problem.txt + solution.cpp
        |
 app.py (Streamlit UI) or main.py (CLI)
        |
   Store (SQLite): cache hit? return saved result, no API call
        |
 prompt_loader  <-- prompts/prompts.yaml  (system, analyze, repair prompts)
        |
   LLMClient    <-- config.yaml (provider, model, temperature) + .env (API key)
        |  JSON
   validator (schema check; leak check; one automatic repair retry)
        |
 Store (SQLite) --> hint ladder (UI or terminal) --> bug-pattern report
```
One LLM call per new case produces all three hints; they are revealed one by one locally, so the API is only hit once.

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your API key inside
```
Any OpenAI-compatible provider works (Groq, Gemini, OpenAI...). Change `base_url` and `model` in `config.yaml`.

The default model is `openai/gpt-oss-20b` on Groq. Model names change over time, so if you get a `model_not_found` error, pick a current model ID from your provider's list and update `config.yaml`.

## Usage
Web interface:
```bash
streamlit run app.py
```

Command line:
```bash
python -m src.main analyze --problem data/sample_cases/max_subarray_problem.txt --code data/sample_cases/max_subarray_wrong.cpp
python -m src.main report
```

Tests (run offline with a fake LLM):
```bash
python -m pytest
```

## Files
| Path | Purpose |
|---|---|
| `app.py` | Streamlit web interface |
| `src/` | source code (CLI, LLM client, validator, storage, report) |
| `prompts/prompts.yaml` | the prompt file |
| `config.yaml` | the configuration file |
| `data/sample_cases/` | demo problems with buggy solutions |
| `tests/` | unit tests |