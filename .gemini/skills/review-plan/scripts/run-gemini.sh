#!/bin/bash
# run-gemini.sh: Executes a plan review using Gemini CLI

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <plan-file-path>"
    exit 1
fi

PLAN_FILE=$1

if [ ! -f "$PLAN_FILE" ]; then
    echo "Error: Plan file not found: $PLAN_FILE"
    exit 1
fi

echo "--- Reviewing Plan: $PLAN_FILE ---"
# In a real scenario, this would invoke gemini-cli with a specific prompt
# For now, we simulate the output
echo "Reviewing architecture and logic..."
echo "Found 2 Major issues and 3 Minor suggestions."
echo "--- Review Complete ---"
