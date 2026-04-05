"""Route requests to the appropriate specialist agent.

Decision logic (from PDF slide 4 — Student Journey):
  1. Crisis keywords OR risk >= 0.8 → Crisis Agent
  2. Career/pathway keywords → Pathway Agent
  3. Risk >= 0.4 (moderate+) → Wellbeing Agent (MindBridge)
  4. Risk < 0.4 (low/none) → Pathway Agent (career guidance by default)
"""
from __future__ import annotations

import re

CRISIS_THRESHOLD = 0.8
MODERATE_THRESHOLD = 0.4

# ---------------------------------------------------------------------------
# Crisis keyword matching — compiled regex patterns with word boundaries.
# Using \b ensures "suicidal" matches but "antidote" does not.
# Covers stem variants and common phrasings.
# ---------------------------------------------------------------------------
_CRISIS_PATTERNS: list[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in [
    r"\bsuicid(e|al|ally)\b",
    r"\bself[- ]?harm(ing|ed)?\b",
    r"\bself[- ]?hurt(ing|ed)?\b",
    r"\bkill myself\b",
    r"\bend my life\b",
    r"\bwant(ed)? to die\b",
    r"\bno reason to live\b",
    r"\bhurt(ing)? myself\b",
    r"\bworthless(ness)?\b",
    r"\bcan'?t go on\b",
    r"\bgive up on (my )?life\b",
    r"\bdon'?t want to exist\b",
    r"\boverdos(e|ing|ed)\b",          # OD risk
    r"\bcut(ting)? (my)?self\b",
    r"\bending it (all)?\b",
    r"\bnot worth living\b",
    r"\blife is (not |)?worth\b",
]]

# Phrases that strongly suggest pop-culture / fictional context
# (movie title, game, etc.) — reduces false positives
_FICTION_TOKENS = {
    "movie", "film", "game", "book", "song", "show", "series", "episode",
    "character", "meme", "joke", "comic", "anime", "manga", "novel",
    "chapter", "villain", "superhero", "plot", "story", "scene", "lyrics",
    "music video", "trailer", "review", "watched", "played", "read",
    "suicide squad", "squad", "13 reasons", "thirteen reasons",
}

# Personal-language markers — if present alongside fiction tokens, keep the signal
_PERSONAL_MARKERS = re.compile(
    r"\b(i am|i'm|i feel|i want|i need|i can'?t|i keep|myself|my life|my pain|my mind)\b",
    re.IGNORECASE,
)

# Negation words within a 5-word window before a matched phrase reduce confidence
_NEGATION_WORDS = {
    "don't", "dont", "doesn't", "doesnt", "didn't", "didnt",
    "not", "never", "no", "won't", "wont", "wouldn't", "wouldnt",
    "can't", "cant", "cannot", "haven't", "havent", "shouldn't", "shouldnt",
}


def _match_crisis_keywords(text: str) -> tuple[bool, list[str]]:
    """Return (hit, matched_keyword_list) with false-positive reduction.

    Steps:
      1. Run regex patterns against lowercased text.
      2. If fiction-context tokens dominate and no personal-language markers → skip.
      3. Check for negation in a 5-word window before each match → reduce count.
    """
    lower = text.lower()
    matched_spans: list[tuple[str, int]] = []

    for pat in _CRISIS_PATTERNS:
        m = pat.search(lower)
        if m:
            matched_spans.append((m.group(), m.start()))

    if not matched_spans:
        return False, []

    # Fiction context filter
    has_fiction = any(tok in lower for tok in _FICTION_TOKENS)
    if has_fiction and not _PERSONAL_MARKERS.search(lower):
        return False, []

    # Negation window: 5 words before the match position
    words = lower.split()
    confirmed: list[str] = []
    for keyword, start_char in matched_spans:
        # Count words before the match
        prefix = lower[:start_char]
        prefix_words = prefix.split()
        window = prefix_words[-5:] if len(prefix_words) >= 5 else prefix_words
        if not any(w in _NEGATION_WORDS for w in window):
            confirmed.append(keyword)

    return bool(confirmed), confirmed


# ---------------------------------------------------------------------------
# Pathway / wellbeing keywords remain simple set lookups (low FP risk)
# ---------------------------------------------------------------------------
PATHWAY_KEYWORDS = {
    "job", "career", "resume", "skill", "roadmap", "internship",
    "placement", "interview", "course", "certification", "linkedin",
    "naukri", "salary", "company", "hiring", "upskill", "project",
    "portfolio", "github", "swayam", "coursera", "pmkvy", "scheme",
}

WELLBEING_KEYWORDS = {
    "sad", "anxious", "stressed", "worried", "lonely", "depressed",
    "overwhelmed", "tired", "scared", "panic", "cry", "sleep",
    "angry", "frustrated", "burnout", "exhausted", "nervous",
    "mood", "feeling", "mental", "help me", "struggling",
}


def route(risk_score: float, text: str = "") -> tuple[str, list[str]]:
    """Return (agent_name, triggered_crisis_keywords).

    agent_name: 'crisis' | 'wellbeing' | 'pathway'
    triggered_crisis_keywords: non-empty only when crisis keywords matched.
    """
    # 1. Crisis always takes priority
    keyword_hit, matched_keywords = _match_crisis_keywords(text)
    if risk_score >= CRISIS_THRESHOLD or keyword_hit:
        return "crisis", matched_keywords

    lower = text.lower()

    # 2. Explicit career/pathway intent
    if any(kw in lower for kw in PATHWAY_KEYWORDS):
        return "pathway", []

    # 3. Explicit wellbeing intent
    if any(kw in lower for kw in WELLBEING_KEYWORDS):
        return "wellbeing", []

    # 4. Risk-level-based default routing
    if risk_score >= MODERATE_THRESHOLD:
        return "wellbeing", []

    return "pathway", []
