# Git Fuck Time

<p align="center">
  <img src="logo.png" alt="Git Fuck Time Logo" width="300">
</p>

**Because nobody needs to know you were debugging CSS at 3 AM on a Saturday.**

`gitfucktime` is a CLI utility that scrubs your git commit timestamps and spreads them out over a healthy, respectable 9-5, Monday-to-Friday schedule. 

Gaslight your boss, your colleagues, and even your future self into believing you have a perfect work-life balance.

## features

-   **9-to-5 Only**: Automatically shifts commits to "standard" business hours (09:00 - 17:00).
-   **No Weekends**: Skips Saturdays and Sundays, because you definitely have a life outside of work.
-   **Smart Detection**: Automatically picks up where you left off. It looks at your last pushed commit and starts falsifying... er, *correcting*... timestamps from the very next workday.
-   **Interactive Dashboard**: Run it without arguments to see a pretty summary of your shame (unpushed commits) and fix them with one click.

## prerequisites

-   **Git**: You need to have `git` installed (duh).
-   **Python 3.6+**: Because we have standards.

## installation

```bash
pip install gitfucktime
```

Congratulations, you are now a "morning person".

## usage

### 1. The "I Just Woke Up and Fixed This" Mode (Recommended)
Automatically detects your unpushed commits and spreads them out starting from the next logical work day after your last push.

```bash
# Run the interactive dashboard
gitfucktime

# Or do it silently
gitfucktime -u
```

### 2. The "Crunch Time" Cover-Up
Rewrites your last 10 commits to look like a productive week rather than a panic-fueled all-nighter.

```bash
gitfucktime --last 10
```

### 3. The micromanager
Manually specify the exact dates you want your work to appear in. We won't judge.

```bash
gitfucktime --start 2025-01-01 --end 2025-01-10
```

## cli reference

| Flag | Short | What it does |
| :--- | :--- | :--- |
| `--start` | `-s` | Start date (YYYY-MM-DD). The day you *allegedly* started working. |
| `--end` | `-e` | End date (YYYY-MM-DD). The day you *allegedly* finished. |
| `--unpushed`| `-u` | Only fixes commits you haven't exposed to the public yet. |
| `--last N` | `-l` | Fixes the last N commits. |
| `--first N` | `-f` | Fixes the first N commits (for fresh repos). |
| `--version` | `-v` | Version info. |
| `--help` | `-h` | Shows the help menu. |

## ⚠️ warning ⚠️

**This tool rewrites git history.**

This changes commit hashes. If you use this on a shared branch that others have already pulled, **they will hate you**. 

Only use this on:
1.  Your own local feature branches before you push.
2.  Personal projects where you are the benevolent dictator.

**ALWAYS MAKE A BACKUP BEFORE RUNNING.**

```bash
cp -r my-project my-project-backup
```
