#!/usr/bin/env bash
# Create GitHub repo chakshu-IVE and push current branch.
set -euo pipefail

REPO_NAME="chakshu-IVE"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v gh >/dev/null 2>&1; then
  echo "Install GitHub CLI: brew install gh && gh auth login"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Run: gh auth login"
  exit 1
fi

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
echo "Branch: $BRANCH"
echo "Latest commit: $(git log -1 --oneline)"

if git remote get-url origin >/dev/null 2>&1; then
  CURRENT="$(git remote get-url origin)"
  if [[ "$CURRENT" != *"$REPO_NAME"* ]]; then
    echo "Removing existing origin: $CURRENT"
    git remote remove origin
  fi
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "Creating GitHub repo: $REPO_NAME"
  gh repo create "$REPO_NAME" --private --source=. --remote=origin --description "Chakshu — digital forensic media examination platform (IVE)"
  git push -u origin "$BRANCH"
else
  echo "Pushing to existing origin..."
  git push -u origin "$BRANCH"
fi

LOGIN="$(gh api user -q .login)"
echo ""
echo "Done: https://github.com/${LOGIN}/${REPO_NAME}"
