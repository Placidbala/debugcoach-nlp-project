import argparse
from pathlib import Path

from dotenv import load_dotenv

from src.prompt_loader import load_config, load_prompts, render
from src.report import weakness_report
from src.storage import Store, case_hash
from src.validator import ValidationError, parse_json, validate


def analyze_case(llm, prompts, cfg, store, problem: str, code: str):
    """Returns (result_dict, from_cache)."""
    h = case_hash(problem, code)
    cached = store.get(h)
    if cached:
        return cached, True

    categories = cfg["categories"]
    user = render(
        prompts["analyze"],
        problem=problem,
        code=code,
        categories=", ".join(categories),
    )
    raw = llm.complete(prompts["system"], user)
    try:
        data = validate(parse_json(raw), categories)
    except ValidationError as err:  # one repair attempt
        repair = render(prompts["repair"], error=str(err))
        raw = llm.complete(prompts["system"], user + "\n\n" + repair)
        data = validate(parse_json(raw), categories)

    title = problem.strip().splitlines()[0][:80] if problem.strip() else "untitled"
    store.save(h, title, data)
    return data, False


def hint_ladder(data: dict):
    print(f"\nDetected constraints: {'; '.join(data['constraints']) or 'none found'}")
    print(f"Bug category: {data['bug_category']} (confidence {data['confidence']:.0%})")
    for level, hint in enumerate(data["hints"], start=1):
        input(f"\n[Enter] to reveal hint {level}/3 ... ")
        print(f"Hint {level}: {hint}")
    print("\nNow try fixing it yourself. Good luck!")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(prog="debugcoach")
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="Analyze a failing solution")
    a.add_argument("--problem", required=True, help="Path to problem statement (.txt)")
    a.add_argument("--code", required=True, help="Path to your solution (.cpp)")
    sub.add_parser("report", help="Show your recurring bug patterns")
    args = parser.parse_args()

    cfg = load_config()
    store = Store(cfg["storage"]["db_path"])

    if args.cmd == "report":
        print(weakness_report(store.category_counts()))
        return

    from src.llm_client import LLMClient  # imported lazily so tests need no API

    prompts = load_prompts()
    problem = Path(args.problem).read_text(encoding="utf-8")
    code = Path(args.code).read_text(encoding="utf-8")
    data, cached = analyze_case(LLMClient(cfg["llm"]), prompts, cfg, store, problem, code)
    if cached:
        print("(loaded from cache, no API call made)")
    hint_ladder(data)


if __name__ == "__main__":
    main()
