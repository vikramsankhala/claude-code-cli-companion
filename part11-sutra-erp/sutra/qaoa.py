"""A working QAOA adapter for Sutra's QUBO problems, on Qiskit (Chapter 33).

    from sutra.optimize import maintenance_qubo, solve_qubo
    from sutra.qaoa import QiskitQAOA
    Q, idx = maintenance_qubo(jobs, slots, clash)
    x, energy, solver = solve_qubo(Q, len(idx), QiskitQAOA(reps=2))

How it works
1. QUBO -> Ising. Each bit x_i becomes (1 - z_i) / 2 with z_i = +1 or -1, the eigenvalues of the Pauli Z
   operator. The QUBO energy turns into  const + sum h_i Z_i + sum J_ik Z_i Z_k  (exactly, for every x).
2. QAOA circuit. Start in an equal superposition, then repeat `reps` times: the cost layer exp(-i gamma H)
   (RZ on each qubit, RZZ on each coupled pair) and the mixer exp(-i beta X) (RX on each qubit).
3. Classical outer loop. SciPy's COBYLA picks gamma and beta to minimise the expected energy <H>.
4. Read out. Sample the tuned circuit, score the most frequent bitstrings with the exact QUBO energy and
   return the best one. QAOA proposes; the classical energy decides.

Runs on Qiskit's exact statevector simulator by default (fine up to about 20 qubits on a laptop). To use IBM
hardware, pass a Sampler V2 and its backend, for example from qiskit-ibm-runtime:

    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    backend = QiskitRuntimeService().least_busy(operational=True, simulator=False)
    QiskitQAOA(sampler=SamplerV2(mode=backend), backend=backend)

Parameters are still tuned on the simulator (cheap); only the final sampling uses the device (paid queue time).
Teaching code: for production-sized problems a classical solver or annealer usually wins today.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .optimize import QuantumProvider, energy


def qubo_to_ising(Q: dict, n: int):
    """Return (h, J, const) with E(x) = const + sum h_i z_i + sum J_ik z_i z_k and x_i = (1 - z_i) / 2."""
    h, J, const = np.zeros(n), {}, 0.0
    for (i, k), w in Q.items():
        if i == k:                       # w x_i = w/2 - (w/2) z_i
            const += w / 2
            h[i] -= w / 2
        else:                            # w x_i x_k = w/4 (1 - z_i - z_k + z_i z_k)
            a, b = min(i, k), max(i, k)
            const += w / 4
            h[a] -= w / 4
            h[b] -= w / 4
            J[a, b] = J.get((a, b), 0.0) + w / 4
    return h, J, const


def ising_energy(h, J, const, z) -> float:
    return const + float(np.dot(h, z)) + sum(w * z[i] * z[k] for (i, k), w in J.items())


def cost_operator(h, J, n):
    from qiskit.quantum_info import SparsePauliOp

    terms = [("Z", [i], h[i]) for i in range(n) if h[i] != 0] + [("ZZ", [i, k], w) for (i, k), w in J.items() if w]
    if not terms:
        return SparsePauliOp("I" * n, coeffs=[0.0])
    return SparsePauliOp.from_sparse_list(terms, num_qubits=n)


def qaoa_circuit(h, J, n, reps):
    from qiskit import QuantumCircuit
    from qiskit.circuit import ParameterVector

    gammas, betas = ParameterVector("gamma", reps), ParameterVector("beta", reps)
    qc = QuantumCircuit(n)
    qc.h(range(n))
    for layer in range(reps):
        g, b = gammas[layer], betas[layer]
        for i in range(n):
            if h[i]:
                qc.rz(2 * g * h[i], i)
        for (i, k), w in J.items():
            if w:
                qc.rzz(2 * g * w, i, k)
        qc.rx(2 * b, range(n))
    return qc, list(gammas) + list(betas)


class QiskitQAOA(QuantumProvider):
    name = "ibm-qiskit"

    def __init__(self, reps: int = 2, shots: int = 4096, top: int = 16, starts: int = 6, seed: int = 7,
                 sampler=None, backend=None, max_qubits: int = 22):
        self.reps, self.shots, self.top, self.starts, self.seed = reps, shots, top, starts, seed
        self.sampler, self.backend, self.max_qubits = sampler, backend, max_qubits
        self.report: dict = {}

    def solve(self, Q, n):
        from qiskit.primitives import StatevectorSampler
        from qiskit.quantum_info import Statevector

        if n > self.max_qubits:
            raise ValueError(f"{n} qubits is too many for statevector QAOA (limit {self.max_qubits})")
        h, J, const = qubo_to_ising(Q, n)
        # Normalise so the angles live on a sensible scale whatever the penalty weights are.
        scale = max([abs(v) for v in h] + [abs(v) for v in J.values()] + [1e-9])
        hs, Js = h / scale, {k: v / scale for k, v in J.items()}
        op = cost_operator(hs, Js, n)
        qc, params = qaoa_circuit(hs, Js, n, self.reps)

        def expected(theta):
            bound = qc.assign_parameters(dict(zip(params, theta)))
            return float(np.real(Statevector(bound).expectation_value(op)))

        rng = np.random.default_rng(self.seed)
        best = None
        for _ in range(self.starts):
            x0 = np.concatenate([rng.uniform(0, np.pi, self.reps), rng.uniform(0, np.pi / 2, self.reps)])
            res = minimize(expected, x0, method="COBYLA", options={"maxiter": 300, "rhobeg": 0.4})
            if best is None or res.fun < best.fun:
                best = res
        tuned = qc.assign_parameters(dict(zip(params, best.x)))
        tuned.measure_all()

        if self.sampler is None:
            counts = StatevectorSampler(seed=self.seed).run([tuned], shots=self.shots).result()[0].data.meas.get_counts()
        else:
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

            isa = generate_preset_pass_manager(optimization_level=1, backend=self.backend).run(tuned)
            counts = self.sampler.run([isa], shots=self.shots).result()[0].data.meas.get_counts()

        ranked = sorted(counts.items(), key=lambda kv: -kv[1])[: self.top]
        candidates = []
        for bits, c in ranked:                       # Qiskit prints qubit 0 as the rightmost character
            x = [int(b) for b in reversed(bits)]
            candidates.append((energy(Q, x), -c, x))
        e, _, x = min(candidates)
        self.report = {"qubits": n, "reps": self.reps, "expected_energy": round(float(best.fun * scale + const), 4),
                       "angles": [round(float(a), 4) for a in best.x], "distinct_samples": len(counts),
                       "best_probability": counts.get("".join(map(str, reversed(x))), 0) / self.shots}
        return x, round(float(e), 4)
