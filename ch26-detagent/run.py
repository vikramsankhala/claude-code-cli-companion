"""Usage: python run.py invoice.txt [--record MODEL]   (replays cassettes/invoices.json by default)"""
import json
import sys

from detagent.agent import InvoiceAgent
from detagent.journal import Journal
from detagent.model import Cassette, OpenAICompatible

args = sys.argv[1:]
inner = OpenAICompatible(args[args.index("--record") + 1]) if "--record" in args else None
agent = InvoiceAgent(Cassette("cassettes/invoices.json", inner, name="devstral"), Journal("journal.sqlite"), {"PO-12345"})
print(json.dumps(agent.run(open(args[0]).read()), indent=2))
