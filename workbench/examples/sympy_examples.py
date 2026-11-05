"""Chapter 40 example: sympy_examples.py. Run: python sympy_examples.py"""
import sympy as sp
x, t = sp.symbols("x t")
f = sp.Function("f")
print(sp.integrate(sp.exp(-x**2), (x, -sp.oo, sp.oo)))
print(sp.solve(x**2 - 5*x + 6, x))
print(sp.series(sp.sin(x), x, 0, 6))
print(sp.dsolve(f(t).diff(t, 2) + f(t), f(t)))
