"""Shajra routes — free AI mind-map studio (Xmind gap build).

Original clean-room build. Not affiliated with Xmind. Stateless:
nothing is stored server-side; maps live in the user's own browser
(localStorage). No account, no card, no subscription, no usage meter,
no map limit, no watermarked exports.

The server only parses outlines, computes deterministic layouts and
offers optional Gemini expansion. The map itself is drawn in the
browser from the layout coordinates.
"""
import json

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, JSONResponse

from . import engine, gemini
from .pages import SHAJRA_HTML

router = APIRouter(prefix="/shajra")


@router.get("", response_class=HTMLResponse)
def index():
    return SHAJRA_HTML


@router.post("/api/outline")
async def outline(text: str = Form("")):
    tree, err = engine.parse_outline(text)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "tree": engine.to_dict(tree),
            "stats": engine.stats(tree)}


@router.post("/api/layout")
async def layout(payload: str = Form("{}")):
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return JSONResponse({"ok": False, "error": "Invalid map JSON."},
                            status_code=400)
    tree = data.get("tree", data)
    mode = data.get("mode", "right")
    err = engine.check_tree(tree)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    if engine.count_nodes(tree) > 500:
        return JSONResponse({"ok": False, "error": "Maps are limited to 500 nodes."},
                            status_code=400)
    tree = engine.from_dict(tree)
    result = engine.layout(tree, mode)
    result["ok"] = True
    result["stats"] = engine.stats(tree)
    return result


@router.get("/api/ai-status")
def ai_status():
    return {"ai_available": gemini.key_available()}


@router.post("/api/ai-expand")
async def ai_expand(node: str = Form(""), path: str = Form(""),
                     language: str = Form("en")):
    if not node.strip():
        return JSONResponse({"ok": False, "error": "Node label missing."},
                            status_code=400)
    path_list = [p for p in path.split(" > ") if p] if path else [node]
    children, err = gemini.expand_node(node.strip(), path_list, language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "children": children}


@router.post("/api/ai-map")
async def ai_map(topic: str = Form(""), language: str = Form("en")):
    if not topic.strip():
        return JSONResponse({"ok": False, "error": "Topic missing."},
                            status_code=400)
    if len(topic) > 200:
        return JSONResponse({"ok": False, "error": "Topic too long."},
                            status_code=400)
    outline_text, err = gemini.map_from_topic(topic.strip(), language)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    tree, err = engine.parse_outline(outline_text)
    if err:
        return JSONResponse({"ok": False, "error": err}, status_code=400)
    return {"ok": True, "tree": engine.to_dict(tree),
            "stats": engine.stats(tree), "outline": outline_text}
