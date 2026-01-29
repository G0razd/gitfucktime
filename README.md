# Git Fuck Time

<p align="center">
  <img src="logo.png" alt="Git Fuck Time Logo" width="300">
</p>


`gitfucktime` is a CLI utility to rewrite your git commit timestamps to make them look like they were done during "standard" work hours (09:00 - 17:00, Mon-Fri).

This is useful if you do a lot of coding late at night or on weekends but want your git history to reflect a standard 9-5 schedule.

## Features

-   **Work Hours Only**: Spreads commits between 09:00 and 17:00.
-   **Work Days Only**: Skips weekends (Saturday and Sunday).
-   **Smart Date Detection**: (Default) Automatically starts rewriting from the day after the last *unmodified* commit, spreading successive commits over realistic intervals (1 commit/day average).
-   **Flexible Selection**: Choose commits to rewrite by:
    -   Specific date range (`--start`, `--end`)
    -   Last N commits (`--last`)
    -   First N commits (`--first`)
    -   Unpushed commits only (`--unpushed`)

## Installation

You can install it directly from the source:

```bash
git clone https://github.com/yourusername/gitfucktime.git
cd gitfucktime
pip install -e .
```

Once installed, the `gitfucktime` command will be available globally.

## Usage

### 1. Smart Mode (Recommended)
Automatically detects the commit *before* your unpushed changes and starts spreading your unpushed commits starting from the next work day.

```bash
gitfucktime --unpushed
# or short flag
gitfucktime -u
```

### 2. Rewrite Last N Commits
Rewrite the last 10 commits, automatically calculating start dates based on the 11th commit.

```bash
gitfucktime --last 10
```

### 3. Manual Date Range
Rewrite history to spread commits between specific dates.

```bash
gitfucktime --start 2025-01-01 --end 2025-01-10
```

### 4. Mix and Match
You can combine selection and explicit dates.

```bash
# Rewrite unpushed commits, but force start date
gitfucktime -u --start 2025-02-01
```

## CLI Reference

| Flag | Short | Description |
| :--- | :--- | :--- |
| `--start` | `-s` | Start date (YYYY-MM-DD). Optional if auto-detected. |
| `--end` | `-e` | End date (YYYY-MM-DD). Optional if auto-detected. |
| `--unpushed`| `-u` | Rewrite only unpushed commits (origin/master..HEAD). |
| `--last N` | `-l` | Rewrite last N commits from HEAD. |
| `--first N` | `-f` | Rewrite first N commits. |
| `--version` | `-v` | Show version number. |
| `--help` | `-h` | Show help message. |

## How It Works

1.  **Selection**: It identifies which commits to rewrite based on your flags.
2.  **Date Calculation**: 
    -   If dates are provided, it uses them.
    -   If not, it looks at the parent of the first commit in the list to determine a baseline date.
    -   It calculates a spread so that commits are roughly 1 per day (configurable via logic, currently ~1/day density).
3.  **Rewriting**: It creates a temporary `git filter-branch` environment filter to rewrite `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`.
4.  **Finalize**: You must force push (`git push -f`) to update the remote.

## Warning

**This tool rewrites git history.**
This changes commit hashes. If you are working on a shared branch with others, this **will** cause conflicts for them. Only use this on your own feature branches or personal projects.

**ALWAYS MAKE A BACKUP BEFORE RUNNING.**

```bash
cp -r my-project my-project-backup
```
