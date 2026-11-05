"""Optimisation: a classical MILP for production planning, and a QUBO for maintenance scheduling that
runs on a local annealer today and on a quantum provider when one is configured."""
import itertools
import math
import random

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


def production_plan(products, machines):
    """Maximise margin subject to machine hours. products: {name: (margin, {machine: hours_per_unit}, max_demand)}."""
    names = list(products)
    c = -np.array([products[n][0] for n in names], dtype=float)
    A = np.array([[products[n][1].get(m, 0) for n in names] for m in machines])
    cons = LinearConstraint(A, -np.inf, np.array(list(machines.values()), dtype=float))
    res = milp(c, constraints=cons, integrality=np.ones(len(names)),
               bounds=Bounds(0, np.array([products[n][2] for n in names], dtype=float)))
    if not res.success:
        raise RuntimeError(res.message)
    plan = {n: int(round(x)) for n, x in zip(names, res.x)}
    return plan, round(-res.fun, 2)


def maintenance_qubo(jobs, slots, clash, penalty=10.0):
    """x[j,s] = 1 if job j runs in slot s. Each job exactly once; clashing jobs not in the same slot;
    risk cost[j][s] rewards early slots for risky machines. Returns (Q dict, variable index)."""
    idx = {(j, s): i for i, (j, s) in enumerate(itertools.product(jobs, range(slots)))}
    Q = {}

    def add(a, b, w):
        key = (min(a, b), max(a, b))
        Q[key] = Q.get(key, 0) + w

    for j, risk in jobs.items():
        for s in range(slots):
            add(idx[j, s], idx[j, s], risk * s - penalty)          # (sum_s x - 1)^2 expands to -x + 2xx'
            for s2 in range(s + 1, slots):
                add(idx[j, s], idx[j, s2], 2 * penalty)
    for a, b in clash:
        for s in range(slots):
            add(idx[a, s], idx[b, s], penalty)
    return Q, idx


def energy(Q, x):
    return sum(w * x[i] * x[k] for (i, k), w in Q.items())


def anneal(Q, n, sweeps=4000, seed=7, t0=5.0, t1=0.01):
    """Simulated annealing: the classical stand-in for a quantum annealer. Deterministic for a seed."""
    rnd = random.Random(seed)
    nbr = [[] for _ in range(n)]
    for (i, k), w in Q.items():
        if i != k:
            nbr[i].append((k, w))
            nbr[k].append((i, w))
    lin = [Q.get((i, i), 0) for i in range(n)]
    x = [rnd.randint(0, 1) for _ in range(n)]
    best, best_e = x[:], energy(Q, x)
    e = best_e
    for step in range(sweeps):
        T = t0 * (t1 / t0) ** (step / sweeps)
        i = rnd.randrange(n)
        d = (1 - 2 * x[i]) * (lin[i] + sum(w * x[k] for k, w in nbr[i]))
        if d <= 0 or rnd.random() < math.exp(-d / T):
            x[i] ^= 1
            e += d
            if e < best_e:
                best, best_e = x[:], e
    return best, round(best_e, 4)


def brute_force(Q, n):
    return min(((list(b), energy(Q, b)) for b in itertools.product((0, 1), repeat=n)), key=lambda r: r[1])


def decode(x, idx):
    return {j: s for (j, s), i in idx.items() if x[i]}


class QuantumProvider:
    """Adapter for qubit access providers. Each subclass maps the same QUBO to a vendor SDK.
    Configure one in tenant settings; without credentials the platform falls back to `anneal`."""
    name = "base"

    def solve(self, Q, n):
        raise NotImplementedError


class DWaveLeap(QuantumProvider):
    name = "dwave-leap"          # pip install dwave-ocean-sdk; needs DWAVE_API_TOKEN

    def solve(self, Q, n):
        from dwave.system import DWaveSampler, EmbeddingComposite  # noqa: PLC0415 (imported only when configured)
        ss = EmbeddingComposite(DWaveSampler()).sample_qubo(Q, num_reads=200)
        best = ss.first
        return [best.sample[i] for i in range(n)], best.energy


# QiskitQAOA (gate-model QAOA on Qiskit, simulator or IBM hardware) lives in sutra/qaoa.py; see __getattr__ below.


class Braket(QuantumProvider):
    name = "aws-braket"          # pip install amazon-braket-sdk; IAM credentials; IonQ, Rigetti, IQM devices


def solve_qubo(Q, n, provider: QuantumProvider | None = None):
    if provider is not None:
        try:
            return provider.solve(Q, n) + (provider.name,)
        except Exception:
            pass                 # fall back, and the caller logs that the fallback was used
    return anneal(Q, n) + ("local-anneal",)


def __getattr__(name):           # `from sutra.optimize import QiskitQAOA` still works, without importing Qiskit eagerly
    if name == "QiskitQAOA":
        from .qaoa import QiskitQAOA
        return QiskitQAOA
    raise AttributeError(name)
