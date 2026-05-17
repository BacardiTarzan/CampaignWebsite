# Rules Glossary — Design Spec
**Date:** 2026-05-17

## Problem

The character sheet has a tooltip system that shows a short rule description on hover and a "Read full rule ›" link. That link calls `openGlossaryModal(slug)`, which opens a modal — but the modal silently does nothing if the glossary map failed to load, and the link always renders even when there's no extra content beyond the short description. Players also have no way to browse rules at their leisure outside the sheet.

## Goals

1. Standalone `/glossary` page players can browse and bookmark.
2. "Read full rule ›" only appears on sheet tooltips when there is genuinely more content to show.
3. Sheet tooltip modal gets a "View in Glossary ↗" link that deep-links to the standalone page.

---

## Backend

No new endpoints needed. `GET /api/content/glossary` already returns all terms with `slug`, `term`, `category`, `short_description`, `full_description`, `ability`. The endpoint is public (no auth dependency).

Add one new route in `app/main.py`:

```python
@app.get("/glossary")
def serve_glossary():
    return FileResponse(str(static_path / "glossary.html"))
```

Requires login (redirect to `/auth/login` on 401 from the JS side, same pattern as lore page).

---

## Glossary data — categories

The seeder populates these categories:

| Category | Display label |
|---|---|
| `combat` | Combat |
| `condition` | Conditions |
| `action` | Actions |
| `weapon_property` | Weapon Properties |
| `mastery` | Masteries |
| `skill` | Skills |

---

## Frontend — new files

### `static/glossary.html`

Two-column layout identical in structure to `lore.html`:

```
┌─────────────────┬──────────────────────────────────┐
│  ← My Characters│  [search bar          ]           │
│  Rules Glossary │                                   │
│  ─────────────  │  Advantage              [combat]  │
│  All            │  You roll twice and take the...   │
│  Combat         │  ▼ (expanded)                     │
│  Conditions     │  Full text of the rule...         │
│  Actions        │                                   │
│  Weapon Props   │  Blinded                [cond.]   │
│  Masteries      │  A Blinded creature can't see...  │
│  Skills         │                                   │
└─────────────────┴──────────────────────────────────┘
```

- Reuses `style.css` + `lore.css` layout variables; own `glossary.css` for term cards.
- Mobile: sidebar collapses behind a "☰ Categories" toggle button (same pattern as lore).

### `static/glossary.js`

- On boot: auth check (`GET /auth/me`), then `GET /api/content/glossary`.
- Renders category filter buttons in sidebar (All + one per category with a count badge).
- Renders term cards in main area — A-Z within the active filter.
- Each card: term name (h3) + category badge, `short_description` always visible, click to expand `full_description` (accordion toggle, arrow indicator).
- Search bar filters by term name and description text (client-side, instant).
- On load: if `window.location.hash` matches a slug, scroll to and expand that card.

### `static/glossary.css`

Term card styles: border-left accent by category color, expand/collapse animation, category badge pills. Reuses CSS variables from `style.css`.

---

## Frontend — portal changes (`portal.html`)

Add a second nav button next to the existing Lore Library:

```html
<a href="/glossary"><button class="btn-secondary">📜 Rules Glossary</button></a>
```

---

## Frontend — sheet.js tooltip fixes

### Fix 1 — hide "Read full rule ›" when no extra content

In `_showGlossPopover`, conditionally render the link:

```js
const hasMore = term.full_description !== term.short_description;
const moreLink = hasMore
  ? `<span class="gloss-popover-more" onclick="openGlossaryModal('${slug}')">Read full rule ›</span>`
  : "";
```

### Fix 2 — add "View in Glossary ↗" inside the modal

In `openGlossaryModal`, add a link in the modal footer:

```html
<a href="/glossary#${slug}" target="_blank" class="gloss-glossary-link">View in Glossary ↗</a>
```

---

## Files changed / created

| File | Change |
|---|---|
| `app/main.py` | Add `GET /glossary` route |
| `static/portal.html` | Add "📜 Rules Glossary" button |
| `static/glossary.html` | New — page shell |
| `static/glossary.js` | New — fetch, filter, render, hash anchor |
| `static/glossary.css` | New — card styles |
| `static/sheet.js` | Fix "Read full rule ›" visibility; add "View in Glossary ↗" in modal |

---

## Out of scope

- Admin CRUD for glossary terms (terms are seeded from reference markdown; no in-app editing planned).
- Adding glossary tooltips to the glossary page itself (avoid recursive nesting).
- Lore page changes — glossary lives at its own URL.
