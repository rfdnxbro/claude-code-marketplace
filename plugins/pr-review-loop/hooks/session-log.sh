#!/bin/bash
input=$(cat)
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
last_message=$(echo "$input" | jq -r '.last_assistant_message // ""')
echo "$timestamp [pr-review-loop] SubagentStop: $last_message" >> /tmp/pr-review-loop.log
