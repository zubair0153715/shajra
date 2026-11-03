# Shajra — Free AI Mind Maps

**Shajra** (شجرہ — tree / branching diagram) is a free, unlimited AI
mind-map studio. It is an original clean-room build, **not affiliated
with Xmind**. Live at
https://clinic-demo.fastapicloud.dev/shajra

## The gap it fills (Xmind, Nov 2026)

Xmind 2027 launched on Product Hunt on 3 Nov 2026 as "an AI thinking
partner" — but the AI is a meter, not a feature: Free and Pro
($59/yr) get **10 AI credits**, Premium ($99/yr) gets 500/month. The
free tier caps at **10 online maps** with **watermarked exports**;
PDF/SVG export, custom themes and unlimited slides are paywalled; and
there is no student plan. Full gap report:
`../market-gaps/daily/2026-11-03-shajra.md` (in the builder's notes).

## What Shajra does

- **Free unlimited maps** — no account, no card, no meter, no 10-map
  cap. Maps live in your browser (localStorage).
- **AI expand + AI map-from-topic** — one Gemini call per action, only
  when the server key is available. When the key is quota-exhausted
  the button says so honestly and the map keeps working.
- **Clean exports, free** — SVG and PNG with **no watermark**, plus
  JSON save/load.
- **Three layouts** — right-tree, down-tree (org chart), radial —
  switchable per map. Collapse/expand branches, presentation
  walkthrough, focus mode.
- **Outline import** — paste an indented outline and get a map
  instantly; the deterministic core that never needs AI.
- **Urdu-first** — Urdu script, Roman-Urdu and English; sample maps
  for a Pharm-D student (Antibiotics; MDCAT Biology).

## Honest limits

- Maps are stored in the browser only — no cloud sync, no real-time
  collaboration in v1.
- AI features need server Gemini quota.
- Layout is automatic — no free-form drag-to-anywhere in v1.
- Export is SVG/PNG/JSON, not PDF.

## Verify

```bash
~/workspace/.venv-fc/bin/python tests/verify.py
```

Hand-computed layout expectations (right/down/radial coordinates,
no-overlap), outline parsing, JSON round-trip, tree validation, and
HTTP routes via TestClient.

## Structure

```
shajra/
  engine.py   tree model, outline parser, 3 deterministic layouts
  gemini.py   optional AI expand / map-from-topic (urllib, key at call time)
  pages.py    interactive SVG mind-map studio (single HTML page)
  routes.py   FastAPI routes: /shajra, /api/outline, /api/layout,
              /api/ai-status, /api/ai-expand, /api/ai-map
tests/
  verify.py   verification suite
```

## Deploy

Part of the `clinic-demo` FastAPI Cloud app (`app/shajra/`); see its
README for the deploy + backup procedure.
