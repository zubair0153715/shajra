"""Shajra verification — hand-computed expectations, no invented data.

Run: ~/workspace/.venv-fc/bin/python tests/verify.py
Covers: outline parsing, tree stats, right/down/radial layout coordinates
(hand-computed), no-overlap, JSON round-trip, tree validation, and the
HTTP routes via TestClient (no main app needed).
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shajra import engine  # noqa: E402

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def close(a, b, tol=0.01):
    return abs(a - b) <= tol


def sample_tree():
    """R -> [A (leaf), B -> [B1, B2]]. IDs assigned DFS: n1..n5."""
    engine.reset_ids()
    root = engine.make_node("R")
    a = engine.make_node("A")
    b = engine.make_node("B")
    b1 = engine.make_node("B1")
    b2 = engine.make_node("B2")
    b["children"] = [b1, b2]
    root["children"] = [a, b]
    return root


def test_outline():
    print("outline parsing")
    tree, err = engine.parse_outline(
        "Antibiotics\n  Beta-lactams\n    Penicillins\n    Cephalosporins\n  Macrolides\n")
    check("outline ok", err is None and tree is not None, str(err))
    check("outline root", tree["text"] == "Antibiotics")
    check("outline children", [c["text"] for c in tree["children"]] ==
          ["Beta-lactams", "Macrolides"])
    check("outline grandchildren",
          [c["text"] for c in tree["children"][0]["children"]] ==
          ["Penicillins", "Cephalosporins"])
    # tabs + bullets + numbered lines
    tree, err = engine.parse_outline(
        "Root\n\t- Child one\n\t* Child two\n\t1. Child three\n")
    check("tabs/bullets/numbers", err is None and
          [c["text"] for c in tree["children"]] ==
          ["Child one", "Child two", "Child three"], str(err))
    # level jump clamps to parent+1 (no orphan levels)
    tree, err = engine.parse_outline("R\n      Deep\n")
    check("jump clamped", err is None and
          tree["children"][0]["text"] == "Deep", str(err))
    # extra level-0 lines fold under the root
    tree, err = engine.parse_outline("R\nSecond\nThird\n")
    check("extra roots fold", err is None and
          [c["text"] for c in tree["children"]] == ["Second", "Third"])
    # empty / blank
    tree, err = engine.parse_outline("   \n\n")
    check("empty outline errors", tree is None and err is not None)
    # blank lines skipped
    tree, err = engine.parse_outline("R\n\n  A\n\n  B\n")
    check("blank lines skipped", err is None and len(tree["children"]) == 2)


def test_stats():
    print("stats")
    tree = sample_tree()
    check("count 5", engine.count_nodes(tree) == 5)
    check("depth 2", engine.max_depth(tree) == 2)
    check("leaves 3", engine.leaf_count(tree) == 3)
    check("find n4", engine.find_node(tree, "n4")["text"] == "B1")
    check("find missing", engine.find_node(tree, "n99") is None)


def test_right_layout():
    print("right layout (hand-computed)")
    tree = sample_tree()
    lay = engine.layout(tree, "right")
    n = lay["nodes"]
    # Leaves take slots 0, 58, 116 (NODE_H 42 + V_GAP 16). B is the
    # midpoint of B1/B2 = 87. R is the midpoint of its *children* A
    # (y=0) and B (y=87) = 43.5 — not the span of all leaves.
    # x = depth * (180 + 70) = depth * 250.
    exp = {"n1": (0, 43.5), "n2": (250, 0), "n3": (250, 87),
           "n4": (500, 58), "n5": (500, 116)}
    for nid, (ex, ey) in exp.items():
        check(f"right {nid}", close(n[nid]["x"], ex) and
              close(n[nid]["y"], ey),
              f"got ({n[nid]['x']},{n[nid]['y']}) want ({ex},{ey})")
    check("right edges", lay["edges"] == [("n1", "n2"), ("n1", "n3"),
                                           ("n3", "n4"), ("n3", "n5")])
    check("right size", lay["width"] == 500 + 180 + 30 and
          lay["height"] == 116 + 42 + 30, f"{lay['width']}x{lay['height']}")


def test_down_layout():
    print("down layout (transpose of right)")
    tree = sample_tree()
    lay = engine.layout(tree, "down")
    n = lay["nodes"]
    exp = {"n1": (43.5, 0), "n2": (0, 250), "n3": (87, 250),
           "n4": (58, 500), "n5": (116, 500)}
    for nid, (ex, ey) in exp.items():
        check(f"down {nid}", close(n[nid]["x"], ex) and
              close(n[nid]["y"], ey),
              f"got ({n[nid]['x']},{n[nid]['y']}) want ({ex},{ey})")


def test_radial_layout():
    print("radial layout (hand-computed)")
    tree = sample_tree()
    lay = engine.layout(tree, "radial")
    n = lay["nodes"]
    # 3 leaves: angles pi/3, pi, 5pi/3. Root sits at r=0 (the radial
    # origin). The canvas is only shifted so everything is visible, so
    # the root is NOT the canvas centre — the invariant is that every
    # node's centre lies on a circle of radius depth*R_STEP around the
    # root's centre, at the expected compass direction.
    rx = n["n1"]["x"] + 90
    ry = n["n1"]["y"] + 21
    # A is depth 1 -> radius 170 from the centre; B1/B2 depth 2 -> 340.
    for nid, want_r in [("n2", 170), ("n4", 340), ("n5", 340)]:
        dx = n[nid]["x"] + 90 - rx
        dy = n[nid]["y"] + 21 - ry
        r = math.hypot(dx, dy)
        check(f"radial {nid} radius {want_r}", close(r, want_r, 1.0),
              f"got {r:.2f}")
    # B1 (angle pi) is due left of the root, at the same height.
    check("radial B1 left", n["n4"]["x"] < rx - 300)
    check("radial B1 level", close(n["n4"]["y"] + 21, ry, 1.0))
    # A (angle pi/3, sin > 0) is below the root; B2 (angle 5pi/3,
    # sin < 0) is above it (screen y grows downwards).
    check("radial A below root", n["n2"]["y"] + 21 > ry)
    check("radial B2 above root", n["n5"]["y"] + 21 < ry)


def test_no_overlap():
    print("no overlap (right layout, wider tree)")
    engine.reset_ids()
    root = engine.make_node("Root")
    for i in range(4):
        branch = engine.make_node(f"Branch {i}")
        for j in range(3):
            leaf = engine.make_node(f"Leaf {i}-{j}")
            branch["children"].append(leaf)
        root["children"].append(branch)
    lay = engine.layout(root, "right")
    nodes = list(lay["nodes"].values())
    overlap = False
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            if (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"] and
                    a["y"] < b["y"] + b["h"] and b["y"] < a["y"] + a["h"]):
                overlap = True
    check("no bbox overlap", not overlap)
    check("17 nodes placed", len(nodes) == 17)


def test_roundtrip_and_validation():
    print("round-trip + validation")
    tree = sample_tree()
    back = engine.from_dict(engine.to_dict(tree))
    check("round-trip text", back["children"][1]["children"][0]["text"] == "B1")
    check("round-trip ids", back["children"][1]["id"] == "n3")
    check("empty root rejected",
          engine.check_tree({"id": "x", "text": "  ", "children": []}) is not None)
    check("long label rejected",
          engine.check_tree({"id": "x", "text": "a" * 201, "children": []}) is not None)
    big = {"id": "x", "text": "R", "children": []}
    cur = big
    for _ in range(501):
        nxt = {"id": "y", "text": "c", "children": []}
        cur["children"] = [nxt]
        cur = nxt
    check(">500 nodes rejected", engine.check_tree(big) is not None)
    check("valid tree passes",
          engine.check_tree(engine.to_dict(sample_tree())) is None)


def test_routes():
    print("routes (TestClient)")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from shajra.routes import router
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/shajra")
    check("GET /shajra 200", r.status_code == 200, str(r.status_code))
    check("page mentions Shajra", "Shajra" in r.text)
    check("page states honest limits", "Honest limits" in r.text)
    r = client.post("/shajra/api/outline",
                    data={"text": "R\n  A\n  B\n    B1\n"})
    check("outline endpoint 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        d = r.json()
        check("outline stats", d["stats"] == {"nodes": 4, "depth": 2, "leaves": 2},
              str(d.get("stats")))
    r = client.post("/shajra/api/outline", data={"text": ""})
    check("empty outline 400", r.status_code == 400)
    import json as _json
    tree = sample_tree()
    r = client.post("/shajra/api/layout",
                    data={"payload": _json.dumps(
                        {"tree": engine.to_dict(tree), "mode": "right"})})
    check("layout endpoint 200", r.status_code == 200, str(r.status_code))
    if r.status_code == 200:
        d = r.json()
        check("layout n1 at (0,43.5)",
              close(d["nodes"]["n1"]["x"], 0) and close(d["nodes"]["n1"]["y"], 43.5),
              str(d["nodes"].get("n1")))
    r = client.get("/shajra/api/ai-status")
    check("ai-status 200", r.status_code == 200 and
          "ai_available" in r.json(), str(r.status_code))
    r = client.post("/shajra/api/ai-expand", data={"node": "Beta-lactams"})
    check("ai-expand without key 400", r.status_code == 400,
          str(r.status_code))


if __name__ == "__main__":
    test_outline()
    test_stats()
    test_right_layout()
    test_down_layout()
    test_radial_layout()
    test_no_overlap()
    test_roundtrip_and_validation()
    test_routes()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
