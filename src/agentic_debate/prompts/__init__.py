"""Built-in prompt templates for the agentic-debate library."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files


@dataclass(frozen=True)
class PlanningPromptSet:
    """Prompt templates required by the built-in LLM planner."""

    intent_prompt_template: str
    team_prompt_template: str


@dataclass(frozen=True)
class ChallengePromptSet:
    """Prompt templates required by the built-in LLM challenge source."""

    first_round_prompt_template: str
    rebuttal_prompt_template: str


def _read_prompt(filename: str) -> str:
    return files("agentic_debate.prompts").joinpath(filename).read_text(encoding="utf-8")


def load_builtin_planning_prompt_set() -> PlanningPromptSet:
    """Return the packaged planning prompt templates."""
    return PlanningPromptSet(
        intent_prompt_template=_read_prompt("planning_intent.md"),
        team_prompt_template=_read_prompt("planning_team.md"),
    )


def load_builtin_challenge_prompt_set() -> ChallengePromptSet:
    """Return the packaged challenge generation prompt templates."""
    return ChallengePromptSet(
        first_round_prompt_template=_read_prompt("challenge_first_round.md"),
        rebuttal_prompt_template=_read_prompt("challenge_rebuttal.md"),
    )


def load_builtin_judge_prompt() -> str:
    """Return the packaged default judge prompt."""
    return _read_prompt("judge_generic.md")


__all__ = [
    "ChallengePromptSet",
    "PlanningPromptSet",
    "load_builtin_challenge_prompt_set",
    "load_builtin_judge_prompt",
    "load_builtin_planning_prompt_set",
]
