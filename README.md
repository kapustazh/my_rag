*This project has been created as part of the 42 curriculum by mnestere*

# Description

# Instructions

## Development

```bash
make install      # install dependencies
make lint-strict  # run strict linting locally
```

## CI and pull requests

Every push to a feature branch runs `make lint-strict` in GitHub Actions. If it passes and no PR exists yet, a pull request to `main` is opened automatically.

To block merging when CI fails, enable branch protection on `main`:

1. GitHub repo → **Settings** → **Branches** → **Add branch ruleset** (or edit rule for `main`)
2. Require a pull request before merging
3. Require status check **lint-strict**
4. Save

# System architecture

# Chunking strategy

# Retrieval method

# Performance analysis

# Design decisions

# Challenges faced

# Example usage

# Resources

- Introduction to Natural Language Processing: https://www.geeksforgeeks.org/nlp/introduction-to-natural-language-processing-nlp/