# Feed the hook the same JSON Claude Code would send, without starting Claude Code.
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
foreach ($cmd in 'ls -la', 'rm -rf ~/tmp-test', 'rm -rf ./build') {
  $json = @{ tool_name = 'Bash'; tool_input = @{ command = $cmd } } | ConvertTo-Json -Compress
  $json | python (Join-Path $here '.claude\hooks\block_rm.py')
  Write-Host "exit $LASTEXITCODE  <-  $cmd"
}
