# CSS Overhaul — Token-First Sweep — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up the Grimoire CSS across wizard, sheet, portal, level-up, and lore pages by enforcing the token system, improving readability, clarifying button hierarchy, and polishing tab navigation — no aesthetic direction change.

**Architecture:** Token-first: add missing tokens to `style.css` first, then propagate fixes through all files. No JS changes. No structural HTML changes. Admin pages excluded.

**Tech Stack:** Plain CSS. Server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`. Visual verification via browser screenshots.

---

## File Map

| File | Changes |
|---|---|
| `static/style.css` | New tokens, readability, button fixes, ribbon-tab gap |
| `static/sheet.css` | Readability, spacing, tab nav polish |
| `static/levelup.css` | Readability, spacing token enforcement |
| `static/lore.css` | Readability, spacing token enforcement |

---

## Task 1: Add missing design tokens to style.css

**Files:** Modify `static/style.css` lines 54–93 (`:root` spacing + compat block)

- [ ] **Step 1: Add `--sp-1h` half-step and green button tokens to `:root`**

In the spacing scale block (after `--sp-1: 4px`), add:
```css
--sp-1h: 6px;
```

After the rubric block, add a green tokens block:
```css
/* ── Verdant (level-up button) ── */
--green-bright: #38904e;
--green:        #2e7a42;
--green-deep:   #1e5a2c;
--green-shadow: #0a2e14;
```

Add tab clip offset token to the radii section:
```css
--tab-clip-offset: 9px;
```

- [ ] **Step 2: Verify tokens are in `:root` and no typos**

Open `static/style.css` and confirm the three additions are present in `:root`.

---

## Task 2: Readability — style.css

**Files:** Modify `static/style.css`

- [ ] **Step 1: Raise body line-height**

Change:
```css
line-height: 1.65;
```
To:
```css
line-height: 1.7;
```

- [ ] **Step 2: Raise button base font-size**

In `button, .btn, .rune-btn` block, change:
```css
font-size: 0.82rem;
```
To:
```css
font-size: 0.84rem;
```

- [ ] **Step 3: Fix `.ribbon-tabs` gap**

Change:
```css
gap: 3px;
```
To:
```css
gap: var(--sp-2);
```
(Both occurrences: `.ribbon-tabs, .tab-bar` in style.css and `.sh-tabs` in sheet.css — sheet.css handled in Task 4)

---

## Task 3: Button fixes — style.css

**Files:** Modify `static/style.css`

- [ ] **Step 1: Differentiate Danger from Primary**

`btn-danger` currently uses identical rubric gradient as `btn-primary`. Change `btn-danger` to a darker, desaturated red so it reads as destructive rather than confirmatory:

```css
button.btn-danger, .btn-danger, .rune-btn--danger {
  background: linear-gradient(180deg, var(--rubric) 0%, var(--rubric-deep) 55%, #3a0808 100%);
  border-color: #2a0606;
  box-shadow: 0 3px 0 #1a0404, 0 5px 16px rgba(0,0,0,0.4);
  color: #f8d0d0;
}
button.btn-danger:hover, .btn-danger:hover, .rune-btn--danger:hover {
  background: linear-gradient(180deg, var(--rubric-bright) 0%, var(--rubric) 55%, var(--rubric-deep) 100%);
}
button.btn-danger:active { box-shadow: none; }
```

- [ ] **Step 2: Fix btn-levelup to use green tokens**

Replace raw hex:
```css
button.btn-levelup {
  background: linear-gradient(180deg, var(--green-bright) 0%, var(--green) 55%, var(--green-deep) 100%);
  border-color: var(--green-deep);
  box-shadow: 0 3px 0 var(--green-shadow), 0 5px 16px rgba(0,0,0,0.4);
  color: #c8f0d4;
}
button.btn-levelup:hover {
  background: linear-gradient(180deg, #42a85e 0%, var(--green-bright) 55%, var(--green) 100%);
}
button.btn-levelup:active { box-shadow: none; }
```

- [ ] **Step 3: Rebuild btn-secondary as self-contained variant**

Replace:
```css
.btn-secondary, .rune-btn--ghost {
  background: transparent;
  border: 1px solid var(--gold-deep);
  color: var(--ink-soft);
  font-family: var(--font-body);
  font-size: 0.95rem;
  text-transform: none;
  letter-spacing: 0;
  min-height: 36px;
  padding: 7px 16px;
}
.btn-secondary:hover, .rune-btn--ghost:hover {
  background: rgba(168,120,43,0.1);
  border-color: var(--gold);
  color: var(--ink);
}
```
With (keep font-body as intentional for secondary/ghost — it's a softer style, but declare it explicitly):
```css
.btn-secondary, .rune-btn--ghost {
  font-family: var(--font-body);
  font-size: 0.95rem;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  padding: var(--sp-2) var(--sp-4);
  min-height: 36px;
  background: transparent;
  border: 1px solid var(--gold-deep);
  color: var(--ink-soft);
  box-shadow: none;
}
.btn-secondary:hover, .rune-btn--ghost:hover {
  background: rgba(168,120,43,0.1);
  border-color: var(--gold);
  color: var(--ink);
  box-shadow: none;
}
```

- [ ] **Step 4: Rebuild btn-logout as self-contained variant**

Replace the existing `.btn-logout` block with:
```css
.btn-logout {
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  padding: var(--sp-1) var(--sp-3);
  min-height: unset;
  background: transparent;
  border: 1px solid rgba(200,168,100,0.35);
  color: var(--light-dim);
  box-shadow: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  text-decoration: none;
  transition: color 0.15s, border-color 0.15s;
}
.btn-logout:hover {
  color: var(--gold-bright);
  border-color: rgba(200,168,100,0.7);
  background: transparent;
  box-shadow: none;
}
```

---

## Task 4: Tab navigation polish — sheet.css

**Files:** Modify `static/sheet.css`

- [ ] **Step 1: Fix `.sh-tabs` gap**

Change:
```css
gap: 3px;
```
To:
```css
gap: var(--sp-2);
```

- [ ] **Step 2: Fix `.sh-tab-btn` padding and font-size**

Replace:
```css
.sh-tab-btn {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  padding: 9px 20px 10px 24px;
  background: var(--leather-warm);
  color: var(--gold);
  border: none;
  border-bottom: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  clip-path: polygon(9px 0, 100% 0, 100% 100%, 0 100%);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.13s, color 0.13s, transform 0.12s;
}
```
With:
```css
.sh-tab-btn {
  font-family: var(--font-display);
  font-size: 0.78rem;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  padding: 10px 20px 10px calc(20px + var(--tab-clip-offset, 9px));
  background: var(--leather-warm);
  color: var(--gold-bright);
  border: none;
  border-bottom: none;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  clip-path: polygon(var(--tab-clip-offset, 9px) 0, 100% 0, 100% 100%, 0 100%);
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.13s, color 0.13s, transform 0.12s;
}
```

- [ ] **Step 3: Fix active tab — add panel connection effect**

Replace `.sh-tab-btn.active`:
```css
.sh-tab-btn.active {
  background: linear-gradient(180deg, var(--gold-bright) 0%, var(--gold) 100%);
  color: var(--ink);
  font-weight: 700;
  transform: translateY(-3px);
  box-shadow: 0 -2px 8px rgba(0,0,0,0.3), 2px 0 6px rgba(0,0,0,0.2);
}
```
With:
```css
.sh-tab-btn.active {
  background: linear-gradient(180deg, var(--gold-bright) 0%, var(--gold) 100%);
  color: var(--ink);
  font-weight: 700;
  transform: translateY(-3px);
  box-shadow: 0 -2px 8px rgba(0,0,0,0.3), 2px 0 6px rgba(0,0,0,0.2);
  border-bottom: 3px solid var(--leather-deep);
  position: relative;
  z-index: 2;
}
```

---

## Task 5: Readability fixes — sheet.css

**Files:** Modify `static/sheet.css`

- [ ] **Step 1: Raise small font sizes in sheet**

Apply the following changes:

`.sh-combat-label`: `0.6rem` → `0.72rem`
`.sh-section-title`: `0.65rem` → `0.72rem`
`.ability-label`: `0.6rem` → `0.72rem`
`.attack-label`: `0.6rem` → `0.72rem`
`.attack-prop, .attack-mastery`: `0.62rem` → `0.7rem`
`.skill-ab`: `0.62rem` → `0.7rem`
`.skill-bonus-tag` (sheet.css instance): `0.62rem` → `0.7rem`
`.feature-badge`: `0.62rem` → `0.7rem`

---

## Task 6: Spacing fixes — sheet.css

**Files:** Modify `static/sheet.css`

- [ ] **Step 1: Replace raw px spacing values with tokens**

Apply the following replacements:

`.sh-header` padding: `24px 28px 18px` → `var(--sp-5) var(--sp-6) var(--sp-4)`
`.sh-combat-cell` gap: `2px` → `var(--sp-1)`
`.sh-tab-panel` padding: `28px 20px` → `var(--sp-6) var(--sp-4)`
`.sh-main` gap: `20px` → `var(--sp-4)`
`.sh-col-left/.sh-col-right` gap: `14px` → `var(--sp-3)`
`.sh-features-section` margin-top: `20px` → `var(--sp-4)`
`.sh-section` padding: `14px 16px` → `var(--sp-3) var(--sp-4)`
`.sh-section-title` margin: `0 0 10px` → `0 0 var(--sp-2)`; padding-bottom: `7px` → `var(--sp-1h)`
`.ability-grid` (sheet) gap: `8px` → `var(--sp-2)` (already aligned, confirm)
`.ability-card` padding: `10px 6px 8px` → `var(--sp-2) var(--sp-1h) var(--sp-2)`
`.ability-label` margin-bottom: `3px` → `var(--sp-1)`
`.attack-cards` gap: `8px` → `var(--sp-2)`
`.attack-card` padding: `10px 14px` → `var(--sp-2) var(--sp-3)`
`.attack-name` margin-bottom: `6px` → `var(--sp-1h)`
`.attack-stats` gap: `16px` → `var(--sp-4)`
`.attack-props` gap: `4px` → `var(--sp-1)`; margin-top: `6px` → `var(--sp-1h)`
`.feature-card` padding: `12px 14px` → `var(--sp-3)`
`.feature-card-header` gap: `10px` → `var(--sp-2)`; margin-bottom: `6px` → `var(--sp-1h)`
`.save-row` gap: `7px` → `var(--sp-2)`; padding: `4px 2px` → `var(--sp-1) 0`

---

## Task 7: Readability + spacing fixes — levelup.css

**Files:** Modify `static/levelup.css`

- [ ] **Step 1: Raise small font sizes in levelup**

`.lu-pip`: `0.65rem` → `0.72rem`
`.lu-pip-sep`: `0.7rem` → `0.72rem`
`.lu-choice-tag`: `0.7rem` → `0.72rem`
`.lu-filter-btn`: `0.7rem` → `0.72rem`
`.ability-name` (in levelup context — `.lu-` scoped): check `.lu-` scoped font sizes < 0.72rem and raise

- [ ] **Step 2: Replace raw px spacing values with tokens**

`.lu-header` padding: `32px 20px 0` → `var(--sp-6) var(--sp-4) 0`
`.lu-subtitle` margin-top: `4px` → `var(--sp-1)`; margin-bottom: `20px` → `var(--sp-4)`
`.lu-steps` gap: `6px` → `var(--sp-1h)`; margin-bottom: `28px` → `var(--sp-5)`
`.lu-panel` padding: `0 20px 60px` → `0 var(--sp-4) var(--sp-8)`
`.lu-step-heading` margin: `0 0 8px` → `0 0 var(--sp-2)`; padding-bottom: `10px` → `var(--sp-2)`
`.lu-step-desc` margin: `0 0 20px` → `0 0 var(--sp-4)`
`.lu-features-list` gap: `14px` → `var(--sp-3)`; margin-bottom: `28px` → `var(--sp-5)`
`.lu-feature-card` padding: `16px 18px` → `var(--sp-4)`
`.lu-feature-name` margin-bottom: `6px` → `var(--sp-1h)`
`.lu-feature-choice` gap: `8px` → `var(--sp-2)`; margin-top: `10px` → `var(--sp-2)`
`.lu-subclass-grid` gap: `14px` → `var(--sp-3)`; margin-bottom: `28px` → `var(--sp-5)`
`.lu-subclass-card` padding: `16px` → `var(--sp-4)`
`.lu-subclass-name` margin-bottom: `6px` → `var(--sp-1h)`
`.lu-spell-filter` gap: `8px` → `var(--sp-2)`; margin-bottom: `14px` → `var(--sp-3)`
`.lu-spell-grid` gap: `10px` → `var(--sp-2)`; margin-bottom: `28px` → `var(--sp-5)`
`.lu-no-features` padding: `20px 0` → `var(--sp-4) 0`

---

## Task 8: Readability + spacing fixes — lore.css

**Files:** Modify `static/lore.css`

- [ ] **Step 1: Raise small font sizes in lore**

`.lore-back`: `0.7rem` → `0.72rem`
`.lore-nav-category`: `0.62rem` → `0.72rem`

- [ ] **Step 2: Replace raw px spacing values with tokens**

`.lore-sidebar-header` padding: `18px 18px 14px` → `var(--sp-4) var(--sp-4) var(--sp-3)`
`.lore-back` margin-bottom: `10px` → `var(--sp-2)`
`#lore-nav` padding: `8px 0 24px` → `var(--sp-2) 0 var(--sp-5)`
`.lore-nav-group` margin-bottom: `6px` → `var(--sp-1h)`
`.lore-topbar` padding: `8px 24px` → `var(--sp-2) var(--sp-5)`
`.lore-welcome` padding-top: `32px` → `var(--sp-6)`
`.lore-welcome h1` margin-bottom: `14px` → `var(--sp-3)`; padding-bottom: `12px` → `var(--sp-3)`
`.lore-md p` margin: `0 0 18px` → `0 0 var(--sp-4)`
`.lore-md blockquote` padding: `10px 20px` → `var(--sp-2) var(--sp-4)`; margin: `0 0 18px` → `0 0 var(--sp-4)`
`.lore-md h1` margin: `0 0 24px` → `0 0 var(--sp-5)`; padding-bottom: `10px` → `var(--sp-2)`
`.lore-md h2` margin: `36px 0 10px` → `var(--sp-6) 0 var(--sp-2)`; padding-bottom: `5px` → `var(--sp-1)`
`.lore-md h3` margin: `28px 0 8px` → `var(--sp-5) 0 var(--sp-2)`
`.lore-md hr` margin: `32px 0` → `var(--sp-6) 0`
`.lore-md ul, .lore-md ol` margin-bottom: `18px` → `var(--sp-4)`
`.lore-md li` margin-bottom: `7px` → `var(--sp-1h)`

---

## Task 9: Visual verification and bug fixes

**Steps:**
- [ ] Start local server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] Take screenshots of: portal, wizard (step 1), character sheet (all 4 tabs), level-up, lore
- [ ] Check: readability of small text, spacing rhythm, button distinction, tab connection effect
- [ ] Fix any regressions found
