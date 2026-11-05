# Check which free-tier keys work, with one tiny request each (Windows PowerShell).
# Usage: .\scripts\test-keys.ps1     Keys come from environment variables; nothing is printed except status.
$tests = @(
  @{ Name = "NVIDIA";     Var = "NVIDIA_API_KEY";     Url = "https://integrate.api.nvidia.com/v1/models" },
  @{ Name = "OpenRouter"; Var = "OPENROUTER_API_KEY"; Url = "https://openrouter.ai/api/v1/key" },
  @{ Name = "Groq";       Var = "GROQ_API_KEY";       Url = "https://api.groq.com/openai/v1/models" },
  @{ Name = "Mistral";    Var = "MISTRAL_API_KEY";    Url = "https://api.mistral.ai/v1/models" },
  @{ Name = "Gemini";     Var = "GEMINI_API_KEY";     Url = "https://generativelanguage.googleapis.com/v1beta/openai/models" }
)
foreach ($t in $tests) {
  $key = [Environment]::GetEnvironmentVariable($t.Var)
  if (-not $key) { "{0,-11} not set ({1})" -f $t.Name, $t.Var; continue }
  try {
    Invoke-RestMethod $t.Url -Headers @{ Authorization = "Bearer $key" } -TimeoutSec 20 | Out-Null
    "{0,-11} OK" -f $t.Name
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    "{0,-11} FAILED (HTTP {1})" -f $t.Name, $code
  }
}
