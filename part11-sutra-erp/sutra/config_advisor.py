"""Configuration advisor: finds configuration that will fail before users hit it, and offers fixes."""


def advise(cfg: dict, pack: dict) -> list[dict]:
    out = []
    mapped = set(cfg.get("tax_mapping", {}))
    for g in cfg.get("item_groups", []):
        if g not in mapped:
            out.append({"problem": f"item group '{g}' has no tax code", "severity": "high",
                        "options": [f"map '{g}' to standard rate ({pack['tax']['rates']['standard']:.0%})",
                                    f"map '{g}' to reduced rate", "copy mapping from a similar group"]})
    bands = sorted(cfg.get("approval_matrix", []), key=lambda b: b["from"])
    edge = 0
    for b in bands:
        if b["from"] > edge:
            out.append({"problem": f"no approver for amounts {edge} to {b['from']}", "severity": "high",
                        "options": [f"extend band starting {b['from']} down to {edge}", "add a new approval band"]})
        if b["approver"] in b.get("requesters", []):
            out.append({"problem": f"approver {b['approver']} can approve own requests", "severity": "medium",
                        "options": ["add a second approver", "route to the next band"]})
        edge = max(edge, b["to"])
    if cfg.get("data_region") != pack["privacy"]["data_residency"]:
        out.append({"problem": f"data stored in {cfg.get('data_region')} but {pack['privacy']['law']} pack expects "
                               f"{pack['privacy']['data_residency']}", "severity": "high",
                    "options": [f"move tenant storage to region {pack['privacy']['data_residency']}",
                                "record a legal basis for transfer and get DPO sign-off"]})
    return out
