"""A small query language:  free words  plus  field:value filters.

  vpn status:approved type:policy lang:de region:eu class:internal tag:security
  entity:"Acme GmbH" updated>2026-01-01
"""
import re

FIELDS = {"type": "doc_type", "status": "status", "lang": "language", "region": "region",
          "class": "classification", "entity": "entity", "dept": "dept", "owner": "owner", "tag": "tags"}
TOKEN = re.compile(r'(\w+)([:<>])("[^"]+"|\S+)|("[^"]+"|\S+)')


def parse(q: str) -> tuple[list[str], list[tuple[str, str, str]]]:
    words, filters = [], []
    for m in TOKEN.finditer(q):
        if m.group(1):
            key, op, val = m.group(1).lower(), m.group(2), m.group(3).strip('"')
            if key == "updated" and op in "<>":
                filters.append(("updated_utc", op, val))
            elif key in FIELDS and op == ":":
                filters.append((FIELDS[key], "=", val))
            else:
                words.append(m.group(0))
        else:
            words.append(m.group(4).strip('"'))
    return words, filters
