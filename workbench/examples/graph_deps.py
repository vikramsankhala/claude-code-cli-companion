"""Chapter 39 example: graph_deps.py. Run: python graph_deps.py"""
import networkx as nx

g = nx.DiGraph([("Python","NumPy"),("NumPy","pandas"),
                ("NumPy","SciPy"),("pandas","Modelling")])
print(list(nx.topological_sort(g)))
print(nx.degree_centrality(g))
