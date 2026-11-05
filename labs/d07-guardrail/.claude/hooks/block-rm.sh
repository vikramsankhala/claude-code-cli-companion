#!/usr/bin/env bash
# .claude/hooks/block-rm.sh  (Chapter 8 worked example; needs jq)
cmd=$(jq -r '.tool_input.command')
if echo "$cmd" | grep -Eq 'rm\s+-rf\s+(/|~|\$HOME)'; then
  echo "Blocked: recursive delete of a root or home path" >&2
  exit 2
fi
exit 0
