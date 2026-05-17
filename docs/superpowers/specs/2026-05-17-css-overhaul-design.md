# CSS Overhaul — Token-First Sweep
**Date:** 2026-05-17
**Scope:** style.css, sheet.css, levelup.css, lore.css (admin excluded)
**Approach:** Token-first sweep — fix design tokens and propagate; no aesthetic direction change, no structural rewrite.

---

## Goals

- Improve readability: raise minimum font sizes, improve body copy spacing
- Enforce spacing rhythm: replace ad-hoc raw px values with design tokens
- Clarify button hierarchy: distinguish Primary from Danger, clean up variant inconsistencies
- Polish tab navigation: fix padding math, improve contrast, add active-tab panel connection

---

## Section 1 — Readability

### Problem
Several text sizes fall below comfortable reading threshold:
- `.sh-combat-label` — `0.6rem`
- `.sh-section-title` — `0.65rem`
- `.sh-tab-btn` — `0.72rem`
- Button base — `0.82rem`

### Fix
- Minimum `0.72rem` for purely decorative micro-labels (e.g. combat stat labels)
- Minimum `0.78rem` for interactive labels (tabs, buttons)
- Minimum `0.875rem` for anything conveying actual content
- Body `line-height`: `1.65` → `1.7`
- Slightly increase paragraph spacing inside sheet parchment panels

### Files affected
`style.css`, `sheet.css`

---

## Section 2 — Spacing

### Problem
The 8-base spacing scale (`--sp-1` through `--sp-8`) exists but is bypassed throughout with raw px values that don't align to the scale:
- `.sh-section` padding: `14px 16px`
- `.sh-header`: `24px 28px 18px`
- `.sh-combat-cell` gap: `2px`
- `.sh-tab-panel`: `28px 20px`
- Various `gap: 14px`, `margin-top: 20px`, `3px` tab gaps

### Fix
- Add `--sp-1h: 6px` half-step token (between sp-1 and sp-2) to `:root` in `style.css`
- Audit every raw px spacing value in all 4 files and replace with nearest token
- No visual redesign — enforce the existing intended rhythm

### Files affected
`style.css`, `sheet.css`, `levelup.css`, `lore.css`

---

## Section 3 — Button Styles

### Problem
1. **Primary and Danger are visually identical** — both use rubric red gradient; player can't distinguish confirm from delete without reading the label
2. **Inconsistent construction:**
   - `btn-levelup` uses raw hex colors (`#2e7a42`, `#1e5a2c`, etc.) instead of tokens
   - `btn-logout` overrides `min-height`, `text-transform`, `letter-spacing` to escape the base style rather than being a clean self-contained variant
   - `btn-secondary` switches to `font-body` instead of `font-display`, inconsistent with the rest of the system

### Fix
- Keep all existing button colors; differentiate Danger from Primary: Danger gets darker, slightly desaturated red; Primary stays brighter
- Extract `btn-levelup` raw hex values into CSS custom properties (`--green-bright`, `--green`, `--green-deep`, `--green-shadow`) added to `:root`
- Rebuild `btn-logout` as a self-contained variant without fighting the base style
- Rebuild `btn-secondary` to use `font-display` consistently, or explicitly declare it a body-font variant with clear intent

### Files affected
`style.css`

---

## Section 4 — Tab Navigation (Aesthetic)

### Problem
The sheet tabs (`clip-path` diagonal bookmark style) are directionally correct but have rough edges:
- Asymmetric padding (`9px 20px 10px 24px`) compensates for the clip-path offset — fragile and hard to maintain
- `3px` gap between tabs feels cramped
- Inactive tab state (`leather-warm` bg, `gold` text) is low contrast — hard to tell active from inactive at a glance
- No visual connection between active tab and the content panel below

### Fix
- Introduce `--tab-clip-offset` custom property to make clip-path offset explicit and padding symmetric
- Widen tab gap to `--sp-2` (8px)
- Boost inactive tab contrast: raise inactive text from `gold` to `gold-bright`
- Add bottom-flush effect on active tab (remove or match border-bottom) so it reads as connected to the content below it

### Files affected
`sheet.css`

---

## Out of Scope
- Admin pages (`admin.html`, `admin.js`, `admin.css`)
- Any functional/JS changes
- New pages or components
- Aesthetic direction change (staying Grimoire)
- Phase 4 spellcasting work
