"""Unit tests for agents.orchestrator.router_logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from agents.orchestrator.router_logic import route, _match_crisis_keywords


# ── _match_crisis_keywords ────────────────────────────────────────────────────

class TestCrisisKeywords:
    def test_suicidal_matches(self):
        hit, kws = _match_crisis_keywords("I am feeling suicidal")
        assert hit is True
        assert len(kws) > 0

    def test_suicide_stem_matches(self):
        hit, kws = _match_crisis_keywords("thinking about suicide")
        assert hit is True

    def test_self_harm_matches(self):
        hit, kws = _match_crisis_keywords("I started self-harming again")
        assert hit is True

    def test_kill_myself_matches(self):
        hit, kws = _match_crisis_keywords("I want to kill myself")
        assert hit is True

    def test_overdose_matches(self):
        hit, kws = _match_crisis_keywords("I took an overdose last night")
        assert hit is True

    def test_fiction_context_suppressed(self):
        # "Suicide Squad" movie reference — should NOT fire
        hit, _ = _match_crisis_keywords("Did you watch the Suicide Squad movie?")
        assert hit is False

    def test_negation_suppresses_match(self):
        hit, _ = _match_crisis_keywords("I would never want to kill myself")
        assert hit is False

    def test_personal_marker_overrides_fiction(self):
        # Even if fiction token present, personal marker forces the signal
        hit, _ = _match_crisis_keywords("I feel like ending it all, it's not a movie")
        assert hit is True

    def test_antidote_does_not_match_suicide(self):
        hit, _ = _match_crisis_keywords("looking for an antidote to the poison")
        assert hit is False

    def test_empty_string(self):
        hit, kws = _match_crisis_keywords("")
        assert hit is False
        assert kws == []


# ── route() ──────────────────────────────────────────────────────────────────

class TestRoute:
    def test_crisis_keyword_routes_crisis(self):
        agent, kws = route(0.0, "I want to kill myself")
        assert agent == "crisis"
        assert len(kws) > 0

    def test_high_risk_score_routes_crisis(self):
        agent, kws = route(0.85, "I feel okay")
        assert agent == "crisis"

    def test_pathway_keywords_route_pathway(self):
        agent, _ = route(0.1, "I need help with my resume and job search")
        assert agent == "pathway"

    def test_wellbeing_keywords_route_wellbeing(self):
        agent, _ = route(0.1, "I feel very sad and overwhelmed today")
        assert agent == "wellbeing"

    def test_moderate_risk_routes_wellbeing(self):
        agent, _ = route(0.5, "Just a random message")
        assert agent == "wellbeing"

    def test_low_risk_no_keywords_routes_pathway(self):
        agent, _ = route(0.1, "What is the weather like?")
        assert agent == "pathway"

    def test_crisis_overrides_pathway_keywords(self):
        # Even if pathway keyword is present, crisis takes priority
        agent, kws = route(0.0, "career advice please, I also want to end my life")
        assert agent == "crisis"
        assert len(kws) > 0

    def test_returns_tuple(self):
        result = route(0.0, "hello")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_no_triggered_keywords_when_no_crisis(self):
        _, kws = route(0.2, "feeling a bit stressed about exams")
        assert kws == []
