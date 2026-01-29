import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt
from rich import print as rprint
from .core import get_repo_stats
from pypager.source import GeneratorSource
from pypager.pager import Pager
from prompt_toolkit.formatted_text import ANSI, to_formatted_text

try:
    import questionary
    QUESTIONARY_INSTALLED = True
except ImportError:
    QUESTIONARY_INSTALLED = False

# Initialize console at module level
console = Console()

def display_commit_history(commits):
    '''Displays a rich table of commit history.'''
    if not commits:
        console.print("[yellow]No commits found.[/yellow]")
        return

    # Use ROUNDED box style for pretty output
    table = Table(title="Git Commit History", show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("Hash", style="cyan", no_wrap=True)
    table.add_column("Date", style="green")
    table.add_column("Relative", style="blue")
    table.add_column("Author", style="yellow")
    table.add_column("Message", style="white")

    for commit in commits:
        table.add_row(
            commit['hash'][:7],
            commit['date'],
            commit['relative_date'],
            commit['author'],
            commit['message']
        )

    # Use pypager for rendering
    # Capture rich output to generator
    def generate_content():
        with console.capture() as capture:
            console.print(table)
        # Convert ANSI object to formatted text list (list of tuples) for pypager
        yield to_formatted_text(ANSI(capture.get()))

    p = Pager()
    p.add_source(GeneratorSource(generate_content()))
    p.run()


def interactive_mode():
    '''Runs the interactive dashboard.'''
    stats = get_repo_stats()

    # Create Dashboard
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="center", ratio=1)
    
    # Add stats to grid
    grid.add_row(
        Panel(f"[bold green]{stats['unpushed_commits']}[/bold green]", title="Unpushed Commits", border_style="green"),
        Panel(f"[bold cyan]{stats['last_pushed_commit']}[/bold cyan]", title="Last Pushed Commit", border_style="cyan"),
        Panel(f"[bold blue]{stats['total_commits']}[/bold blue]", title="Total Commits", border_style="blue"),
        Panel(f"[bold yellow]{stats['last_commit']}[/bold yellow]", title="Last Commit", border_style="yellow")
    )
    
    console.print(grid)
    console.print("\n")

    if not QUESTIONARY_INSTALLED:
        # Fallback to rich prompt if questionary is missing
        rprint("[bold]Select an action:[/bold]")
        rprint("  • [cyan]Auto-Spread Unpushed[/cyan] (Detects parent date automatically)")
        rprint("  • [cyan]Custom Range[/cyan] (Enter start/end dates manually)")
        rprint("  • [magenta]View Commit History[/magenta] (See current commits)")
        rprint("  • [yellow]Revert Last Operation[/yellow] (Undo last rewrite)")
        rprint("  • [red]Quit[/red]")
        
        choice = Prompt.ask("\n[bold]>[/bold]", choices=["auto", "custom", "view", "revert", "quit", "a", "c", "v", "r", "q"], default="auto")
        
        if choice in ["quit", "q"]:
            console.print("[red]Exiting...[/red]")
            sys.exit(0)
        elif choice in ["auto", "a"]:
            return "unpushed"
        elif choice in ["custom", "c"]:
            return "custom"
        elif choice in ["view", "v"]:
            return "view"
        elif choice in ["revert", "r"]:
            return "revert"
            
    else:
        # Use Questionary for arrow key selection
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Auto-Spread Unpushed Commits",
                "Custom Date Range",
                "View Commit History",
                "Revert Last Operation",
                "Quit"
            ],
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       
                ('question', 'bold'),               
                ('answer', 'fg:#f44336 bold'),      
                ('pointer', 'fg:#673ab7 bold'),     
                ('highlighted', 'fg:#673ab7 bold'), 
                ('selected', 'fg:#cc5454'),         
                ('separator', 'fg:#cc5454'),        
                ('instruction', ''),                
                ('text', ''),                       
                ('disabled', 'fg:#858585 italic')   
            ])
        ).ask()

        if choice == "Quit" or choice is None:
            console.print("[red]Exiting...[/red]")
            sys.exit(0)
        elif choice == "Auto-Spread Unpushed Commits":
            return "unpushed"
        elif choice == "Custom Date Range":
            return "custom"
        elif choice == "View Commit History":
            return "view"
        elif choice == "Revert Last Operation":
            return "revert"
