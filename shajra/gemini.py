"""Shajra AI layer — optional Gemini calls: expand one node into
sub-branches, or generate a whole map from a topic.

Same call pattern as the other gap builds: urllib, key read from the
environment AT CALL TIME only, never stored or logged. The AI is a
convenience only — the deterministic core (outline import, manual
editing, three layouts, free exports) works at 100% without a key,
and when the key is quota-exhausted the page says so instead of
failing the map (lesson from the 2026-11-01 Tahqeeq deploy, where
Deep mode 429'd on the shared deployed key).
"""
import json
import os
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
TIMEOUT = 120
MAX_EXPAND = 8


def _get_key():
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_APIkey")


def key_available() -> bool:
    return bool(_get_key())


def _call(prompt):
    key = _get_key()
    if not key:
        return None, ("AI ke liye GEMINI_API_KEY set nahi hai. "
                      "Map phir bhi poora kaam karta hai — outline "
                      "paste karke ya haath se branches banayein.")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODEL}:generateContent?key={key}")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, f"Gemini HTTP {e.code}: {e.read()[:200].decode(errors='replace')}"
    except Exception as e:
        return None, f"Gemini request failed: {type(e).__name__}: {e}"
    try:
        return body["candidates"][0]["content"]["parts"][0]["text"], None
    except (KeyError, IndexError, TypeError):
        return None, "Gemini returned an unexpected response."


def _clean_lines(text, limit):
    items = []
    for raw in (text or "").splitlines():
        line = raw.strip().lstrip("-*•0123456789. ").strip()
        if line and len(line) <= 80 and line not in items:
            items.append(line)
        if len(items) >= limit:
            break
    return items


def expand_node(node_text, path, language="en"):
    """Return (children, error): 4-8 sub-topic labels for one node."""
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    context = " > ".join(path) if path else node_text
    prompt = (
        "Break this mind-map node into 4 to 8 short sub-topics "
        f"{lang_note}. Reply with ONLY one sub-topic per line, no "
        "numbering, no bullets, no explanation. Each sub-topic at most "
        "6 words. Use only real, correct facts — do not invent names, "
        "numbers or claims.\n\nNode: " + context)
    text, err = _call(prompt)
    if err:
        return None, err
    items = _clean_lines(text, MAX_EXPAND)
    if len(items) < 2:
        return None, "Gemini ne usable branches nahi diye — dobara try karein."
    return items, None


def map_from_topic(topic, language="en"):
    """Return (outline_text, error): an indented outline for the topic,
    so the deterministic parser can turn it into a map."""
    lang_note = {"en": "in English", "roman": "in Roman-Urdu",
                 "ur": "in Urdu script"}.get(language, "in English")
    prompt = (
        "Make a mind-map outline for this topic " + lang_note + ". "
        "Reply with ONLY an indented outline: the topic on the first "
        "line, then 4 to 6 main branches indented by two spaces, each "
        "with 2 to 4 sub-branches indented by four spaces. No numbering, "
        "no bullets, no explanation. Use only real, correct facts — do "
        "not invent names, numbers or claims.\n\nTopic: " + topic)
    text, err = _call(prompt)
    if err:
        return None, err
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    if len(lines) < 3:
        return None, "Gemini ne usable outline nahi diya — dobara try karein."
    return "\n".join(lines), None
