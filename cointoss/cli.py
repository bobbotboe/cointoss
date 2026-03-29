"""CoinToss CLI — import data, validate, and query lottery results."""

import argparse
import logging
import sys
from datetime import date

from rich.console import Console
from rich.table import Table

from cointoss.data.database import get_session, init_db

console = Console()
logger = logging.getLogger("cointoss")


def cmd_init(args):
    """Initialise database and seed lottery configs."""
    init_db()
    console.print("[green]Database initialised and lottery configs seeded.[/green]")


def cmd_import_us(args):
    """Import US lottery data from NY Open Data."""
    from cointoss.data.importers.ny_open_data import NYOpenDataImporter

    init_db()
    session = get_session()
    importer = NYOpenDataImporter(session)
    since = date.fromisoformat(args.since) if args.since else None

    if args.lottery:
        count = importer.import_single_lottery(args.lottery, since)
    else:
        count = importer.import_draws(since)

    console.print(f"[green]Imported {count} new US draws.[/green]")
    session.close()


def cmd_import_au(args):
    """Import Australian lottery data."""
    from cointoss.data.importers.au_lotteries import AustralianLotteryImporter

    init_db()
    session = get_session()
    importer = AustralianLotteryImporter(session)

    if args.csv:
        if not args.lottery:
            console.print("[red]--lottery is required when importing from CSV[/red]")
            sys.exit(1)
        count = importer.import_from_csv(args.csv, args.lottery)
    elif args.lottery:
        count = importer.import_single_lottery(args.lottery)
    else:
        count = importer.import_draws()

    console.print(f"[green]Imported {count} new AU draws.[/green]")
    session.close()


def cmd_import_lotto_america(args):
    """Import Lotto America data."""
    from cointoss.data.importers.lotto_america import LottoAmericaImporter

    init_db()
    session = get_session()
    importer = LottoAmericaImporter(session)
    since = date.fromisoformat(args.since) if args.since else None
    count = importer.import_draws(since)
    console.print(f"[green]Imported {count} new Lotto America draws.[/green]")
    session.close()


def cmd_celestial(args):
    """Populate celestial data for a date range."""
    from cointoss.data.celestial import populate_celestial_data

    init_db()
    session = get_session()
    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    count = populate_celestial_data(session, start, end)
    console.print(f"[green]Computed celestial data for {count} dates.[/green]")
    session.close()


def cmd_validate(args):
    """Validate imported draw data."""
    from cointoss.data.validation import find_duplicates, validate_all

    init_db()
    session = get_session()
    results = validate_all(session)

    table = Table(title="Validation Results")
    table.add_column("Lottery", style="cyan")
    table.add_column("Draws", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Errors", justify="right")

    for lottery_id, result in results.items():
        status = "[green]OK[/green]" if result.is_valid else "[red]ERRORS[/red]"
        table.add_row(lottery_id, str(result.total_draws), status, str(len(result.errors)))

    console.print(table)

    dupes = find_duplicates(session)
    if dupes:
        console.print(f"\n[yellow]Found {len(dupes)} duplicate draw entries[/yellow]")
        for lottery_id, draw_date, cnt in dupes:
            console.print(f"  {lottery_id} {draw_date}: {cnt} entries")

    session.close()


def cmd_stats(args):
    """Show stats for all lotteries."""
    from cointoss.data.queries import get_stats_summary, list_lotteries

    init_db()
    session = get_session()
    lotteries = list_lotteries(session, country=args.country)

    table = Table(title="Lottery Data Summary")
    table.add_column("Lottery", style="cyan")
    table.add_column("Country")
    table.add_column("Draws", justify="right")
    table.add_column("Earliest")
    table.add_column("Latest")
    table.add_column("Latest Numbers", style="yellow")

    for lottery in lotteries:
        stats = get_stats_summary(session, lottery.id)
        nums = ", ".join(str(n) for n in stats["latest_numbers"]) if stats["latest_numbers"] else "-"
        table.add_row(
            lottery.name, lottery.country,
            str(stats["total_draws"]),
            stats["earliest_date"] or "-",
            stats["latest_date"] or "-",
            nums,
        )

    console.print(table)
    session.close()


def cmd_frequency(args):
    """Show number frequency for a lottery."""
    from cointoss.data.queries import get_lottery, get_number_frequency

    init_db()
    session = get_session()
    lottery = get_lottery(session, args.lottery)
    if not lottery:
        console.print(f"[red]Unknown lottery: {args.lottery}[/red]")
        sys.exit(1)

    freq = get_number_frequency(session, args.lottery, last_n=args.last)

    table = Table(title=f"Number Frequency — {lottery.name}" + (f" (last {args.last})" if args.last else ""))
    table.add_column("Number", justify="right", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Bar")

    max_count = max(freq.values()) if freq else 1
    for num, count in freq.items():
        bar_len = int((count / max_count) * 40)
        table.add_row(str(num), str(count), "[yellow]" + "█" * bar_len + "[/yellow]")

    console.print(table)
    session.close()


def cmd_analyse(args):
    """Run one or all agents on a lottery."""
    import cointoss.agents  # noqa: F401 — triggers registration
    from cointoss.agents.registry import build_context, get_agent, list_agents

    init_db()
    session = get_session()
    target = date.fromisoformat(args.date) if args.date else None
    ctx = build_context(session, args.lottery, target_date=target)

    if args.agent:
        agents = [get_agent(args.agent)]
    else:
        agents = list_agents()

    for agent in agents:
        console.print(f"\n[bold]{agent.emoji} {agent.agent_name}[/bold]")
        console.print(f"[dim]{agent.perspective}[/dim]\n")

        try:
            result = agent.predict(ctx)
            console.print(result.analysis)

            if result.picks:
                console.print(f"\n[bold yellow]PICKS: {result.picks.numbers}[/bold yellow]")
                if result.picks.bonus:
                    console.print(f"[bold cyan]BONUS: {result.picks.bonus}[/bold cyan]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        console.print("\n" + "─" * 60)

    session.close()


def cmd_debate(args):
    """Run a full multi-agent debate with synthesis."""
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import get_agent, list_agents
    from cointoss.engine.debate import DebateOrchestrator
    from cointoss.engine.modes import pre_draw_prediction
    from cointoss.engine.scoring import save_predictions
    from cointoss.engine.synthesis import synthesise

    init_db()
    session = get_session()
    target = date.fromisoformat(args.date) if args.date else None
    rounds = args.rounds or 1

    # Select agents
    if args.agents:
        agent_list = [get_agent(aid.strip()) for aid in args.agents.split(",")]
    else:
        agent_list = list_agents()

    agent_names = ", ".join(f"{a.emoji} {a.agent_name}" for a in agent_list)
    console.print(f"[bold]Debate: {agent_names}[/bold]")
    console.print(f"[dim]Lottery: {args.lottery} | Rounds: {rounds}[/dim]\n")

    transcript, consensus = pre_draw_prediction(
        session, args.lottery, agents=agent_list,
        target_date=target, debate_rounds=rounds,
    )

    # Print transcript
    for round_ in transcript.rounds:
        round_labels = {"analysis": "Opening Analyses", "challenge": "Challenges", "defense": "Defenses"}
        label = round_labels.get(round_.round_type, round_.round_type.title())
        console.print(f"\n[bold cyan]═══ Round {round_.round_number}: {label} ═══[/bold cyan]\n")

        for entry in round_.entries:
            target_str = f" → {entry.target_agent_id}" if entry.target_agent_id else ""
            console.print(f"[bold]{entry.emoji} {entry.agent_name}{target_str}:[/bold]")
            console.print(entry.text)
            console.print()

    # Print synthesis
    _print_consensus(consensus)

    # Save predictions
    saved = save_predictions(session, transcript.all_picks, args.lottery, target or date.today())
    if saved:
        console.print(f"\n[green]Saved {saved} predictions for scoring.[/green]")

    session.close()


def cmd_predict(args):
    """Quick prediction — all agents pick, no debate, with consensus."""
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import build_context, list_agents
    from cointoss.engine.scoring import save_predictions
    from cointoss.engine.synthesis import ConsensusResult, synthesise
    from cointoss.engine.debate import DebateTranscript, DebateRound, DebateEntry

    init_db()
    session = get_session()
    target = date.fromisoformat(args.date) if args.date else None
    ctx = build_context(session, args.lottery, target_date=target)
    agent_list = list_agents()

    console.print(f"[bold]Quick Prediction: {ctx.lottery_name}[/bold]")
    console.print(f"[dim]Target: {ctx.target_date} | {len(agent_list)} agents[/dim]\n")

    # Build a simple transcript for synthesis
    transcript = DebateTranscript(
        lottery_id=ctx.lottery_id,
        lottery_name=ctx.lottery_name,
        target_date=str(ctx.target_date),
        agents=[a.agent_id for a in agent_list],
    )
    analysis_round = DebateRound(round_number=1, round_type="analysis")

    for agent in agent_list:
        console.print(f"[bold]{agent.emoji} {agent.agent_name}[/bold]")
        try:
            result = agent.predict(ctx)
            console.print(result.analysis)
            if result.picks:
                console.print(f"\n  [yellow]PICKS: {result.picks.numbers}[/yellow]" +
                              (f" + [cyan]{result.picks.bonus}[/cyan]" if result.picks.bonus else ""))
            analysis_round.entries.append(DebateEntry(
                agent_id=agent.agent_id, agent_name=agent.agent_name, emoji=agent.emoji,
                text=result.analysis,
                picks=result.picks.numbers if result.picks else None,
                bonus=result.picks.bonus if result.picks else None,
            ))
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
        console.print("\n" + "─" * 60 + "\n")

    transcript.rounds.append(analysis_round)
    consensus = synthesise(transcript)
    _print_consensus(consensus)

    saved = save_predictions(session, transcript.all_picks, args.lottery, target or date.today())
    if saved:
        console.print(f"\n[green]Saved {saved} predictions for scoring.[/green]")
    session.close()


def cmd_post_draw(args):
    """Post-draw analysis — agents explain why these numbers came up."""
    import cointoss.agents  # noqa: F401
    from cointoss.engine.modes import post_draw_analysis

    init_db()
    session = get_session()
    draw_date = date.fromisoformat(args.date)

    console.print(f"[bold]Post-Draw Analysis: {args.lottery} on {draw_date}[/bold]\n")

    try:
        results = post_draw_analysis(session, args.lottery, draw_date)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        session.close()
        return

    from cointoss.agents.registry import get_agent
    for agent_id, text in results.items():
        agent = get_agent(agent_id)
        console.print(f"[bold]{agent.emoji} {agent.agent_name}:[/bold]")
        console.print(text)
        console.print("\n" + "─" * 60 + "\n")

    session.close()


def cmd_score(args):
    """Score predictions against actual results."""
    from cointoss.engine.scoring import score_predictions

    init_db()
    session = get_session()
    scored = score_predictions(session, lottery_id=args.lottery)
    console.print(f"[green]Scored {scored} predictions.[/green]")
    session.close()


def cmd_leaderboard(args):
    """Show agent leaderboard."""
    from cointoss.engine.scoring import get_leaderboard

    init_db()
    session = get_session()
    entries = get_leaderboard(session, lottery_id=args.lottery)

    if not entries:
        console.print("[yellow]No scored predictions yet. Run 'score' after a draw to see results.[/yellow]")
        session.close()
        return

    table = Table(title="Agent Leaderboard" + (f" — {args.lottery}" if args.lottery else ""))
    table.add_column("#", justify="right", style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("Predictions", justify="right")
    table.add_column("Avg Hits", justify="right", style="yellow")
    table.add_column("Best", justify="right", style="green")
    table.add_column("Total Hits", justify="right")
    table.add_column("Bonus Hits", justify="right")

    for entry in entries:
        table.add_row(
            str(entry.rank), entry.agent_id, str(entry.predictions),
            f"{entry.avg_hits:.2f}", str(entry.best_hits),
            str(entry.total_hits), str(entry.bonus_hits),
        )

    console.print(table)
    session.close()


def cmd_told_you_so(args):
    """Show 'I told you so' moments — predictions with 3+ hits."""
    from cointoss.engine.scoring import get_told_you_so

    init_db()
    session = get_session()
    moments = get_told_you_so(session, lottery_id=args.lottery)

    if not moments:
        console.print("[yellow]No 'I told you so' moments yet. Keep predicting![/yellow]")
        session.close()
        return

    table = Table(title="I Told You So! (3+ hits)")
    table.add_column("Agent", style="cyan")
    table.add_column("Date")
    table.add_column("Predicted", style="dim")
    table.add_column("Actual", style="dim")
    table.add_column("Hits", style="bold yellow")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Bonus?", justify="center")

    for m in moments:
        table.add_row(
            m["agent_id"], m["date"],
            str(m["predicted"]), str(m["actual"]),
            str(m["hits"]), str(m["hit_count"]),
            "[green]✓[/green]" if m["bonus_hit"] else "",
        )

    console.print(table)
    session.close()


def _print_consensus(consensus):
    """Pretty-print a consensus result."""
    console.print(f"\n[bold cyan]═══ CONSENSUS ═══[/bold cyan]\n")

    if not consensus.consensus_numbers:
        console.print("[yellow]No consensus — agents didn't provide parseable picks.[/yellow]")
        return

    console.print(f"[bold yellow]CONSENSUS PICKS: {consensus.consensus_numbers}[/bold yellow]")
    if consensus.consensus_bonus:
        console.print(f"[bold cyan]CONSENSUS BONUS: {consensus.consensus_bonus}[/bold cyan]")

    # Convergence
    if consensus.convergence_numbers:
        console.print(f"\n[bold]Convergence (2+ agents agree):[/bold]")
        for num, voters in consensus.convergence_numbers:
            console.print(f"  #{num}: picked by {', '.join(voters)}")

    # All agent picks
    console.print(f"\n[bold]All Picks:[/bold]")
    for agent_id, pick_data in consensus.agent_picks.items():
        emoji = pick_data.get("emoji", "")
        name = pick_data.get("agent_name", agent_id)
        nums = pick_data.get("numbers", [])
        bonus = pick_data.get("bonus", [])
        console.print(f"  {emoji} {name}: [yellow]{nums}[/yellow]" +
                      (f" + [cyan]{bonus}[/cyan]" if bonus else ""))

    # Unique picks (dissent)
    if consensus.unique_picks:
        console.print(f"\n[bold]Unique Picks (only one agent):[/bold]")
        for agent_id, nums in consensus.unique_picks.items():
            console.print(f"  {agent_id}: {nums}")


def cmd_agents(args):
    """List all available agents."""
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import list_agents

    table = Table(title="Available Agents")
    table.add_column("", width=3)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Perspective")

    for agent in list_agents():
        table.add_row(agent.emoji, agent.agent_id, agent.agent_name, agent.perspective)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(prog="cointoss", description="CoinToss — Multi-Agent Lottery Analysis Engine")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    sub = parser.add_subparsers(dest="command")

    # init
    sub.add_parser("init", help="Initialise database")

    # import-us
    p_us = sub.add_parser("import-us", help="Import US lottery data")
    p_us.add_argument("--lottery", choices=["powerball_us", "mega_millions", "cash4life"])
    p_us.add_argument("--since", help="Import only since date (YYYY-MM-DD)")

    # import-au
    p_au = sub.add_parser("import-au", help="Import Australian lottery data")
    p_au.add_argument("--lottery", choices=["oz_lotto", "powerball_au", "saturday_lotto", "mon_wed_lotto", "set_for_life"])
    p_au.add_argument("--csv", help="Path to CSV file for bulk import")

    # import-lotto-america
    p_la = sub.add_parser("import-lotto-america", help="Import Lotto America data")
    p_la.add_argument("--since", help="Import only since date (YYYY-MM-DD)")

    # celestial
    p_cel = sub.add_parser("celestial", help="Populate celestial data")
    p_cel.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    p_cel.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")

    # validate
    sub.add_parser("validate", help="Validate imported data")

    # stats
    p_stats = sub.add_parser("stats", help="Show lottery data summary")
    p_stats.add_argument("--country", choices=["AU", "US"], help="Filter by country")

    # frequency
    p_freq = sub.add_parser("frequency", help="Show number frequency")
    p_freq.add_argument("lottery", help="Lottery ID (e.g. powerball_us)")
    p_freq.add_argument("--last", type=int, help="Only consider last N draws")

    # agents
    sub.add_parser("agents", help="List all available agents")

    # analyse
    p_analyse = sub.add_parser("analyse", help="Run single agent analysis")
    p_analyse.add_argument("lottery", help="Lottery ID (e.g. powerball_us)")
    p_analyse.add_argument("--agent", help="Specific agent ID (default: all agents)")
    p_analyse.add_argument("--date", help="Target date (YYYY-MM-DD, default: today)")

    # predict — quick all-agent prediction with consensus
    p_predict = sub.add_parser("predict", help="Quick prediction — all agents pick with consensus")
    p_predict.add_argument("lottery", help="Lottery ID")
    p_predict.add_argument("--date", help="Target date (YYYY-MM-DD)")

    # debate — full multi-agent debate with synthesis
    p_debate = sub.add_parser("debate", help="Full multi-agent debate with synthesis")
    p_debate.add_argument("lottery", help="Lottery ID")
    p_debate.add_argument("--agents", help="Comma-separated agent IDs (default: all)")
    p_debate.add_argument("--rounds", type=int, default=1, help="Number of challenge/defense rounds (1-3)")
    p_debate.add_argument("--date", help="Target date (YYYY-MM-DD)")

    # post-draw — explain why numbers came up
    p_post = sub.add_parser("post-draw", help="Post-draw analysis — agents explain the results")
    p_post.add_argument("lottery", help="Lottery ID")
    p_post.add_argument("--date", required=True, help="Draw date to analyse (YYYY-MM-DD)")

    # score — score predictions against results
    p_score = sub.add_parser("score", help="Score predictions against actual results")
    p_score.add_argument("--lottery", help="Filter by lottery ID")

    # leaderboard
    p_lb = sub.add_parser("leaderboard", help="Show agent leaderboard")
    p_lb.add_argument("--lottery", help="Filter by lottery ID")

    # told-you-so
    p_tys = sub.add_parser("told-you-so", help="Show predictions with 3+ hits")
    p_tys.add_argument("--lottery", help="Filter by lottery ID")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    commands = {
        "init": cmd_init,
        "import-us": cmd_import_us,
        "import-au": cmd_import_au,
        "import-lotto-america": cmd_import_lotto_america,
        "celestial": cmd_celestial,
        "validate": cmd_validate,
        "stats": cmd_stats,
        "frequency": cmd_frequency,
        "agents": cmd_agents,
        "analyse": cmd_analyse,
        "predict": cmd_predict,
        "debate": cmd_debate,
        "post-draw": cmd_post_draw,
        "score": cmd_score,
        "leaderboard": cmd_leaderboard,
        "told-you-so": cmd_told_you_so,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
