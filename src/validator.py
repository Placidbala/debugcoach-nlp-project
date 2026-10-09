import json
import re


class ValidationError(ValueError):
    pass


def parse_json(raw: str) -> dict:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    raise ValidationError("Response is not valid JSON")


def validate(data: dict, categories: list) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Top-level value must be a JSON object")
    for key in ("constraints", "bug_category", "confidence", "hints"):
        if key not in data:
            raise ValidationError(f"Missing key: {key}")

    if data["bug_category"] not in categories:
        raise ValidationError(f"bug_category must be one of: {', '.join(categories)}")

    conf = data["confidence"]
    if not isinstance(conf, (int, float)) or not 0 <= conf <= 1:
        raise ValidationError("confidence must be a number between 0 and 1")

    if not isinstance(data["constraints"], list) or not all(
        isinstance(c, str) for c in data["constraints"]
    ):
        raise ValidationError("constraints must be a list of strings")

    hints = data["hints"]
    if (
        not isinstance(hints, list)
        or len(hints) != 3
        or not all(isinstance(h, str) and h.strip() for h in hints)
    ):
        raise ValidationError("hints must be a list of exactly 3 non-empty strings")

    if any("```" in h for h in hints[:2]):
        raise ValidationError("Hints 1 and 2 must not contain code blocks")
    return data
