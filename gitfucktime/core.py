import subprocess
import datetime
import os
from .utils import TIME_FORMAT

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

def get_repo_stats():
    '''Gathers stats for the interactive dashboard.'''
    stats = {}
    
    # Total commits
    try:
        stats['total_commits'] = int(subprocess.check_output(["git", "rev-list", "--count", "HEAD"]).decode("utf-8").strip())
    except:
        stats['total_commits'] = 0

    # Unpushed commits
    try:
        stats['unpushed_commits'] = int(subprocess.check_output(["git", "rev-list", "--count", "origin/master..HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip())
    except:
        stats['unpushed_commits'] = 0

    # Last commit info
    try:
        last_commit_date = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short", "HEAD"]).decode("utf-8").strip()
        last_commit_hash = subprocess.check_output(["git", "show", "-s", "--format=%h", "HEAD"]).decode("utf-8").strip()
        stats['last_commit'] = f"{last_commit_hash} ({last_commit_date})"
    except:
        stats['last_commit'] = "Unknown"
    
    # Last pushed commit (before unpushed)
    try:
        # Get the merge base with origin/master (last commit that was pushed)
        last_pushed_hash = subprocess.check_output(["git", "merge-base", "origin/master", "HEAD"], stderr=subprocess.DEVNULL).decode("utf-8").strip()
        last_pushed_date = subprocess.check_output(["git", "show", "-s", "--format=%cd", "--date=short", last_pushed_hash]).decode("utf-8").strip()
        last_pushed_short_hash = subprocess.check_output(["git", "show", "-s", "--format=%h", last_pushed_hash]).decode("utf-8").strip()
        stats['last_pushed_commit'] = f"{last_pushed_short_hash} ({last_pushed_date})"
    except:
        stats['last_pushed_commit'] = "N/A"
        
    return stats

def generate_filter_script(mapping):
    '''Generates the content of the git filter-branch script.'''
    filter_script = "#!/bin/sh\ncase ${GIT_COMMIT} in\n"
    for commit_hash, new_date in mapping.items():
        filter_script += f'{commit_hash})\n'
        filter_script += f'  export GIT_AUTHOR_DATE="{new_date}"\n'
        filter_script += f'  export GIT_COMMITTER_DATE="{new_date}"\n'
        filter_script += '  ;;\n'
    filter_script += 'esac\n'
    return filter_script

def run_filter_branch(commits, filter_file, args, revision_range_start=None):
    '''Executes the git filter-branch command.'''
    # Set environment variable to suppress warning
    os.environ["FILTER_BRANCH_SQUELCH_WARNING"] = "1"

    print("\nRunning git filter-branch...")
    print(f"This will rewrite {len(commits)} commits")

    try:
        # Use absolute path and proper quoting for Windows
        filter_path = filter_file.replace("\\", "/")
        
        # Determine revision range
        if args.last:
            revision_range = f"HEAD~{args.last}..HEAD"
        elif args.unpushed and revision_range_start:
            # Only rewrite commits after the merge-base (unpushed commits)
            revision_range = f"{revision_range_start}..HEAD"
        elif args.first and revision_range_start:
            # Only rewrite from first commit's parent to HEAD
            revision_range = f"{revision_range_start}..HEAD"
        else:
            revision_range = "HEAD"
            
        cmd = f'git filter-branch --env-filter ". {filter_path}" --force {revision_range}'
        print(f"Command: {cmd}")
        subprocess.check_call(cmd, shell=True)
        print("\nSuccess! History rewritten.")
        
        # Only warn about force push if we potentially rewrote pushed commits
        if not args.unpushed:
            print("Don't forget to force push: git push --force origin <branch>")
        else:
            print("These were unpushed commits - no force push needed, just git push normally.")
            
    except subprocess.CalledProcessError as e:
        print(f"\nError running git filter-branch: {e}")


