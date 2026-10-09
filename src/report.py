def weakness_report(counts) -> str:
    if not counts:
        return "No analyses yet. Run `python -m src.main analyze ...` first."
    total = sum(c for _, c in counts)
    lines = [f"Your bug patterns across {total} analyzed solution(s):", ""]
    for category, n in counts:
        bar = "#" * n
        lines.append(f"{category:<22} {bar} {n} ({n / total:.0%})")
    lines += ["", f"Most frequent: {counts[0][0]}. Focus your practice there."]
    return "\n".join(lines)
