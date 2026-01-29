#!/usr/bin/env python3
import sys
import os
import subprocess
import datetime
import random
import json
import argparse

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

def get_commits(count=None, unpushed_only=False, reverse_order=False):
    '''Returns a list of commit hashes.'''
    if unpushed_only:
        try:
            result = subprocess.check_output(
                ["git", "rev-list", "origin/master..HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8")
        except subprocess.CalledProcessError:
            print("Warning: Could not find origin/master, using all commits on HEAD")
            result = subprocess.check_output(["git", "rev-list", "HEAD"]).decode("utf-8")
    else:
        result = subprocess.check_output(["git", "rev-list", "HEAD"]).decode("utf-8")

    commits = [line.strip() for line in result.splitlines() if line.strip()]

    if count:
        commits = commits[:count]

    if reverse_order:
        commits.reverse()

    return commits

def get_commit_date(commit_hash):
    '''Returns the datetime of a specific commit.'''
    try:
        timestamp = subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", commit_hash]
        ).decode("utf-8").strip()
        return datetime.datetime.fromtimestamp(int(timestamp))
    except (subprocess.CalledProcessError, ValueError):
        return None

def get_next_work_day(date):
    '''Returns the next work day (Mon-Fri) after the given date.'''
    next_day = date + datetime.timedelta(days=1)
    while not is_work_day(next_day):
        next_day += datetime.timedelta(days=1)
    return next_day

def is_work_day(date):
    '''Returns True if date is Monday-Friday.'''
    return date.weekday() < 5

def generate_work_hours_timestamp(start_date, end_date):
    '''Generates a random timestamp within work hours (09:00-17:00) on a work day.'''
    total_days = (end_date - start_date).days + 1

    while True:
        random_days = random.randint(0, total_days)
        target_date = start_date + datetime.timedelta(days=random_days)

        if is_work_day(target_date):
            hour = random.randint(9, 16)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            result = target_date.replace(hour=hour, minute=minute, second=second)
            return result

def main():
    parser = argparse.ArgumentParser(
        description="Rewrite git commit dates to spread them over a time frame",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Rewrite all commits between Dec 6-17, 2025
  python gitfucktime.py --start 2025-12-06 --end 2025-12-17

  # Only rewrite unpushed commits
  python gitfucktime.py --start 2025-12-06 --end 2025-12-17 --unpushed

  # Rewrite last 16 commits (from HEAD going back)
  python gitfucktime.py --start 2025-12-06 --end 2025-12-17 --last 16

  # Rewrite oldest 10 commits (from past going forward)
  python gitfucktime.py --start 2025-12-06 --end 2025-12-17 --first 10
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
    parser.add_argument("-v", "--version", action="version", version="gitfucktime 0.1.0",
                        help="Show program's version number and exit")

    args = parser.parse_args()

    print("=== Git Time Spreader (gitfucktime) ===")
    print("This script will rewrite your git history to spread commits over a time frame.")
    print("Work hours (09:00-17:00, Mon-Fri) will be used.")
    print("WARNING: This rewrites history. Make sure you have a backup.\n")

    # Identifiy commits to process
    print("\nFetching commits...")
    
    revision_range_start = None

    if args.last:
        commits = get_commits(count=args.last, unpushed_only=args.unpushed, reverse_order=True)
        print(f"Found {len(commits)} commits (last {args.last} from HEAD).")
        # Parent is HEAD~N
        try:
             revision_range_start = subprocess.check_output(["git", "rev-parse", f"HEAD~{args.last}"]).decode('utf-8').strip()
        except:
             pass
    elif args.first:
        all_commits = get_commits(unpushed_only=args.unpushed, reverse_order=True)
        commits = all_commits[:args.first] if len(all_commits) >= args.first else all_commits
        print(f"Found {len(commits)} commits (first {args.first} from oldest).")
        # Parent of the oldest commit in logic? If we are changing the very first commits, 
        # there might be no parent, or we look at the one before the first in this list.
        # But if 'first' implies the repo root, there is no parent. 
        # We will try to find the commit before the first one in our list.
        try:
            first_commit = commits[0] # commits are reverse ordered (oldest first)? existing get_commits sorts?
            # get_commits with reverse_order=True returns oldest first? 
            # Let's check get_commits implementation. 
            # Yes: commits.reverse() if reverse_order=True. 
            # The list from rev-list HEAD is usually newest first. 
            # So reverse_order=True means Oldest -> Newest.
            # So commits[0] is the oldest.
            # We need the parent of commits[0].
            revision_range_start = subprocess.check_output(["git", "rev-parse", f"{commits[0]}~1"]).decode('utf-8').strip()
        except:
            revision_range_start = None
    else:
        # Default or Unpushed
        commits = get_commits(unpushed_only=args.unpushed, reverse_order=True)
        scope = "unpushed " if args.unpushed else ""
        print(f"Found {len(commits)} {scope}commits.")
        
        if args.unpushed:
            # Parent is origin/master
            try:
                revision_range_start = subprocess.check_output(["git", "merge-base", "origin/master", "HEAD"]).decode('utf-8').strip()
            except:
                print("Warning: Could not determine merge base with origin/master.")
        else:
             # If just running without arguments and not unpushed, it takes ALL commits (per existing logic line 25/130).
             # It acts like --first ALL.
             pass

    if len(commits) == 0:
        print("No commits to process.")
        return

    # Determine dates
    start_date = None
    end_date = None

    if args.start:
        try:
            start_date = datetime.datetime.strptime(args.start, DATE_FORMAT)
        except ValueError:
            print(f"Error: Invalid start date format (expected {DATE_FORMAT}).")
            return
    
    if args.end:
        try:
             end_date = datetime.datetime.strptime(args.end, DATE_FORMAT)
             end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            print(f"Error: Invalid end date format (expected {DATE_FORMAT}).")
            return

    # Auto-detect start date if not provided
    if not start_date:
        if revision_range_start:
            print(f"Auto-detecting start date based on parent commit: {revision_range_start[:7]}")
            parent_date = get_commit_date(revision_range_start)
            if parent_date:
                start_date = get_next_work_day(parent_date)
                print(f"  Parent Date: {parent_date.strftime(DATE_FORMAT)}")
                print(f"  Start Date:  {start_date.strftime(DATE_FORMAT)} (Next Work Day)")
            else:
                print("  Could not get parent commit date. Fallback to today.")
                start_date = datetime.datetime.now()
        else:
            # Fallback if no parent (e.g. root commit or no logic found)
            if not args.start: # Only confirm if we really have no clue
                 print("No start date specified and could not deduce from context.")
                 # If interactive:
                 try:
                    start_str = input("Enter start date (YYYY-MM-DD): ").strip()
                    start_date = datetime.datetime.strptime(start_str, DATE_FORMAT)
                 except:
                    return

    # Auto-detect end date if not provided
    if not end_date:
        # Strategy: start_date + num_commits days
        days_needed = len(commits)
        # We want to roughly match 1 commit/day density as requested?
        # "amount of days=commits"
        end_date = start_date + datetime.timedelta(days=max(1, days_needed - 1)) # -1 because start counts as day 1
        end_date = end_date.replace(hour=23, minute=59, second=59)
        print(f"Auto-calculated End Date: {end_date.strftime(DATE_FORMAT)} ({days_needed} commits over {days_needed} days)")

    if start_date > end_date:
        print("Error: Start date must be before end date.")
        return

    if args.last and args.first:
        print("Error: Cannot use both --last and --first flags.")
        return

    # Commits already fetched above

    if len(commits) == 0:
        print("No commits to process.")
        return

    print("Generating timestamps...")
    timestamps = []
    for _ in range(len(commits)):
        timestamps.append(generate_work_hours_timestamp(start_date, end_date))

    timestamps.sort()

    # Create mapping
    mapping = {}
    for i, commit in enumerate(commits):
        mapping[commit] = timestamps[i].strftime(TIME_FORMAT)

    # Create a shell script for the env-filter
    # FIXED: Use full commit hash comparison
    filter_script = "#!/bin/sh\ncase ${GIT_COMMIT} in\n"
    for commit_hash, new_date in mapping.items():
        filter_script += f'{commit_hash})\n'
        filter_script += f'  export GIT_AUTHOR_DATE="{new_date}"\n'
        filter_script += f'  export GIT_COMMITTER_DATE="{new_date}"\n'
        filter_script += '  ;;\n'
    filter_script += 'esac\n'

    # Write the filter script with absolute path
    filter_file = os.path.abspath(".git_date_filter.sh")
    with open(filter_file, "w", newline='\n') as f:
        f.write(filter_script)

    print(f"Filter script created: {filter_file}")

    # Set environment variable to suppress warning
    os.environ["FILTER_BRANCH_SQUELCH_WARNING"] = "1"

    print("\nRunning git filter-branch...")
    print(f"This will rewrite {len(commits)} commits")

    try:
        # Use absolute path and proper quoting for Windows
        filter_path = filter_file.replace("\\", "/")
        
        # For last N commits, use HEAD~N..HEAD syntax
        if args.last:
            revision_range = f"HEAD~{args.last}..HEAD"
        elif args.first or args.unpushed:
            revision_range = "HEAD"
        else:
            revision_range = "HEAD"
            
        cmd = f'git filter-branch --env-filter ". {filter_path}" --force {revision_range}'
        print(f"Command: {cmd}")
        subprocess.check_call(cmd, shell=True)
        print("\nSuccess! History rewritten.")
        print("Don't forget to force push: git push --force origin <branch>")
    except subprocess.CalledProcessError as e:
        print(f"\nError running git filter-branch: {e}")
    finally:
        if os.path.exists(filter_file):
            os.remove(filter_file)
            print(f"Cleaned up filter script")

if __name__ == "__main__":
    main()
