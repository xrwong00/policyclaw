#!/usr/bin/env bash
set -e

GSTACK_DIR="$HOME/.claude/skills/gstack"

if [ -d "$GSTACK_DIR" ]; then
  echo "gstack already installed at $GSTACK_DIR — running upgrade..."
  cd "$GSTACK_DIR" && git pull --ff-only
else
  echo "Installing gstack..."
  mkdir -p "$HOME/.claude/skills"
  git clone --single-branch --depth 1 https://github.com/garrytan/gstack.git "$GSTACK_DIR"
fi

cd "$GSTACK_DIR" && ./setup
echo "gstack ready."
