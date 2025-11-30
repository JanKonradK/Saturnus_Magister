"""
TickTick setup helper - retrieves project IDs for Eisenhower matrix.
"""

import asyncio
import httpx
from rich.console import Console
from rich.table import Table

from src.config import settings

console = Console()


async def main():
    """Fetch and display TickTick projects for .env configuration."""
    console.print("\n[bold cyan]TickTick Project Setup[/bold cyan]\n")
    console.print("Fetching your TickTick projects...\n")

    headers = {
        "Authorization": f"Bearer {settings.ticktick_access_token}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.ticktick.com/open/v1/project",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            projects = response.json()

        # Display projects in a table
        table = Table(title="TickTick Projects")
        table.add_column("Project Name", style="cyan")
        table.add_column("Project ID", style="green")

        for project in projects:
            table.add_row(project.get("name", "Unknown"), project.get("id", ""))

        console.print(table)

        # Guide user
        console.print("\n[bold yellow]Configuration Instructions:[/bold yellow]\n")
        console.print("1. Find your Eisenhower Matrix projects:")
        console.print("   - Q1: Urgent + Important (Do First)")
        console.print("   - Q2: Not Urgent + Important (Schedule)")
        console.print("   - Q3: Urgent + Not Important (Delegate)")
        console.print("   - Q4: Not Urgent + Not Important (Eliminate)")
        console.print("\n2. Find your main 'Work' project\n")
        console.print("3. Copy the corresponding IDs to your .env file:\n")

        console.print("[dim]   TICKTICK_Q1_PROJECT=<Q1 project ID>")
        console.print("   TICKTICK_Q2_PROJECT=<Q2 project ID>")
        console.print("   TICKTICK_Q3_PROJECT=<Q3 project ID>")
        console.print("   TICKTICK_Q4_PROJECT=<Q4 project ID>")
        console.print("   TICKTICK_WORK_PROJECT=<Work project ID>[/dim]\n")

    except httpx.HTTPStatusError as e:
        console.print(f"[bold red]Error:[/bold red] HTTP {e.response.status_code}")
        console.print(f"Response: {e.response.text}")
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    asyncio.run(main())
