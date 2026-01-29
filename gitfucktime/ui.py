import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint
from .core import get_repo_stats

try:
    import questionary
    QUESTIONARY_INSTALLED = True
except ImportError:
    QUESTIONARY_INSTALLED = False

def interactive_mode():
    '''Runs the interactive dashboard.'''
    console = Console()
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

    console.print("\n")
    console.print(Panel(grid, title="[bold magenta]Git Fuck Time Dashboard[/bold magenta]", border_style="magenta"))
    # Added vertical spacing as requested
    console.print("\n") 

    if not QUESTIONARY_INSTALLED:
        # Fallback to rich prompt if questionary is missing
        rprint("[bold]Select an action:[/bold]")
        rprint("  • [cyan]Auto-Spread Unpushed[/cyan] (Detects parent date automatically)")
        rprint("  • [cyan]Custom Range[/cyan] (Enter start/end dates manually)")
        rprint("  • [red]Quit[/red]")
        
        choice = Prompt.ask("\n[bold]>[/bold]", choices=["auto", "custom", "quit", "a", "c", "q"], default="auto")
        
        if choice in ["quit", "q"]:
            console.print("[red]Exiting...[/red]")
            sys.exit(0)
        elif choice in ["auto", "a"]:
            return "unpushed"
        elif choice in ["custom", "c"]:
            return "custom"
            
    else:
        # Use Questionary for arrow key selection
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Auto-Spread Unpushed Commits",
                "Custom Date Range",
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
