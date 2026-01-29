# Pre-commit Hook Setup

This project includes a pre-commit hook that runs all tests before allowing commits.

## Installation

The hook is already installed in `.git/hooks/pre-commit`.

On Unix/Mac, make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

On Windows, the hook will run automatically via Python.

## Usage

The hook runs automatically when you commit. If tests fail, the commit is rejected.

To bypass the hook (not recommended):
```bash
git commit --no-verify
```

## Manual Testing

Run tests manually:
```bash
python -m unittest discover tests -v
```
