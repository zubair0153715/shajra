"""Shajra engine — original clean-room mind-map core.

A map is a plain tree: {"id": "n1", "text": "...", "children": [...]}.
The engine parses indented outlines into trees, counts and measures
them, and computes deterministic node coordinates for three layouts
(right-tree, down-tree, radial) using fixed-size node boxes, so the
layout is exactly verifiable by hand (see tests/verify.py).

No Xmind code, format, theme or asset is used. Shajra is not affiliated
with Xmind.
"""

NODE_W = 180
NODE_H = 42
H_GAP = 70   # horizontal gap between depth columns (right/down layouts)
V_GAP = 16   # vertical gap between sibling subtrees
R_STEP = 170  # radial distance per depth level (radial layout)
PAD = 30

_id_counter = [0]


def _new_id():
    _id_counter[0] += 1
    return f"n{_id_counter[0]}"


def reset_ids():
    _id_counter[0] = 0


def make_node(text, children=None):
    return {"id": _new_id(), "text": text, "children": children or []}


def count_nodes(node):
    # Iterative: deep chains must not blow the recursion limit.
    total = 0
    stack = [node]
    while stack:
        current = stack.pop()
        total += 1
        stack.extend(current["children"])
    return total


def max_depth(node):
    deepest = 0
    stack = [(node, 0)]
    while stack:
        current, depth = stack.pop()
        deepest = max(deepest, depth)
        stack.extend((c, depth + 1) for c in current["children"])
    return deepest


def leaf_count(node):
    total = 0
    stack = [node]
    while stack:
        current = stack.pop()
        if not current["children"]:
            total += 1
        stack.extend(current["children"])
    return total


def find_node(node, node_id):
    if node["id"] == node_id:
        return node
    for child in node["children"]:
        found = find_node(child, node_id)
        if found is not None:
            return found
    return None


def to_dict(node):
    return {"id": node["id"], "text": node["text"],
            "children": [to_dict(c) for c in node["children"]]}


def from_dict(data):
    node = {"id": data["id"], "text": data["text"], "children": []}
    for child in data.get("children", []):
        node["children"].append(from_dict(child))
    return node


def check_tree(data, depth=0):
    """Validate a client-supplied tree. Returns an error string or None.

    Depth-capped recursion: a chain deeper than 500 is rejected before
    it can grow the stack, and the total-node cap is enforced once by
    the caller (see routes) with the iterative count_nodes.
    """
    if not isinstance(data, dict):
        return "Map data must be an object."
    if not isinstance(data.get("text"), str) or not data["text"].strip():
        return "Root node needs a label."
    if len(data["text"]) > 200:
        return "Node labels are at most 200 characters."
    if not isinstance(data.get("children", []), list):
        return "Children must be a list."
    if depth > 500:
        return "Maps are limited to 500 nodes."
    for child in data.get("children", []):
        err = check_tree(child, depth + 1)
        if err:
            return err
    return None


# ---------------------------------------------------------------- outline
def _indent_level(line):
    """Indent level: one tab = 1, two spaces = 1. Returns (level, text)."""
    stripped = line.lstrip(" \t")
    if not stripped:
        return None
    prefix = line[:len(line) - len(stripped)]
    level = prefix.count("\t") + len(prefix.replace("\t", "")) // 2
    text = stripped
    for marker in ("- ", "* ", "+ ", "• "):
        if text.startswith(marker):
            text = text[len(marker):]
            break
    # "1. " numbered items
    if len(text) >= 3 and text[0].isdigit() and text[1] == "." and text[2] == " ":
        text = text[3:]
    return level, text.strip()


def parse_outline(text):
    """Parse an indented outline into a tree.

    Rules: first level-0 line is the root; extra level-0 lines become
    children of the root; deeper lines attach to the nearest shallower
    ancestor; blank lines are skipped; a line may not jump more than
    one level deeper than its parent (it is clamped to parent+1).
    Returns (tree, error). Error is None on success.
    """
    lines = []
    for raw in (text or "").splitlines():
        parsed = _indent_level(raw)
        if parsed and parsed[1]:
            lines.append(parsed)
    if not lines:
        return None, "Outline is empty — likhain ya paste karein."
    if len(lines) > 500:
        return None, "Outline is limited to 500 lines."
    reset_ids()
    root_level, root_text = lines[0]
    root = make_node(root_text)
    stack = [(root_level, root)]
    for level, label in lines[1:]:
        if level <= root_level:
            parent = root
            parent_level = root_level
        else:
            while stack and stack[-1][0] >= level:
                stack.pop()
            if not stack:
                parent_level, parent = root_level, root
            else:
                parent_level, parent = stack[-1]
            level = parent_level + 1  # clamp jumps to one level deeper
        node = make_node(label)
        parent["children"].append(node)
        stack.append((level, node))
    return root, None


# ---------------------------------------------------------------- layout
def _assign_y(node, depth, pos, counter):
    """Post-order y assignment for right/down layouts.

    Leaves take the next vertical slot; a parent sits at the midpoint
    of its first and last child. Returns the node's y (top edge).
    """
    if not node["children"]:
        y = counter[0] * (NODE_H + V_GAP)
        counter[0] += 1
        pos[node["id"]] = (depth * (NODE_W + H_GAP), y, depth)
        return y
    child_ys = [_assign_y(c, depth + 1, pos, counter)
                for c in node["children"]]
    y = (child_ys[0] + child_ys[-1]) / 2
    pos[node["id"]] = (depth * (NODE_W + H_GAP), y, depth)
    return y


def _collect_angles(node, angles, leaf_index, total_leaves):
    import math
    if not node["children"]:
        angle = (leaf_index[0] + 0.5) * (2 * math.pi / total_leaves)
        leaf_index[0] += 1
        angles[node["id"]] = angle
        return angle
    sin_sum = cos_sum = 0.0
    for child in node["children"]:
        a = _collect_angles(child, angles, leaf_index, total_leaves)
        sin_sum += math.sin(a)
        cos_sum += math.cos(a)
    angle = math.atan2(sin_sum, cos_sum)
    if angle < 0:
        angle += 2 * math.pi
    angles[node["id"]] = angle
    return angle


def layout(tree, mode="right"):
    """Compute coordinates. Returns {"nodes": {id: {...}}, "edges": [...],
    "width": w, "height": h}. Coordinates are the top-left corner of
    each node's fixed NODE_W x NODE_H box."""
    if mode not in ("right", "down", "radial"):
        mode = "right"
    nodes = {}
    edges = []

    def walk(node):
        for child in node["children"]:
            edges.append((node["id"], child["id"]))
            walk(child)

    walk(tree)
    if mode == "radial":
        import math
        total = leaf_count(tree)
        angles = {}
        _collect_angles(tree, angles, [0], total)
        raw = {}
        for node_id, angle in angles.items():
            node = find_node(tree, node_id)
            depth = _depth_of(tree, node_id)
            r = depth * R_STEP
            raw[node_id] = (r * math.cos(angle), r * math.sin(angle))
        min_x = min(x for x, _ in raw.values())
        min_y = min(y for _, y in raw.values())
        for node_id, (x, y) in raw.items():
            nodes[node_id] = {
                "x": round(x - min_x + PAD - NODE_W / 2, 2),
                "y": round(y - min_y + PAD - NODE_H / 2, 2),
                "w": NODE_W, "h": NODE_H,
                "depth": _depth_of(tree, node_id),
            }
        width = round(max(n["x"] for n in nodes.values()) + NODE_W + PAD, 2)
        height = round(max(n["y"] for n in nodes.values()) + NODE_H + PAD, 2)
        return {"nodes": nodes, "edges": edges, "width": width,
                "height": height}

    pos = {}
    _assign_y(tree, 0, pos, [0])
    for node_id, (a, b, depth) in pos.items():
        if mode == "right":
            x, y = a, b
        else:  # down: transpose
            x, y = b, a
        nodes[node_id] = {"x": round(x, 2), "y": round(y, 2),
                          "w": NODE_W, "h": NODE_H, "depth": depth}
    width = round(max(n["x"] for n in nodes.values()) + NODE_W + PAD, 2)
    height = round(max(n["y"] for n in nodes.values()) + NODE_H + PAD, 2)
    return {"nodes": nodes, "edges": edges, "width": width, "height": height}


def _depth_of(tree, node_id, depth=0):
    if tree["id"] == node_id:
        return depth
    for child in tree["children"]:
        d = _depth_of(child, node_id, depth + 1)
        if d is not None:
            return d
    return None


def stats(tree):
    return {"nodes": count_nodes(tree), "depth": max_depth(tree),
            "leaves": leaf_count(tree)}
