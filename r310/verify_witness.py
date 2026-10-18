"""Independent check of a claimed Ramsey witness (graph6 on stdin or argv):
triangle-free and independence number < t, via networkx (shares no code
with graphs.py / indep.c)."""
import sys
import networkx as nx

g6, t = sys.argv[1], int(sys.argv[2])
G = nx.from_graph6_bytes(g6.strip().encode())
tri = sum(nx.triangles(G).values()) // 3
alpha = max(len(c) for c in nx.find_cliques(nx.complement(G)))
print(f"n={G.number_of_nodes()} e={G.number_of_edges()} triangles={tri} alpha={alpha}")
print("VALID (3,%d,%d)-graph" % (t, G.number_of_nodes()) if tri == 0 and alpha < t else "INVALID")
