# Student set-up: NVIDIA API catalogue (about 15 minutes)

You will use NVIDIA's free API catalogue for this course's labs. It is for learning only: no client data, no personal data, nothing in production.

1. **Create your own account.** Join the free NVIDIA Developer Program and sign in at **build.nvidia.com** with your own email address. Do not share an account or a key with anyone: limits are per account, and sharing breaks the terms.
2. **Get a key.** Open any model's page, choose **Get API Key**, and copy it. It starts with `nvapi-`.
3. **Store it safely.**
   - Windows PowerShell: `setx NVIDIA_API_KEY "nvapi-..."`, then close and reopen PowerShell.
   - macOS or Linux: add `export NVIDIA_API_KEY="nvapi-..."` to `~/.zshrc` or `~/.bashrc`, then open a new terminal.
   - Never paste the key into code, a notebook, a chat, a screenshot or a repository.
4. **Get the lab kit.**
   ```powershell
   git clone https://github.com/vikramsankhala/claude-code-cli-companion.git
   cd claude-code-cli-companion\free-tier
   python -m venv .venv; .venv\Scripts\activate
   pip install -r requirements.txt
   ```
5. **Check it works.**
   ```powershell
   .\scripts\test-keys.ps1             # NVIDIA should say OK
   cd nvidia
   python probe_models.py              # which models your key can call (about 3 minutes)
   $env:NVIDIA_MODEL = "<a model the probe marked 'answers'>"
   python hello.py
   ```
6. **If you see "rate-limited",** wait a minute. The scripts already slow down and retry.

If your key ever appears somewhere public, revoke it on build.nvidia.com straight away and create a new one.
