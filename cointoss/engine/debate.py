"""Debate orchestrator — runs multi-agent debates with configurable rounds."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime

from cointoss.agents.base import AnalysisContext, AnalysisResult, BaseAgent

logger = logging.getLogger(__name__)


@dataclass
class DebateRound:
    """A single round of the debate."""
    round_number: int
    round_type: str  # "analysis", "challenge", "defense", "final"
    entries: list[DebateEntry] = field(default_factory=list)


@dataclass
class DebateEntry:
    """A single agent's contribution in a round."""
    agent_id: str
    agent_name: str
    emoji: str
    text: str
    target_agent_id: str | None = None  # who they're responding to
    picks: list[int] | None = None
    bonus: list[int] | None = None


@dataclass
class DebateTranscript:
    """Full transcript of a multi-agent debate."""
    lottery_id: str
    lottery_name: str
    target_date: str
    agents: list[str]
    rounds: list[DebateRound] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def all_picks(self) -> dict[str, dict]:
        """Extract final picks from each agent. Returns {agent_id: {numbers, bonus}}."""
        picks = {}
        # Walk rounds in reverse to find each agent's latest picks
        for round_ in reversed(self.rounds):
            for entry in round_.entries:
                if entry.agent_id not in picks and entry.picks:
                    picks[entry.agent_id] = {
                        "numbers": entry.picks,
                        "bonus": entry.bonus,
                        "agent_name": entry.agent_name,
                        "emoji": entry.emoji,
                    }
        return picks


class DebateOrchestrator:
    """Orchestrates a multi-agent debate."""

    def __init__(self, agents: list[BaseAgent], rounds: int = 1):
        self.agents = agents
        self.rounds = min(rounds, 3)  # cap at 3 challenge/defense rounds

    def run(self, ctx: AnalysisContext) -> DebateTranscript:
        """Run a full debate and return the transcript."""
        transcript = DebateTranscript(
            lottery_id=ctx.lottery_id,
            lottery_name=ctx.lottery_name,
            target_date=str(ctx.target_date),
            agents=[a.agent_id for a in self.agents],
        )

        # Round 1: All agents analyse independently
        logger.info("Debate Round 1: Opening analyses")
        analysis_round = DebateRound(round_number=1, round_type="analysis")
        results: dict[str, AnalysisResult] = {}

        for agent in self.agents:
            logger.info(f"  {agent.agent_id} analysing...")
            result = agent.predict(ctx)
            results[agent.agent_id] = result
            analysis_round.entries.append(DebateEntry(
                agent_id=agent.agent_id,
                agent_name=agent.agent_name,
                emoji=agent.emoji,
                text=result.analysis,
                picks=result.picks.numbers if result.picks else None,
                bonus=result.picks.bonus if result.picks else None,
            ))

        transcript.rounds.append(analysis_round)

        # Challenge/Defense rounds
        for round_num in range(self.rounds):
            # Challenge round
            logger.info(f"Debate Round {2 + round_num * 2}: Challenges")
            challenge_round = DebateRound(
                round_number=2 + round_num * 2,
                round_type="challenge",
            )

            challenges: dict[str, dict] = {}  # {challenger_id: {target_id, text}}
            for i, agent in enumerate(self.agents):
                # Each agent challenges the next agent in the list (circular)
                target = self.agents[(i + 1) % len(self.agents)]
                target_result = results[target.agent_id]

                logger.info(f"  {agent.agent_id} challenges {target.agent_id}")
                challenge_text = agent.challenge(target_result, ctx)

                challenges[agent.agent_id] = {
                    "target_id": target.agent_id,
                    "text": challenge_text,
                }

                challenge_round.entries.append(DebateEntry(
                    agent_id=agent.agent_id,
                    agent_name=agent.agent_name,
                    emoji=agent.emoji,
                    text=challenge_text,
                    target_agent_id=target.agent_id,
                ))

            transcript.rounds.append(challenge_round)

            # Defense round
            logger.info(f"Debate Round {3 + round_num * 2}: Defenses")
            defense_round = DebateRound(
                round_number=3 + round_num * 2,
                round_type="defense",
            )

            for agent in self.agents:
                # Find who challenged this agent
                challenger_id = None
                challenge_text = ""
                for cid, cdata in challenges.items():
                    if cdata["target_id"] == agent.agent_id:
                        challenger_id = cid
                        challenge_text = cdata["text"]
                        break

                if not challenge_text:
                    continue

                logger.info(f"  {agent.agent_id} defends against {challenger_id}")
                defense_text = agent.defend(
                    challenge_text,
                    results[agent.agent_id].analysis,
                )

                defense_round.entries.append(DebateEntry(
                    agent_id=agent.agent_id,
                    agent_name=agent.agent_name,
                    emoji=agent.emoji,
                    text=defense_text,
                    target_agent_id=challenger_id,
                ))

            transcript.rounds.append(defense_round)

        return transcript
