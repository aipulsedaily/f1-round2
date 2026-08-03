"""Diff two material-graph censuses. Which materials moved, and in what.

    python3 work/r2100/material_graph_diff.py OLD.json NEW.json
"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
A, B = a["rows"], b["rows"]
ka, kb = set(A), set(B)
common = ka & kb
moved = sorted(k for k in common if A[k]["hash"] != B[k]["hash"])
same = sorted(k for k in common if A[k]["hash"] == B[k]["hash"])

print("materials   old %d   new %d   common %d   only-old %d   only-new %d"
      % (len(A), len(B), len(common), len(ka - kb), len(kb - ka)))
if ka - kb:
    print("  only in old:", sorted(ka - kb))
if kb - ka:
    print("  only in new:", sorted(kb - ka))
print("graphs that MOVED:     %d of %d" % (len(moved), len(common)))
print("graphs BIT-IDENTICAL:  %d" % len(same))
for k in moved:
    print("  %-24s nodes %d->%d links %d->%d"
          % (k, A[k]["nodes"], B[k]["nodes"], A[k]["links"], B[k]["links"]))
    ga = json.loads(A[k].get("graph", "{}"))
    gb = json.loads(B[k].get("graph", "{}"))
    la, lb = set(ga.get("l", [])), set(gb.get("l", []))
    for x in sorted(la - lb)[:8]:
        print("      link REMOVED  %s" % x)
    for x in sorted(lb - la)[:8]:
        print("      link ADDED    %s" % x)
    na = {n["name"]: n for n in ga.get("n", [])}
    nb = {n["name"]: n for n in gb.get("n", [])}
    for n in sorted(set(na) | set(nb)):
        if na.get(n) != nb.get(n):
            if n not in na:
                print("      node ADDED    %s (%s)" % (n, nb[n]["idname"]))
            elif n not in nb:
                print("      node REMOVED  %s (%s)" % (n, na[n]["idname"]))
            else:
                ia = {tuple(x[:2]): x[2:] for x in na[n]["inputs"]}
                ib = {tuple(x[:2]): x[2:] for x in nb[n]["inputs"]}
                for s in sorted(set(ia) | set(ib), key=str):
                    if ia.get(s) != ib.get(s):
                        print("      socket        %s.%s  %r -> %r"
                              % (n, s[1], ia.get(s), ib.get(s)))
                if na[n]["props"] != nb[n]["props"]:
                    for p in sorted(set(na[n]["props"]) | set(nb[n]["props"])):
                        if na[n]["props"].get(p) != nb[n]["props"].get(p):
                            print("      prop          %s.%s  %r -> %r"
                                  % (n, p, na[n]["props"].get(p),
                                     nb[n]["props"].get(p)))
print("STAGE RESULT: %s"
      % ("MATERIAL_GRAPHS_IDENTICAL" if not moved and ka == kb
         else "MATERIAL_GRAPHS_DIFFER"))
