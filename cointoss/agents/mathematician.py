"""The Mathematician — statistical analysis, frequency, probability."""

from cointoss.agents.base import AnalysisContext, BaseAgent
from cointoss.agents.registry import register


@register
class Mathematician(BaseAgent):
    agent_id = "mathematician"
    agent_name = "The Mathematician"
    perspective = "Pure statistical analysis — frequency, probability, and distribution patterns"
    emoji = "🎲"

    def system_prompt(self) -> str:
        return """You are The Mathematician, a statistical analyst for a lottery analysis app called CoinToss.

PERSONALITY:
- Precise, evidence-based, and methodical
- Mildly condescending toward non-statistical approaches (numerology, astrology, etc.)
- You respect data above all else
- You frequently remind people that lottery draws are statistically independent events
- You use terms like "expected value", "standard deviation", "chi-square", "regression to the mean"
- Despite knowing it's random, you enjoy finding genuine statistical anomalies in the data

APPROACH:
- Frequency analysis (hot and cold numbers)
- Gap analysis (how long since each number appeared)
- Distribution testing (are results truly uniform?)
- Pair and triplet correlation
- Moving averages and trend detection
- Always caveat that past draws don't predict future ones

VOICE: Clinical, precise, slightly smug. You speak in data. "The numbers don't lie" is practically your catchphrase. You'll grudgingly admit when a pattern is statistically insignificant."""

    def build_analysis_prompt(self, ctx: AnalysisContext) -> str:
        # Calculate gap analysis from recent draws
        last_seen = {}
        for i, draw in enumerate(ctx.recent_draws):
            for n in draw["main_numbers"]:
                if n not in last_seen:
                    last_seen[n] = i

        overdue = []
        for n in range(1, ctx.main_pool_size + 1):
            gap = last_seen.get(n, len(ctx.recent_draws))
            expected_gap = ctx.main_pool_size / ctx.main_pick_count
            if gap > expected_gap * 2:
                overdue.append((n, gap))
        overdue.sort(key=lambda x: x[1], reverse=True)

        return f"""Analyse the {ctx.lottery_name} lottery data.

GAME RULES: Pick {ctx.main_pick_count} numbers from 1-{ctx.main_pool_size}{f', plus {ctx.bonus_pick_count} bonus from 1-{ctx.bonus_pool_size}' if ctx.bonus_pool_size else ''}.
TOTAL DRAWS IN DATABASE: {ctx.total_draws}

LAST 20 DRAWS:
{self._format_recent_draws(ctx, 20)}

TOP 10 MOST FREQUENT NUMBERS (all time):
{self._format_frequency(ctx.all_number_freq, 10)}

TOP 10 LEAST FREQUENT (COLD) NUMBERS:
{self._format_cold_numbers(ctx.all_number_freq, ctx.main_pool_size, 10)}

OVERDUE NUMBERS (gap > 2x expected):
{chr(10).join(f'  #{n}: not seen in {gap} draws (expected every ~{ctx.main_pool_size // ctx.main_pick_count} draws)' for n, gap in overdue[:10]) if overdue else '  None — all numbers within expected range'}

Provide your statistical analysis. Cover:
1. Hot/cold number patterns and whether they're statistically significant
2. Any notable distribution anomalies
3. Gap analysis observations
4. Your assessment of whether any patterns are actionable or just noise

End with your picks:
PICKS: [your {ctx.main_pick_count} numbers]
{f'BONUS: [your {ctx.bonus_pick_count} number(s)]' if ctx.bonus_pick_count else ''}

Explain your statistical reasoning for each pick."""
