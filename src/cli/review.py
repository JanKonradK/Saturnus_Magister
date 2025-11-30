"""
Manual review TUI - Review and resolve emails in the manual review queue.
"""

import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from src.db.repository import DatabaseRepository
from src.services.job_linker import JobLinker
from src.ai.job_matcher import JobMatcher
from src.config import settings

console = Console()


async def main():
    """Interactive manual review queue."""
    console.print("\n[bold cyan]Saturnus_Magister - Manual Review Queue[/bold cyan]\n")

    # Initialize database
    db = DatabaseRepository(settings.database_url)
    await db.initialize()

    matcher = JobMatcher(db)
    linker = JobLinker(db, matcher)

    try:
        while True:
            # Get pending reviews
            reviews = await db.get_pending_reviews(limit=10)

            if not reviews:
                console.print("[green]✓ No pending reviews![/green]\n")
                break

            # Display queue
            table = Table(title=f"Pending Reviews ({len(reviews)})")
            table.add_column("#", style="dim")
            table.add_column("Reason", style="yellow")
            table.add_column("Priority", style="cyan")
            table.add_column("Created", style="dim")

            for i, review in enumerate(reviews, 1):
                table.add_row(
                    str(i),
                    review.reason,
                    str(review.priority),
                    review.created_at.strftime("%Y-%m-%d %H:%M") if review.created_at else "Unknown"
                )

            console.print(table)

            # Select review
            choice = Prompt.ask("\nSelect review to process (or 'q' to quit)", default="1")

            if choice.lower() == 'q':
                break

            try:
                idx = int(choice) - 1
                if idx < 0 or idx >= len(reviews):
                    console.print("[red]Invalid selection[/red]")
                    continue
            except ValueError:
                console.print("[red]Invalid selection[/red]")
                continue

            review = reviews[idx]

            # Get email details
            email = await db.get_email_by_gmail_id(
                (await db.pool.fetchval("SELECT gmail_id FROM emails WHERE id = $1", review.email_id))
            )

            if not email:
                console.print("[red]Error: Email not found[/red]")
                continue

            # Display email
            console.print(Panel(
                f"[bold]Subject:[/bold] {email.subject}\n"
                f"[bold]From:[/bold] {email.sender_email}\n"
                f"[bold]Date:[/bold] {email.received_at}\n"
                f"[bold]Category:[/bold] {email.category}\n"
                f"[bold]Sentiment:[/bold] {email.sentiment}\n\n"
                f"[dim]{(email.body_text or '')[:500]}...[/dim]",
                title="Email Details",
                expand=False
            ))

            # Get match candidates
            candidates = await linker.get_match_candidates(email, limit=5)

            if candidates:
                console.print("\n[bold]Potential Matches:[/bold]\n")
                for i, candidate in enumerate(candidates, 1):
                    console.print(
                        f"  {i}. {candidate.company_name} - {candidate.position_title}\n"
                        f"     Score: {candidate.match_score:.2f} | "
                        f"Applied: {candidate.application_date.strftime('%Y-%m-%d') if candidate.application_date else 'Unknown'}"
                    )
            else:
                console.print("\n[yellow]No match candidates found[/yellow]")

            # Action menu
            console.print("\n[bold]Actions:[/bold]")
            console.print("  1-9: Link to candidate #")
            console.print("  n: No job link (not related to any application)")
            console.print("  s: Skip for now")

            action = Prompt.ask("\nChoose action", default="s")

            if action.lower() == 's':
                continue
            elif action.lower() == 'n':
                notes = Prompt.ask("Notes (optional)", default="")
                await linker.reject_match(email.id, reviewer_notes=notes)
                console.print("[green]✓ Marked as no job link[/green]")
            else:
                try:
                    candidate_idx = int(action) - 1
                    if 0 <= candidate_idx < len(candidates):
                        candidate = candidates[candidate_idx]
                        notes = Prompt.ask("Notes (optional)", default="")
                        await linker.manual_link(
                            email.id,
                            candidate.job_id,
                            reviewer_notes=notes
                        )
                        console.print(f"[green]✓ Linked to {candidate.company_name}[/green]")
                    else:
                        console.print("[red]Invalid candidate number[/red]")
                except ValueError:
                    console.print("[red]Invalid action[/red]")

            console.print()

    finally:
        await db.close()

    console.print("[bold green]Review session complete![/bold green]\n")


if __name__ == "__main__":
    asyncio.run(main())
