"""Host-agnostic debate engine primitives.

The package is intentionally independent from LangGraph, FastAPI, and any
application-specific persistence model. Application integrations should sit in
adapter layers outside this package.
"""

from agentic_debate.compile import CompiledDebate, DebateCompiler
from agentic_debate.context import DebateContext
from agentic_debate.engine import DebateEngine
from agentic_debate.errors import (
    DebateConfigurationError,
    DebateError,
    DebateExecutionError,
    DebateGenerationError,
    DebatePlanningError,
)
from agentic_debate.llm.base import LlmCaller
from agentic_debate.localization import OutputLocalizer, PassthroughLocalizer
from agentic_debate.methods.arbitration.heuristic import HeuristicArbitrator
from agentic_debate.methods.arbitration.llm_single_judge import LlmSingleJudgeArbitrator
from agentic_debate.methods.grouping import GroupByTopicStrategy
from agentic_debate.methods.rounds.llm import LlmChallengeSource
from agentic_debate.methods.rounds.precomputed import PrecomputedChallengeSource
from agentic_debate.methods.synthesis.passthrough import PassthroughSynthesizer
from agentic_debate.methods.transcript import SimpleTranscriptFormatter
from agentic_debate.observers.composite import CompositeObserver
from agentic_debate.observers.memory import InMemoryObserver
from agentic_debate.planning import (
    DebateIntent,
    DebatePlan,
    DebatePlanner,
    LlmDebatePlanner,
    PlannedParticipant,
)
from agentic_debate.protocols import (
    Arbitrator,
    ChallengeSource,
    DebateObserver,
    GroupingStrategy,
    Synthesizer,
    TranscriptFormatter,
)
from agentic_debate.result import DebateRoundResult, DebateRunResult
from agentic_debate.spec import (
    ArbitrationPolicy,
    DebateSpec,
    PersistencePolicy,
    RoundPolicy,
    SynthesisPolicy,
    TranscriptPolicy,
)
from agentic_debate.types import (
    DebateArbitration,
    DebateChallenge,
    DebateEvidence,
    DebateParticipant,
    DebateSubject,
    DebateTopicGroup,
    DebateVerdict,
)

__all__ = [
    # Core engine
    "CompiledDebate",
    "DebateCompiler",
    "DebateContext",
    "DebateEngine",
    # Protocols (extension points)
    "Arbitrator",
    "ChallengeSource",
    "DebateObserver",
    "GroupingStrategy",
    "Synthesizer",
    "TranscriptFormatter",
    # LLM
    "LlmCaller",
    "LlmSingleJudgeArbitrator",
    # Localization
    "OutputLocalizer",
    "PassthroughLocalizer",
    # Built-in implementations
    "CompositeObserver",
    "GroupByTopicStrategy",
    "HeuristicArbitrator",
    "InMemoryObserver",
    "LlmChallengeSource",
    "PassthroughSynthesizer",
    "PrecomputedChallengeSource",
    "SimpleTranscriptFormatter",
    # Planning
    "DebateIntent",
    "DebatePlan",
    "DebatePlanner",
    "LlmDebatePlanner",
    "PlannedParticipant",
    # Spec / policies
    "ArbitrationPolicy",
    "DebateSpec",
    "PersistencePolicy",
    "RoundPolicy",
    "SynthesisPolicy",
    "TranscriptPolicy",
    # Types
    "DebateArbitration",
    "DebateChallenge",
    "DebateEvidence",
    "DebateParticipant",
    "DebateRoundResult",
    "DebateRunResult",
    "DebateSubject",
    "DebateTopicGroup",
    "DebateVerdict",
    # Errors
    "DebateConfigurationError",
    "DebateError",
    "DebateExecutionError",
    "DebateGenerationError",
    "DebatePlanningError",
]
