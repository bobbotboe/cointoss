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
    """Run a debate between two agents."""
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import build_context, get_agent

    init_db()
    session = get_session()
    target = date.fromisoformat(args.date) if args.date else None
    ctx = build_context(session, args.lottery, target_date=target)

    agent_a = get_agent(args.agent_a)
    agent_b = get_agent(args.agent_b)

    console.print(f"[bold]{agent_a.emoji} {agent_a.agent_name} vs {agent_b.emoji} {agent_b.agent_name}[/bold]\n")

    # Round 1: Both analyse
    console.print(f"[bold cyan]═══ Round 1: Opening Analyses ═══[/bold cyan]\n")

    console.print(f"[bold]{agent_a.emoji} {agent_a.agent_name}:[/bold]")
    result_a = agent_a.predict(ctx)
    console.print(result_a.analysis)
    console.print()

    console.print(f"[bold]{agent_b.emoji} {agent_b.agent_name}:[/bold]")
    result_b = agent_b.predict(ctx)
    console.print(result_b.analysis)
    console.print()

    # Round 2: Challenge each other
    console.print(f"[bold cyan]═══ Round 2: Challenges ═══[/bold cyan]\n")

    console.print(f"[bold]{agent_a.emoji} {agent_a.agent_name} challenges {agent_b.agent_name}:[/bold]")
    challenge_a = agent_a.challenge(result_b, ctx)
    console.print(challenge_a)
    console.print()

    console.print(f"[bold]{agent_b.emoji} {agent_b.agent_name} challenges {agent_a.agent_name}:[/bold]")
    challenge_b = agent_b.challenge(result_a, ctx)
    console.print(challenge_b)
    console.print()

    # Round 3: Defend
    console.print(f"[bold cyan]═══ Round 3: Defenses ═══[/bold cyan]\n")

    console.print(f"[bold]{agent_a.emoji} {agent_a.agent_name} defends:[/bold]")
    defense_a = agent_a.defend(challenge_b, result_a.analysis)
    console.print(defense_a)
    console.print()

    console.print(f"[bold]{agent_b.emoji} {agent_b.agent_name} defends:[/bold]")
    defense_b = agent_b.defend(challenge_a, result_b.analysis)
    console.print(defense_b)
    console.print()

    # Summary
    console.print(f"[bold cyan]═══ Final Picks ═══[/bold cyan]\n")
    for label, result in [(agent_a.agent_name, result_a), (agent_b.agent_name, result_b)]:
        if result.picks:
            console.print(f"  {label}: [yellow]{result.picks.numbers}[/yellow]" +
                          (f" + [cyan]{result.picks.bonus}[/cyan]" if result.picks.bonus else ""))

    session.close()


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
    p_analyse = sub.add_parser("analyse", help="Run agent analysis on a lottery")
    p_analyse.add_argument("lottery", help="Lottery ID (e.g. powerball_us)")
    p_analyse.add_argument("--agent", help="Specific agent ID (default: all agents)")
    p_analyse.add_argument("--date", help="Target date (YYYY-MM-DD, default: today)")

    # debate
    p_debate = sub.add_parser("debate", help="Run a debate between two agents")
    p_debate.add_argument("lottery", help="Lottery ID")
    p_debate.add_argument("agent_a", help="First agent ID")
    p_debate.add_argument("agent_b", help="Second agent ID")
    p_debate.add_argument("--date", help="Target date (YYYY-MM-DD)")

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
        "debate": cmd_debate,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
