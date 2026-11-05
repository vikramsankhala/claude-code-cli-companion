# Nothing here should be reported.
import os
import subprocess

import requests

API_KEY = os.environ["NVIDIA_API_KEY"]
subprocess.run(["ls", "-la"], check=True)
requests.get("https://example.com", timeout=10)
