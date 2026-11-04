"""Edge telemetry: threshold alerts (rules), predictive alerts (trend) and anomaly alerts (statistics).
The same code runs on an edge gateway (no network needed) and in the cloud."""
from collections import defaultdict, deque
from statistics import mean, pstdev

RULES = {  # metric: (warn, critical) upper thresholds
    "vibration_mm_s": (7.1, 11.0),     # ISO 10816-style velocity bands, illustrative
    "bearing_temp_c": (80.0, 95.0),
    "current_a": (42.0, 48.0),
}


class EdgeMonitor:
    def __init__(self, window=30, z=3.5, cooldown_h=6):
        self.hist = defaultdict(lambda: deque(maxlen=window))
        self.z, self.cooldown = z, cooldown_h
        self.last = {}             # (device, metric, kind, severity) -> time last raised: stops alert storms

    def ingest(self, device, metric, t, value) -> list[dict]:
        alerts, h = [], self.hist[(device, metric)]
        warn, crit = RULES.get(metric, (None, None))
        if crit is not None and value >= crit:
            alerts.append(self._a("threshold", "critical", device, metric, t, value, f">= {crit}"))
        elif warn is not None and value >= warn:
            alerts.append(self._a("threshold", "warning", device, metric, t, value, f">= {warn}"))
        if len(h) >= 10:
            mu, sd = mean(v for _, v in h), pstdev(v for _, v in h)
            if sd > 0 and abs(value - mu) / sd >= self.z:
                alerts.append(self._a("anomaly", "warning", device, metric, t, value, f"z={abs(value - mu) / sd:.1f}"))
            eta = self.time_to_threshold(h, warn)
            if eta is not None and 0 < eta <= 24 and (warn is None or value < warn):
                alerts.append(self._a("predictive", "warning", device, metric, t, value,
                                      f"reaches {warn} in about {eta:.0f} h", eta_hours=round(eta, 1)))
        h.append((t, value))
        fresh = []
        for a in alerts:
            k = (device, metric, a["kind"], a["severity"])
            if k not in self.last or t - self.last[k] >= self.cooldown:
                self.last[k] = t
                fresh.append(a)
        return fresh

    @staticmethod
    def time_to_threshold(h, limit):
        """Least-squares slope over the window; hours until the trend crosses the limit."""
        if limit is None or len(h) < 10:
            return None
        ts, vs = [p[0] for p in h], [p[1] for p in h]
        tm, vm = mean(ts), mean(vs)
        den = sum((x - tm) ** 2 for x in ts)
        slope = sum((x - tm) * (y - vm) for x, y in zip(ts, vs)) / den if den else 0
        if slope <= 0:
            return None
        return (limit - vs[-1]) / slope

    @staticmethod
    def _a(kind, severity, device, metric, t, value, why, **extra):
        return {"kind": kind, "severity": severity, "device": device, "metric": metric, "t": t,
                "value": round(value, 2), "why": why, **extra}
