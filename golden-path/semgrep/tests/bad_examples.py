# Each line below must be caught by semgrep/rules.yml. This file is test data, never imported.
import subprocess

import requests

API_KEY = "nvapi-AbCdEf0123456789xyz"  # gitleaks:allow (fake key for the rule test)
subprocess.run("ls -la", shell=True)
requests.get("https://example.com", verify=False)
eval(input())
