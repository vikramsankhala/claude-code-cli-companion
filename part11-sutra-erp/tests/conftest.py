import os
import sys
from pathlib import Path

os.environ["KB_EMBEDDER"] = "hash"          # offline, deterministic embeddings for tests
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
