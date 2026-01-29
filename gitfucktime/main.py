import sys
import os
import argparse
import datetime
import subprocess
from .core import get_commits, get_commit_date, generate_filter_script, run_filter_branch, get_commit_history, revert_last_operation, create_backup_branch, check_branch_divergence
from .utils import get_next_work_day, generate_work_hours_timestamp, DATE_FORMAT, TIME_FORMAT
from .ui import interactive_mode, display_commit_history

try:
    from rich.console import Console
    from rich.prompt import Confirm, Prompt
    from rich import print as rprint
    RICH_INSTALLED = True
    console = Console()
except ImportError:
    RICH_INSTALLED = False
    console = None

try:
    import questionary
    QUESTIONARY_INSTALLED = True
except ImportError:
    QUESTIONARY_INSTALLED = False

def print_info(msg):
    if RICH_INSTALLED:
        console.print(f"[bold cyan]INFO[/] {msg}")
    else:
        print(f"INFO: {msg}")

def print_success(msg):
    if RICH_INSTALLED:
        console.print(f"[bold green]SUCCESS[/] {msg}")
    else:
        print(f"SUCCESS: {msg}")

def print_warning(msg):
    if RICH_INSTALLED:
        console.print(f"[bold yellow]WARNING[/] {msg}")
    else:
        print(f"WARNING: {msg}")

def print_error(msg):
    if RICH_INSTALLED:
        console.print(f"[bold red]ERROR[/] {msg}")
    else:
        print(f"ERROR: {msg}")

def confirm_action(message):
    '''Prompts user to confirm a potentially risky action.'''
    if QUESTIONARY_INSTALLED:
        return questionary.confirm(message, default=False).ask()
    elif RICH_INSTALLED:
        return Confirm.ask(message, default=False)
    else:
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']

def main():
    parser = argparse.ArgumentParser(
        description="Rewrite git commit dates to spread them over a time frame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Rewrite all commits between Dec 6-17, 2025
  gitfucktime --start 2025-12-06 --end 2025-12-17

  # Only rewrite unpushed commits
  gitfucktime --start 2025-12-06 --end 2025-12-17 --unpushed

  # Rewrite last 16 commits (from HEAD going back)
  gitfucktime --start 2025-12-06 --end 2025-12-17 --last 16

  # Rewrite oldest 10 commits (from past going forward)
  gitfucktime --start 2025-12-06 --end 2025-12-17 --first 10
  
  # View commit history
  gitfucktime --view
  
  # Revert last operation
  gitfucktime --revert
        '''
    )

    parser.add_argument("-s", "--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("-e", "--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("-u", "--unpushed", action="store_true",
                        help="Only rewrite commits not pushed to origin/master")
    parser.add_argument("-l", "--last", type=int, metavar="N",
                        help="Only rewrite last N commits (from HEAD going back)")
    parser.add_argument("-f", "--first", type=int, metavar="N",
                        help="Only rewrite first N commits (from oldest going forward)")
    parser.add_argument("-V", "--view", action="store_true",
                        help="View git commit history and exit")
    parser.add_argument("--revert", action="store_true",
                        help="Revert the last gitfucktime operation")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip creating a backup branch before operation")
    parser.add_argument("-v", "--version", action="version", version="gitfucktime 1.1.0",
                        help="Show program's version number and exit")

    args = parser.parse_args()

    # Handle View History
    if args.view:
        if not RICH_INSTALLED:
            print("Error: The --view feature requires 'rich'. Please install it: pip install rich")
            return
        
        history = get_commit_history()
        display_commit_history(history)
        return

    # Handle Revert
    if args.revert:
        print_info("Attempting to revert last operation...")
        result = revert_last_operation(no_backup=args.no_backup)
        if result['success']:
            print_success(result['message'])
            if result.get('backup'):
                print_info(f"Backup created at: {result['backup']}")
        else:
            print_error(result['message'])
        return

    # Interactive Mode Trigger
    if not any(vars(args).values()):  # No arguments provided
        if RICH_INSTALLED:
            while True:  # Loop for interactive menu
                mode = interactive_mode()
                if mode == "unpushed":
                    args.unpushed = True
                    break
                elif mode == "custom":
                    # Ask for inputs
                    if QUESTIONARY_INSTALLED:
                        args.start = questionary.text("Enter start date (YYYY-MM-DD):").ask()
                        args.end = questionary.text("Enter end date (YYYY-MM-DD, optional):").ask()
                    else:
                        start_str = Prompt.ask("Enter start date [dim](YYYY-MM-DD)[/dim]")
                        end_str = Prompt.ask("Enter end date [dim](YYYY-MM-DD, optional)[/dim]", default="")
                        args.start = start_str
                        if end_str:
                            args.end = end_str
                    break
                elif mode == "view":
                    history = get_commit_history()
                    display_commit_history(history)
                    # Loop continues to show menu again
                elif mode == "revert":
                    print_info("Attempting to revert last operation...")
                    if not confirm_action("Are you sure you want to revert the last rewriting operation?"):
                         continue
                         
                    # Ask about backup
                    no_backup = not confirm_action("Create a backup branch before reverting?")
                    
                    result = revert_last_operation(no_backup=no_backup)
                    if result['success']:
                        print_success(result['message'])
                        if result.get('backup'):
                            print_info(f"Backup created at: {result['backup']}")
                    else:
                        print_error(result['message'])
                    
                    input("\nPress Enter to continue...")
                elif mode is None: # Quit
                     return
        else:
             print("Install 'rich' for interactive mode: pip install rich")
             parser.print_help()
             return

    if RICH_INSTALLED:
        console.rule("[bold magenta]Git Fuck Time[/bold magenta]")
        console.print("[dim]Spreading your commits over time...[/dim]\n")
        console.print("[yellow]WARNING: This rewrites history. Make sure you have a backup.[/yellow]\n")
    else:
        print("\n=== Git Fuck Time ===")
        print("WARNING: This rewrites history. Make sure you have a backup.\n")

    # Identifiy commits to process
    if RICH_INSTALLED:
        status_ctx = console.status("[bold green]Fetching commits...[/bold green]", spinner="dots")
        status_ctx.start()
    else:
        print("Fetching commits...")
        status_ctx = None
    
    revision_range_start = None

    try:
        if args.last:
            commits = get_commits(count=args.last, unpushed_only=args.unpushed, reverse_order=True)
            if status_ctx: status_ctx.stop()
            print_info(f"Found {len(commits)} commits (last {args.last} from HEAD).")
            try:
                revision_range_start = subprocess.check_output(["git", "rev-parse", f"HEAD~{args.last}"]).decode('utf-8').strip()
            except:
                pass
        elif args.first:
            all_commits = get_commits(unpushed_only=args.unpushed, reverse_order=True)
            commits = all_commits[:args.first] if len(all_commits) >= args.first else all_commits
            if status_ctx: status_ctx.stop()
            print_info(f"Found {len(commits)} commits (first {args.first} from oldest).")
            try:
                revision_range_start = subprocess.check_output(["git", "rev-parse", f"{commits[0]}~1"]).decode('utf-8').strip()
            except:
                revision_range_start = None
        else:
            # Default or Unpushed
            commits = get_commits(unpushed_only=args.unpushed, reverse_order=True)
            if status_ctx: status_ctx.stop()
            scope = "unpushed " if args.unpushed else ""
            print_info(f"Found {len(commits)} {scope}commits.")
            
            if args.unpushed:
                # Parent is origin/master
                try:
                    revision_range_start = subprocess.check_output(["git", "merge-base", "origin/master", "HEAD"]).decode('utf-8').strip()
                except:
                    print_warning("Could not determine merge base with origin/master.")
    except Exception as e:
        if status_ctx: status_ctx.stop()
        print_error(f"Failed to fetch commits: {e}")
        return

    if len(commits) == 0:
        print_warning("No commits to process.")
        return

    # Determine dates
    start_date = None
    end_date = None

    if args.start:
        try:
            start_date = datetime.datetime.strptime(args.start, DATE_FORMAT)
        except ValueError:
            print_error(f"Invalid start date format (expected {DATE_FORMAT}).")
            return
    
    if args.end:
        try:
             end_date = datetime.datetime.strptime(args.end, DATE_FORMAT)
             end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            print_error(f"Invalid end date format (expected {DATE_FORMAT}).")
            return

    # Auto-detect start date if not provided
    if not start_date:
        if revision_range_start:
            print_info(f"Auto-detecting start date based on parent commit: {revision_range_start[:7]}")
            parent_date = get_commit_date(revision_range_start)
            if parent_date:
                start_date = get_next_work_day(parent_date)
                if RICH_INSTALLED:
                    console.print(f"  Parent Date: [cyan]{parent_date.strftime(DATE_FORMAT)}[/cyan]")
                    console.print(f"  Start Date:  [green]{start_date.strftime(DATE_FORMAT)}[/green] (Next Work Day)")
                else:
                    print(f"  Parent Date: {parent_date.strftime(DATE_FORMAT)}")
                    print(f"  Start Date:  {start_date.strftime(DATE_FORMAT)} (Next Work Day)")
            else:
                print_warning("Could not get parent commit date. Fallback to today.")
                start_date = datetime.datetime.now()
        else:
            # Fallback if no parent 
            if not args.start:
                 print_info("No start date specified and could not deduce from context.")
                 try:
                    if RICH_INSTALLED:
                        start_str = Prompt.ask("Enter start date [dim](YYYY-MM-DD)[/dim]")
                    else:
                        start_str = input("Enter start date (YYYY-MM-DD): ").strip()
                    start_date = datetime.datetime.strptime(start_str, DATE_FORMAT)
                 except:
                    return

    # Auto-detect end date if not provided
    if not end_date:
        days_needed = len(commits)
        end_date = start_date + datetime.timedelta(days=max(1, days_needed - 1)) 
        end_date = end_date.replace(hour=23, minute=59, second=59)
        print_info(f"Auto-calculated End Date: {end_date.strftime(DATE_FORMAT)} ({days_needed} commits over {days_needed} days)")

    if start_date > end_date:
        print_error("Start date must be before end date.")
        return

    if args.last and args.first:
        print_error("Cannot use both --last and --first flags.")
        return

    if len(commits) == 0:
        print_warning("No commits to process.")
        return

    # Get current time for validation
    now = datetime.datetime.now()
    
    # Check for future dates
    if end_date > now:
        # If user explicitly provided end date or interactive custom input
        if args.end or (not args.unpushed and not args.last and not args.first):
            print_warning(f"End date ({end_date.strftime(DATE_FORMAT)}) is in the future.")
            print_info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            if not confirm_action("Do you really want to create commits in the future?"):
                print("Operation cancelled.")
                return
        else:
            # Auto-calculated: cap at now
            print_info("Auto-calculated end date was in the future. Capping at current time.")
            end_date = now
            if start_date > end_date:
                print_error("Start date is after current time. Cannot proceed.")
                return
    
    # Check if start date is before parent commit
    if revision_range_start:
        parent_date = get_commit_date(revision_range_start)
        if parent_date and start_date < parent_date:
            print_warning(f"Start date ({start_date.strftime(DATE_FORMAT)}) is before the parent commit date ({parent_date.strftime('%Y-%m-%d %H:%M:%S')}).")
            print_warning("This may create a messy or confusing git history.")
            if not confirm_action("Do you really want to proceed?"):
                print("Operation cancelled.")
                return

    # Check for branch divergence
    divergence = check_branch_divergence()
    if divergence:
        ahead = divergence['ahead']
        behind = divergence['behind']
        if ahead > 50 or behind > 50:
            print_warning("Branch significantly diverged from origin/master!")
            print_info(f"  - Ahead by: {ahead} commits")
            print_info(f"  - Behind by: {behind} commits")
            print_warning("Rewriting history on a diverged branch can cause conflicts.")
            if not confirm_action("Are you sure you want to continue?"):
                print("Operation cancelled.")
                return

    if RICH_INSTALLED:
        status_gen = console.status("[bold green]Generating timestamps...[/bold green]", spinner="dots")
        status_gen.start()
    else:
        print("Generating timestamps...")
        status_gen = None

    timestamps = []
    for _ in range(len(commits)):
        timestamps.append(generate_work_hours_timestamp(start_date, end_date, max_time=now))

    timestamps.sort()

    # Create mapping: commits are in oldest->newest order (after reverse)
    # Timestamps are in earliest->latest order (after sort)
    # Direct assignment gives oldest commit -> earliest timestamp
    mapping = {}
    for i, commit in enumerate(commits):
        mapping[commit] = timestamps[i].strftime(TIME_FORMAT)

    if status_gen: status_gen.stop()

    # Generate filter script
    filter_script = generate_filter_script(mapping)

    # Write the filter script with absolute path
    filter_file = os.path.abspath(".git_date_filter.sh")
    with open(filter_file, "w", newline='\n') as f:
        f.write(filter_script)

    print_success(f"Filter script created: {filter_file}")
    
    # BACKUP CREATION
    if not args.no_backup:
        print_info("Creating backup branch...")
        backup_branch = create_backup_branch()
        if backup_branch:
             print_success(f"Backup created: {backup_branch}")
        else:
             print_error("Failed to create backup branch. Continuing...")
    else:
        print_warning("Skipping backup creation (as requested).")
    
    print_info("Refactoring git history... this might take a moment.")
    # Run filter branch
    run_filter_branch(commits, filter_file, args, revision_range_start)
    
    # Cleanup
    if os.path.exists(filter_file):
        os.remove(filter_file)
        if RICH_INSTALLED:
            console.print("[dim]Cleaned up filter script[/dim]")
        else:
            print(f"Cleaned up filter script")

if __name__ == "__main__":
    main()
