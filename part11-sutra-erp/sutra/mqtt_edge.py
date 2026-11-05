"""MQTT edge simulator and gateway for Sutra (Chapters 31 and 34).

Sensors publish readings; an edge gateway subscribes, runs EdgeMonitor (threshold, predictive and anomaly
alerts) next to the machines, and publishes only the alerts upstream. Raw telemetry stays on site.

Topics:   sutra/<site>/<device>/<metric>   payload {"t": hours, "v": value, "q": 192}
Alerts:   sutra/<site>/<device>/alerts     payload: the EdgeMonitor alert dict

Run against a real broker (docker compose up mqtt), in two terminals:
    python -m sutra.mqtt_edge gateway --host localhost
    python -m sutra.mqtt_edge sensors --host localhost --hours 96
Or everything in one process, no broker needed:
    python -m sutra.mqtt_edge demo
"""
from __future__ import annotations

import argparse
import json
import math
import random
import threading
import time
from collections import defaultdict
from collections.abc import Callable, Iterator

from .iot import EdgeMonitor

Handler = Callable[[str, bytes], None]


def topic_matches(pattern: str, topic: str) -> bool:
    """MQTT wildcard rules: `+` matches one level, `#` matches the rest (and must be last)."""
    p, t = pattern.split("/"), topic.split("/")
    for i, part in enumerate(p):
        if part == "#":
            return i == len(p) - 1
        if i >= len(t) or (part != "+" and part != t[i]):
            return False
    return len(p) == len(t)


class MemoryBroker:
    """An in-process broker with MQTT topic matching: for tests, demos and laptops without Docker."""

    def __init__(self):
        self.subs: list[tuple[str, Handler]] = []
        self.published: list[tuple[str, bytes]] = []

    def subscribe(self, pattern: str, handler: Handler) -> None:
        self.subs.append((pattern, handler))

    def publish(self, topic: str, payload: bytes) -> None:
        self.published.append((topic, payload))
        for pattern, handler in list(self.subs):
            if topic_matches(pattern, topic):
                handler(topic, payload)

    def flush(self, timeout: float = 0) -> None:      # same interface as PahoTransport
        pass

    def close(self) -> None:
        pass


class PahoTransport:
    """The same interface over a real MQTT broker (Mosquitto, EMQX, HiveMQ, AWS IoT Core) with paho-mqtt 2.x."""

    def __init__(self, host: str = "localhost", port: int = 1883, client_id: str = "", username: str | None = None,
                 password: str | None = None, tls: bool = False, qos: int = 1):
        import paho.mqtt.client as mqtt

        self.qos, self.subs, self._pending = qos, [], []
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
        if username:
            self.client.username_pw_set(username, password)
        if tls:
            self.client.tls_set()
        self.client.on_message = lambda c, u, m: [h(m.topic, m.payload) for p, h in self.subs
                                                  if topic_matches(p, m.topic)]
        self._connected = threading.Event()
        self.client.on_connect = lambda c, u, f, rc, props=None: (self._resubscribe(), self._connected.set())
        self.client.connect(host, port, keepalive=30)
        self.client.loop_start()
        if not self._connected.wait(10):
            raise ConnectionError(f"no MQTT broker answered at {host}:{port}")

    def _resubscribe(self):
        for pattern, _ in self.subs:
            self.client.subscribe(pattern, qos=self.qos)

    def subscribe(self, pattern: str, handler: Handler) -> None:
        self.subs.append((pattern, handler))
        self.client.subscribe(pattern, qos=self.qos)       # the SUBACK arrives asynchronously
        time.sleep(0.2)

    def publish(self, topic: str, payload: bytes) -> None:
        # Never block here: the gateway publishes alerts from inside on_message, on paho's network thread,
        # and waiting for the PUBACK on that thread would stall every message behind it.
        self._pending.append(self.client.publish(topic, payload, qos=self.qos))

    def flush(self, timeout: float = 10.0) -> None:
        """Wait until every QoS 1 message published so far has been acknowledged by the broker."""
        end = time.monotonic() + timeout
        for info in self._pending:
            info.wait_for_publish(max(0.0, end - time.monotonic()))
        self._pending = [i for i in self._pending if not i.is_published()]

    def close(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()


# --- Sensors ------------------------------------------------------------------------------------------------
PROFILES = {  # metric: (baseline, noise, daily cycle amplitude)
    "vibration_mm_s": (3.0, 0.25, 0.3),
    "bearing_temp_c": (62.0, 0.8, 2.0),
    "current_a": (35.0, 0.6, 1.0),
}


def readings(device: str, hours: int = 96, seed: int = 11, wear_from: int | None = 40,
             wear_rate: float = 0.11, spike_at: int | None = None) -> Iterator[tuple[str, float, float]]:
    """Hourly (metric, t, value) for one machine. From `wear_from` a bearing starts to wear: vibration and
    temperature drift upwards, which is what predictive alerts should catch before the thresholds do."""
    rnd = random.Random(f"{device}:{seed}")
    for t in range(hours):
        for metric, (base, noise, cycle) in PROFILES.items():
            v = base + cycle * math.sin(2 * math.pi * t / 24) + rnd.gauss(0, noise)
            if wear_from is not None and t >= wear_from and metric != "current_a":
                v += (t - wear_from) * wear_rate * (1 if metric == "vibration_mm_s" else 4)
            if spike_at is not None and t == spike_at and metric == "current_a":
                v += 9
            yield metric, float(t), round(v, 3)


def run_sensors(bus, site: str = "pune", devices=("press-01", "press-02"), hours: int = 96, delay: float = 0.0,
                **kw) -> int:
    sent = 0
    streams = {d: readings(d, hours, wear_from=kw.get("wear_from", 40) if d == devices[0] else None,
                           spike_at=60 if d == devices[-1] else None) for d in devices}
    for batch in zip(*streams.values()):
        for d, (metric, t, v) in zip(devices, batch):
            bus.publish(f"sutra/{site}/{d}/{metric}", json.dumps({"t": t, "v": v, "q": 192}).encode())
            sent += 1
        if delay:
            time.sleep(delay)
    return sent


# --- Gateway ------------------------------------------------------------------------------------------------
class EdgeGateway:
    """Subscribes to raw telemetry, runs EdgeMonitor locally, publishes alerts. Bad payloads are counted, not fatal."""

    def __init__(self, bus, site: str = "+", monitor: EdgeMonitor | None = None):
        self.bus, self.monitor = bus, monitor or EdgeMonitor()
        self.alerts: list[dict] = []
        self.stats = defaultdict(int)
        bus.subscribe(f"sutra/{site}/+/+", self.on_message)

    def on_message(self, topic: str, payload: bytes) -> None:
        _, site, device, metric = topic.split("/")
        if metric == "alerts":
            return
        try:
            msg = json.loads(payload)
            t, v, q = float(msg["t"]), float(msg["v"]), int(msg.get("q", 192))
        except (ValueError, KeyError, TypeError):
            self.stats["bad_payload"] += 1
            return
        if q < 192:                          # OPC UA style: below 192 is uncertain or bad quality
            self.stats["bad_quality"] += 1
            return
        self.stats["readings"] += 1
        for a in self.monitor.ingest(device, metric, t, v):
            a["site"] = site
            self.alerts.append(a)
            self.bus.publish(f"sutra/{site}/{device}/alerts", json.dumps(a).encode())


def summarise(alerts: list[dict]) -> dict:
    first = {}
    for a in alerts:
        first.setdefault((a["device"], a["metric"], a["kind"], a["severity"]), a["t"])
    return {f"{d} {m} {k}/{s}": t for (d, m, k, s), t in sorted(first.items(), key=lambda kv: kv[1])}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["demo", "sensors", "gateway"])
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--site", default="pune")
    ap.add_argument("--hours", type=int, default=96)
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between simulated hours")
    args = ap.parse_args(argv)
    if args.mode == "demo":
        bus = MemoryBroker()
        gw = EdgeGateway(bus)
        n = run_sensors(bus, args.site, hours=args.hours)
        print(f"{n} readings, {len(gw.alerts)} alerts published upstream (raw telemetry stayed on site)")
        for k, t in summarise(gw.alerts).items():
            print(f"  hour {t:>4.0f}  {k}")
        return 0
    bus = PahoTransport(args.host, args.port, client_id=f"sutra-{args.mode}")
    try:
        if args.mode == "sensors":
            n = run_sensors(bus, args.site, hours=args.hours, delay=args.delay)
            bus.flush()
            print(f"published {n} readings")
        else:
            gw = EdgeGateway(bus)
            print(f"gateway listening on {args.host}:{args.port} for sutra/+/+/+  (Ctrl+C to stop)")
            seen = 0
            while True:
                time.sleep(1)
                for a in gw.alerts[seen:]:
                    print(f"{a['site']}/{a['device']} {a['kind']}/{a['severity']} {a['metric']}={a['value']} ({a['why']})")
                seen = len(gw.alerts)
    except KeyboardInterrupt:
        pass
    finally:
        bus.flush(1)
        bus.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
