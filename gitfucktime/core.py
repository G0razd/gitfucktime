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

def get_commit_history(count=None):
    '''Returns a list of commit details for history view.'''
    try:
        cmd = ["git", "log", "--pretty=format:%H|%cd|%cr|%an|%s", "--date=format:%Y-%m-%d %H:%M:%S"]
        if count:
            cmd.extend(["-n", str(count)])
            
        result = subprocess.check_output(cmd).decode("utf-8")
        
        history = []
        for line in result.splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) == 5:
                history.append({
                    "hash": parts[0],
                    "date": parts[1],
                    "relative_date": parts[2],
                    "author": parts[3],
                    "message": parts[4]
                })
        return history
    except subprocess.CalledProcessError:
        return []

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


def create_backup_branch():
    '''Creates a backup branch with timestamp'''
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    branch_name = f"gitfucktime-backup-{timestamp}"
    
    try:
        subprocess.check_call(["git", "branch", branch_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return branch_name
    except subprocess.CalledProcessError:
        return None

def detect_last_filter_branch():
    '''Detects the last filter-branch operation from reflog.'''
    try:
        # Get reflog
        # Output format: HEAD@{index} action: message
        reflog = subprocess.check_output(["git", "reflog", "--date=iso"]).decode("utf-8").splitlines()
        
        for i, line in enumerate(reflog):
            if "filter-branch: rewrite" in line:
                # Found HEAD@{i}: filter-branch: rewrite
                # Current HEAD (or HEAD@{i}) is the result of rewrite.
                # The state BEFORE the rewrite is HEAD@{i+1}
                # We need to make sure i+1 exists
                
                # Extract index just to be safe, though i corresponds to reflog index usually
                # But git reflog output might have gaps if we filter?
                # "git reflog" implies "git reflog show HEAD"
                
                return {
                    "index": i,
                    "ref": f"HEAD@{{{i}}}", # The rewrite commit
                    "target": f"HEAD@{{{i+1}}}" # The original commit before rewrite
                }
        return None
    except:
        return None

def revert_last_operation(no_backup=False):
    '''Reverts the last gitfucktime filter-branch operation.'''
    # 1. Detect last operation
    last_op = detect_last_filter_branch()
    if not last_op:
        return {"success": False, "message": "No 'filter-branch' operation found in recent reflog."}
    
    target_ref = last_op['target']
    
    # 2. Create backup of current state
    backup_name = None
    if not no_backup:
        backup_name = create_backup_branch()
    
    # 3. Perform Revert
    try:
         # Stash uncommitted changes
        subprocess.call(["git", "stash", "push", "-m", "gitfucktime-revert-auto-stash"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Reset to before rewrite
        subprocess.check_call(["git", "reset", "--hard", target_ref], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Try pop stash
        subprocess.call(["git", "stash", "pop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return {
            "success": True, 
            "message": f"Reverted to state before last operation ({target_ref}).",
            "backup": backup_name
        }
        
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Git command failed: {e}"}

def check_branch_divergence():
    '''Check if branch has diverged significantly from remote'''
    try:
        # Get ahead/behind counts
        ahead = int(subprocess.check_output(
            ["git", "rev-list", "--count", "origin/master..HEAD"],
            stderr=subprocess.DEVNULL
        ).decode().strip())
        
        behind = int(subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD..origin/master"],
            stderr=subprocess.DEVNULL
        ).decode().strip())
        
        return {"ahead": ahead, "behind": behind}
    except:
        return None


