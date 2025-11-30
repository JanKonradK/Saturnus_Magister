"""
Search and manually link jobs - For retroactive linking.
"""

import asyncio
from rich.console import Console
from rich.prompt import Prompt

from src.db.repository import DatabaseRepository
from src.config import settings

console = Console()


async def main():
    """Search for emails and jobs to manually link."""
    console.print("\n[bold cyan]Job Search & Manual Linking[/bold cyan]\n")
    console.print("[dim]Coming soon...[/dim]\n")

    # TODO: Implement search functionality
    # - Search emails by company/subject
    # - Search jobs by company/position
    # - Create manual links


if __name__ == "__main__":
    asyncio.run(main())
