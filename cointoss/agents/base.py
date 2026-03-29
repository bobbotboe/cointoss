"""Base agent interface for CoinToss lottery analysts."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date

import anthropic

from cointoss.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Context passed to agents for analysis."""
    lottery_id: str
    lottery_name: str
    main_pool_size: int
    main_pick_count: int
    bonus_pool_size: int | None
    bonus_pick_count: int
    recent_draws: list[dict]  # [{date, main_numbers, bonus_numbers}, ...]
    all_number_freq: dict[int, int]  # number -> count across all draws
    bonus_freq: dict[int, int]
    total_draws: int
    moon_phase: dict | None = None  # {phase_name, illumination, phase_angle}
    planetary: dict | None = None  # {sun_lon, moon_lon, mercury_lon, ...}
    target_date: date | None = None  # date being analysed or predicted for


@dataclass
class AgentPick:
    """A number pick with reasoning."""
    numbers: list[int]
    bonus: list[int] | None = None
    reasoning: str = ""


@dataclass
class AnalysisResult:
    """Result from an agent's analysis."""
    agent_id: str
    agent_name: str
    perspective: str  # one-line description of the agent's lens
    analysis: str  # the full analysis text
    picks: AgentPick | None = None
    confidence: str = "medium"  # low / medium / high
    raw_response: str = ""


@dataclass
class Challenge:
    """A challenge from one agent to another."""
    challenger_id: str
    target_id: str
    challenge_text: str
    target_analysis: str


@dataclass
class Defense:
    """An agent's defense against a challenge."""
    agent_id: str
    defense_text: str


class BaseAgent(ABC):
    """Base class for all CoinToss analyst agents."""

    agent_id: str = ""
    agent_name: str = ""
    perspective: str = ""
    emoji: str = ""

    def __init__(self):
        self._client: anthropic.Anthropic | None = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt defining this agent's personality and approach."""
        ...

    @abstractmethod
    def build_analysis_prompt(self, ctx: AnalysisContext) -> str:
        """Build the user prompt for analysis given the context."""
        ...

    def analyse(self, ctx: AnalysisContext) -> AnalysisResult:
        """Analyse lottery data through this agent's lens."""
        response = self._call_llm(
            system=self.system_prompt(),
            user=self.build_analysis_prompt(ctx),
        )

        # Try to parse structured response
        picks = self._extract_picks(response)

        return AnalysisResult(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            perspective=self.perspective,
            analysis=response,
            picks=picks,
            raw_response=response,
        )

    def predict(self, ctx: AnalysisContext) -> AnalysisResult:
        """Generate number picks with reasoning."""
        prompt = self.build_analysis_prompt(ctx) + "\n\nBased on your analysis, provide your number picks for the next draw. Format your picks as:\nPICKS: [comma-separated main numbers] + BONUS: [bonus number(s)]\nThen explain your reasoning."

        response = self._call_llm(
            system=self.system_prompt(),
            user=prompt,
        )

        picks = self._extract_picks(response)

        return AnalysisResult(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            perspective=self.perspective,
            analysis=response,
            picks=picks,
            raw_response=response,
        )

    def challenge(self, other_result: AnalysisResult, ctx: AnalysisContext) -> str:
        """Challenge another agent's analysis."""
        prompt = f"""Another analyst ({other_result.agent_name}) has provided this analysis:

---
{other_result.analysis}
---

Their picks: {other_result.picks.numbers if other_result.picks else 'None provided'}

Challenge their reasoning from your perspective. Be specific about what you disagree with and why. Stay in character."""

        return self._call_llm(
            system=self.system_prompt(),
            user=prompt,
        )

    def defend(self, challenge_text: str, original_analysis: str) -> str:
        """Defend your analysis against a challenge."""
        prompt = f"""Your original analysis was:

---
{original_analysis}
---

Another analyst challenges you:

---
{challenge_text}
---

Defend your position. Address their specific points. Stay in character."""

        return self._call_llm(
            system=self.system_prompt(),
            user=prompt,
        )

    def _call_llm(self, system: str, user: str) -> str:
        """Call the LLM and return the text response."""
        logger.debug(f"[{self.agent_id}] Calling LLM ({len(system)} sys chars, {len(user)} user chars)")

        message = self.client.messages.create(
            model=settings.llm_model,
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        text = message.content[0].text
        logger.debug(f"[{self.agent_id}] Response: {len(text)} chars, {message.usage.input_tokens}+{message.usage.output_tokens} tokens")
        return text

    def _extract_picks(self, text: str) -> AgentPick | None:
        """Try to extract number picks from response text."""
        import re

        # Look for PICKS: pattern
        picks_match = re.search(r"PICKS?:\s*\[?([\d,\s]+)\]?", text, re.IGNORECASE)
        if not picks_match:
            return None

        try:
            numbers = [int(n.strip()) for n in picks_match.group(1).split(",") if n.strip().isdigit()]
        except ValueError:
            return None

        if not numbers:
            return None

        # Look for BONUS: pattern
        bonus = None
        bonus_match = re.search(r"BONUS:\s*\[?([\d,\s]+)\]?", text, re.IGNORECASE)
        if bonus_match:
            try:
                bonus = [int(n.strip()) for n in bonus_match.group(1).split(",") if n.strip().isdigit()]
            except ValueError:
                pass

        # Extract reasoning (everything after the picks line)
        reasoning = ""
        reasoning_match = re.search(r"(?:reason|explain|because|rationale)[:\s]*(.*)", text, re.IGNORECASE | re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()[:500]

        return AgentPick(numbers=sorted(numbers), bonus=bonus, reasoning=reasoning)

    def _format_recent_draws(self, ctx: AnalysisContext, n: int = 20) -> str:
        """Format recent draws as readable text."""
        lines = []
        for draw in ctx.recent_draws[:n]:
            bonus_str = f" + {draw['bonus_numbers']}" if draw.get('bonus_numbers') else ""
            lines.append(f"  {draw['date']}: {draw['main_numbers']}{bonus_str}")
        return "\n".join(lines)

    def _format_frequency(self, freq: dict[int, int], top_n: int = 10) -> str:
        """Format top N frequent numbers."""
        sorted_freq = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        lines = [f"  #{n}: {count} times" for n, count in sorted_freq[:top_n]]
        return "\n".join(lines)

    def _format_cold_numbers(self, freq: dict[int, int], pool_size: int, top_n: int = 10) -> str:
        """Format least frequent (cold) numbers."""
        # Include numbers that never appeared
        full_freq = {i: freq.get(i, 0) for i in range(1, pool_size + 1)}
        sorted_freq = sorted(full_freq.items(), key=lambda x: x[1])
        lines = [f"  #{n}: {count} times" for n, count in sorted_freq[:top_n]]
        return "\n".join(lines)
