"""
Saturnus_Magister - Main entry point
Orchestrates email monitoring, classification, and routing.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import NoReturn

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich import box

from src.services.email_processor import EmailProcessor
from src.config import settings

console = Console()

def print_banner():
    """Print the application banner."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Panel(
            "[bold cyan]Saturnus_Magister[/bold cyan]\n"
            "[dim]Autonomous Email Orchestration System[/dim]",
            style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)

def check_environment():
    """Verify environment setup."""
    # Check Python version
    if sys.version_info < (3, 14):
        console.print(f"[yellow]⚠️  Warning: Running Python {sys.version_info.major}.{sys.version_info.minor}[/yellow]")
        console.print("[dim]   Recommended: Python 3.14+ for best performance[/dim]")

    # Check free-threading
    if hasattr(sys, '_is_gil_enabled'):
        if not sys._is_gil_enabled():
            console.print("[green]✓ Free-threading enabled (GIL disabled)[/green]")
        else:
            console.print("[dim]ℹ️  GIL enabled - consider python3.14t for parallel processing[/dim]")

    # Verify critical settings
    if "example" in settings.agent_api_key or "your-key" in settings.agent_api_key:
        console.print("[bold red]❌ Error: AGENT_API_KEY not configured in .env[/bold red]")
        sys.exit(1)

async def main():
    """Main email processing loop."""
    print_banner()
    check_environment()

    console.print(f"\n[bold]Environment:[/bold] {settings.environment.value}")
    console.print(f"[bold]Poll Interval:[/bold] {settings.poll_interval_seconds}s")
    console.print(f"[bold]Database:[/bold] {settings.database_url.split('@')[1] if '@' in settings.database_url else 'configured'}")
    console.print("[dim]Press Ctrl+C to stop.[/dim]\n")

    # Initialize processor
    with console.status("[bold green]Initializing system...[/bold green]"):
        try:
            processor = EmailProcessor()
            await processor.initialize()
        except Exception as e:
            console.print(f"[bold red]❌ Initialization failed:[/bold red] {e}")
            return

    # Graceful shutdown handling
    stop_event = asyncio.Event()

    def signal_handler():
        console.print("\n[yellow]🛑 Shutdown requested...[/yellow]")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    # Main processing loop
    iteration = 0
    try:
        while not stop_event.is_set():
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')

            console.rule(f"[bold cyan]Iteration #{iteration}[/bold cyan] - {timestamp}")

            try:
                # Process emails
                stats = await processor.process_new_emails()

                # Sync TickTick tasks
                synced = await processor.sync_ticktick_tasks()

                # Summary table
                table = Table(show_header=True, header_style="bold magenta", box=box.SIMPLE)
                table.add_column("Metric", style="dim")
                table.add_column("Value", justify="right")

                table.add_row("Inbox Processed", str(stats['inbox_processed']))
                table.add_row("Sent Processed", str(stats['sent_processed']))
                table.add_row("Tasks Synced", str(synced))

                if stats['errors'] > 0:
                    table.add_row("Errors", f"[red]{stats['errors']}[/red]")

                console.print(table)

            except Exception as e:
                console.print(f"[bold red]❌ Error during processing:[/bold red] {e}")
                import traceback
                console.print(traceback.format_exc(), style="dim red")

            # Wait for next iteration or shutdown signal
            if not stop_event.is_set():
                with console.status(f"[dim]Sleeping for {settings.poll_interval_seconds}s...[/dim]"):
                    try:
                        await asyncio.wait_for(
                            stop_event.wait(),
                            timeout=settings.poll_interval_seconds
                        )
                    except asyncio.TimeoutError:
                        pass

    finally:
        with console.status("[bold red]Shutting down...[/bold red]"):
            await processor.shutdown()
        console.print("[bold green]✓ Shutdown complete.[/bold green]")


def cli():
    """CLI entry point."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    cli()
