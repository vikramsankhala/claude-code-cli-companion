# Chapter 43, week 5 review: a one-screen network check, layer by layer (Chapter 42).
# Run: .\netcheck.ps1   or add the netcheck function from profile.ps1
$ErrorActionPreference = "SilentlyContinue"

$cfg = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | Select-Object -First 1
$ip  = $cfg.IPv4Address.IPAddress
$gw  = $cfg.IPv4DefaultGateway.NextHop
$dns = (Get-DnsClientServerAddress -AddressFamily IPv4 -InterfaceIndex $cfg.InterfaceIndex).ServerAddresses -join ", "
$pub = try { Invoke-RestMethod https://api.ipify.org -TimeoutSec 5 } catch { "unreachable" }
$ping = Test-Connection 1.1.1.1 -Count 4
$avg = if ($ping) { [math]::Round(($ping | ForEach-Object { if ($_.Latency) { $_.Latency } else { $_.ResponseTime } } | Measure-Object -Average).Average) } else { "no reply" }
$https = (Test-NetConnection pypi.org -Port 443 -WarningAction SilentlyContinue).TcpTestSucceeded

"Private IP       : $ip"
"Default gateway  : $gw"
"DNS server(s)    : $dns"
"Public IP        : $pub"
"Ping 1.1.1.1 (ms): $avg"
"pypi.org:443     : $(if ($https) { 'reachable' } else { 'NOT reachable' })"
