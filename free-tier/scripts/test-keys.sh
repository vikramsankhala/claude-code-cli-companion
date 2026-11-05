#!/usr/bin/env bash
# Check which free-tier keys work, with one tiny request each (macOS, Linux). Prints status only.
check() {
  local name=$1 var=$2 url=$3 key=${!2:-}
  if [ -z "$key" ]; then printf '%-11s not set (%s)\n' "$name" "$var"; return; fi
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $key" --max-time 20 "$url")
  if [ "$code" = 200 ]; then printf '%-11s OK\n' "$name"; else printf '%-11s FAILED (HTTP %s)\n' "$name" "$code"; fi
}
check NVIDIA     NVIDIA_API_KEY     https://integrate.api.nvidia.com/v1/models
check OpenRouter OPENROUTER_API_KEY https://openrouter.ai/api/v1/key
check Groq       GROQ_API_KEY       https://api.groq.com/openai/v1/models
check Mistral    MISTRAL_API_KEY    https://api.mistral.ai/v1/models
check Gemini     GEMINI_API_KEY     https://generativelanguage.googleapis.com/v1beta/openai/models
