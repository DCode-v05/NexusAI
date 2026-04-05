import re


def clean_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s.,!?'-]", "", text)
    return text[:512]  # distilbert max token limit


def prepare_mood_text(q1: int, q2: int, q3: int, free_text: str | None) -> str:
    parts = [
        f"Mood score: {q1}/10.",
        f"Energy level: {q2}/10.",
        f"Study motivation: {q3}/10.",
    ]
    if free_text:
        parts.append(clean_text(free_text))
    return " ".join(parts)
