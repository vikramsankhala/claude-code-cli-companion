#!/usr/bin/env bash
# Feed the hook the same JSON Claude Code would send, without starting Claude Code.
here="$(cd "$(dirname "$0")" && pwd)"
for cmd in 'ls -la' 'rm -rf ~/tmp-test' 'rm -rf ./build'; do
  printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$cmd" | python "$here/.claude/hooks/block_rm.py"
  echo "exit $?  <-  $cmd"
done
