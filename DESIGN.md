---
name: TechISOlutions
description: Clasificación ISO 45001 como registro de inspección en campo — papel formulario, sellos y trazabilidad normativa.
colors:
  paper: "#f4f0e6"
  paper-ink: "#2a2520"
  institutional: "#1a3a5c"
  sst-yellow: "#f0c419"
  stamp-red: "#c0392b"
  carbon: "#2c5282"
  card: "#faf8f3"
  muted: "#ebe6dc"
  muted-foreground: "#5c5348"
  border: "#c9c0b4"
  secondary: "#e8e2d6"
typography:
  display:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "clamp(1.875rem, 5vw, 2.5rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  headline:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.25
  title:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.35
  body:
    fontFamily: "Source Sans 3, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.625
  label:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.625rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.05em"
rounded:
  sm: "0.15rem"
  md: "0.2rem"
  lg: "0.25rem"
spacing:
  sm: "0.5rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2rem"
components:
  button-cta:
    backgroundColor: "{colors.sst-yellow}"
    textColor: "{colors.institutional}"
    rounded: "{rounded.lg}"
    padding: "10px 20px"
  button-cta-hover:
    backgroundColor: "{colors.sst-yellow}"
    textColor: "{colors.institutional}"
    rounded: "{rounded.lg}"
    padding: "10px 20px"
  button-primary:
    backgroundColor: "{colors.institutional}"
    textColor: "#f8f6f0"
    rounded: "{rounded.lg}"
    padding: "6px 12px"
  button-secondary:
    backgroundColor: "{colors.card}"
    textColor: "{colors.institutional}"
    rounded: "{rounded.lg}"
    padding: "10px 20px"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.paper-ink}"
    rounded: "{rounded.lg}"
    padding: "10px 12px"
  category-badge:
    backgroundColor: "{colors.institutional}"
    textColor: "#f8f6f0"
    rounded: "{rounded.sm}"
    padding: "2px 8px"
---

# Design System: TechISOlutions

## Overview

**Creative North Star: "Registro de inspección en campo"**

TechISOlutions looks like an SST coordinator’s clipboard brought to screen: cream form paper, institutional blue ink, yellow hazard tape accents, and red approval stamps. Classification is framed as inspection and traceability — not generic SaaS dashboards. Every surface reads as a formulario normativo with IDs, revision numbers, and check cells.

The visual world commits to office-grade sans typography for prose and monospace for metadata (form codes, probabilities, dates). Corners stay nearly square; depth comes from hard offset shadows and 2px borders, not soft elevation. Motion is minimal: a slight lift on hover (`translateY(-1px)`) on stamps and CTAs.

**Key Characteristics:**

- Papel formulario crema (`#f4f0e6`) as default ground; cards slightly lighter (`#faf8f3`)
- Azul institucional (`#1a3a5c`) for headings, borders, and primary actions
- Franja SST amarilla (`#f0c419`) for tape strips, primary CTAs, and active pipeline steps
- Sellos rojos (`#c0392b`) for destructive states, nav active underline, and approval accents
- Source Sans 3 for UI text; JetBrains Mono for labels, IDs, stats, and form codes
- `border-2` + `stamp-shadow` instead of rounded cards and diffuse shadows
- ISO category badges with fixed color mapping per document type

## Colors

A warm paper palette with institutional blue authority and SST safety signaling (yellow + red).

### Primary

- **Institutional Blue** (`#1a3a5c`): Headings, primary borders, nav chrome, default stamp borders, primary text mode buttons, and checklist cells when checked. The dominant structural ink.
- **Carbon Blue** (`#2c5282`): Focus rings, text links, secondary accent for interactive hints and ring tokens.

### Secondary

- **SST Yellow** (`#f0c419`): Primary CTAs, tape strips, active pipeline stage highlight, accent backgrounds at low opacity. Safety signaling — not decorative fill.

### Tertiary

- **Stamp Red** (`#c0392b`): Errors, required field asterisks, destructive actions, active nav underline, result panels with approval framing. Used sparingly as stamp ink.

### Neutral

- **Paper Cream** (`#f4f0e6`): Page background (`--background`).
- **Paper Ink** (`#2a2520`): Body text (`--foreground`).
- **Card Warm White** (`#faf8f3`): Form surfaces and header bar.
- **Muted Wash** (`#ebe6dc`): Sidebar nav background, keyword chips, secondary fills.
- **Muted Brown-Gray** (`#5c5348`): Secondary text, hints, inactive pipeline steps.
- **Border Tan** (`#c9c0b4`): Default borders, ruled lines, table dividers.
- **Secondary Tan** (`#e8e2d6`): Hover fills on secondary buttons and stat cells.

### Named Rules

**The Tape Accent Rule.** Yellow appears on tape strips, primary CTAs, and one active state per control group — never as large background fields except the demo banner stripe.

**The Stamp Rarity Rule.** Red is stamp ink: errors, approval accents, and a single nav active marker. It should not compete with institutional blue on the same row.

## Typography

**Display Font:** Source Sans 3 (with system-ui, sans-serif)
**Body Font:** Source Sans 3 (with system-ui, sans-serif)
**Label/Mono Font:** JetBrains Mono (with ui-monospace, monospace)

**Character:** Office sans for clarity under audit conditions; mono for anything that must be scanned, copied, or traced (form IDs, probabilities, dates).

### Hierarchy

- **Display** (700, `clamp(1.875rem–2.5rem)`, 1.2): Landing hero and major page titles. Institutional blue, tight leading.
- **Headline** (700, 1.5rem / `text-2xl`, 1.25): Section headings (`h2`) inside app surfaces.
- **Title** (600, 1rem / `text-base`, 1.35): Card titles, document names, semibold labels.
- **Body** (400, 0.875rem / `text-sm`, 1.625): Default UI copy; max ~65ch in descriptive paragraphs.
- **Label** (700 mono, 0.625rem / `text-[10px]`, uppercase, `tracking-wider`): Form field labels, form codes (`Form. IMP-01`), metadata lines.

### Named Rules

**The Mono Metadata Rule.** Probabilities, dates, document IDs, form revision codes, and table column headers use JetBrains Mono. Prose descriptions stay in Source Sans 3.

## Layout

**Container:** `max-w-6xl` centered with `mx-auto`. Main content padding `px-4 py-6` (sm: `px-6 py-8`).

**App shell:** Header (card bg, `border-b-2 institutional`) → optional demo banner → nav (`border-b-2`, sidebar muted bg) → main.

**Density:** Operate surfaces favor compact tables and form stacks (`space-y-5` in forms). Landing uses more vertical breathing (`py-10–14` on sections).

**Responsive:** Desktop nav is horizontal tabs with bottom border active state. Mobile nav is horizontal scroll chips (`text-xs`, icon + label). Pipeline steps grid 2×2 on small screens, inline row on `sm+`.

**Spacing rhythm:** 2px borders define structure; internal padding typically `p-4` / `p-6` / `p-8` on form paper. Gap scale: `gap-2` (tight), `gap-3–4` (default), `gap-6` (section breaks).

## Elevation & Depth

Hybrid: mostly flat tonal layering (paper → card → muted) with **hard offset shadows** on interactive stamps. No diffuse Material-style elevation on cards at rest.

### Shadow Vocabulary

- **Stamp shadow** (`box-shadow: 2px 3px 0 color-mix(institutional 35%, transparent)`): CTAs, mode toggles, stamp actions. Reads as ink stamp offset.
- **Form paper shadow** (`4px 4px 0 rgba(26,58,92,0.12)`): `FormPaper` containers — document on clipboard.
- **Tape strip shadow** (`0 1px 2px rgb(0 0 0 / 12%)`): Subtle lift on yellow tape labels.
- **Clipboard clip** (gradient metal bar + `shadow-md`): Physical clip metaphor on dashboard action bar only.

### Named Rules

**The Flat-By-Default Rule.** Surfaces are flat at rest. Depth appears on hover (translate + stamp shadow) or on `FormPaper` containers — not on every card.

## Shapes

Nearly square geometry: base `--radius: 0.25rem` (4px). Chips and badges use minimal radius; the system avoids pill shapes and large rounded corners.

**Borders:** `border-2` is the default structural weight on headers, forms, tables, stamps, and inputs. `border` (1px) only on inner chips and keyword tags.

**Form language:** Ruled paper (`ruled-paper` utility) — horizontal lines every `1.75rem` on cream card. Dashed `border-2` for file drop zones.

**Silhouettes:** Rectangular stamps, square check cells (`size-8`), rectangular category badges (uppercase, no pill).

## Components

Tactile form stamps: confident borders, bold labels, mono metadata.

### Buttons

- **Shape:** Near-square corners (`0.25rem` radius); reads rectangular.
- **Primary CTA:** SST yellow fill, institutional blue text, `border-2 border-institutional`, `stamp-shadow`, bold `text-sm`, padding `py-2.5 px-5`. Used for “Crear cuenta”, “Procesar, clasificar y guardar”.
- **Primary (ink):** Institutional fill, cream foreground — mode toggle “Texto RAW” when active, mobile nav active chip.
- **Secondary:** Card background, institutional border and text; hover `bg-secondary/60`.
- **Hover / Focus:** `hover:-translate-y-px` on stamps; inputs use `focus-visible:border-carbon` + `ring-2 ring-carbon/25`.

### Chips

- **Category badges:** Uppercase bold `text-[11px]`, `border border-institutional/20`, fixed palette per ISO category (institutional, carbon, sst-yellow, secondary, stamp-red).
- **Keyword tags:** `border border-border`, muted bg, mono `text-[10px–xs]`, no fill color coding.

### Cards / Containers

- **FormPaper:** `ruled-paper`, `border-2 border-institutional`, offset shadow `4px 4px 0`. Primary document surface.
- **Stat / document cards:** `border-2 border-border`, `bg-card`, hover `border-institutional`.
- **Internal padding:** `p-4` default, `p-6–8` for primary forms.

### Inputs / Fields

- **Style:** `border-2`, paper background, `text-sm`, no default ring until focus.
- **Labels:** Mono uppercase `text-[10px]`, institutional color, required `*` in stamp red.
- **Focus:** Carbon border + `ring-2 ring-carbon/25`.
- **Error:** Stamp red border + red ring; error text `text-xs font-medium text-stamp-red`.

### Navigation

- **Header:** Card bg, institutional bottom border, wordmark + optional tape strip “ISO 45001”.
- **Desktop nav:** Muted sidebar bg, tab links with `border-b-2`; active = stamp red bottom border + institutional text.
- **Mobile nav:** Horizontal scroll chips; active = institutional fill + cream text.

### Pipeline Steps (signature)

Four-step import flow: Recibir → Procesar → Clasificar → Guardar. Numbered mono cells; done = institutional fill + checkmark; active = sst-yellow cell; pending = border-border muted.

### Clipboard Clip Bar (signature)

Dashboard action hub: metal gradient clip centered above a bordered tray; contains `StampAction` links (default / yellow / red tones).

## Do's and Don'ts

Concrete guardrails from the implemented clipboard world.

### Do:

- **Do** use `FormPaper` for any surface that represents a document or formulario being filled.
- **Do** show form codes (`Form. IMP-01`, `Form. REP-01`) in mono uppercase above page titles.
- **Do** map ISO categories to `CategoryBadge` colors — never invent ad hoc badge colors per screen.
- **Do** express ML output with visible probability in mono bold (`NN% confianza` / `NN% probabilidad`).
- **Do** keep Spanish copy professional and compliance-oriented (SST, ISO 45001, trazabilidad).

### Don't:

- **Don't** use large border-radius, pill buttons, or glassmorphism — this is field paperwork, not consumer SaaS.
- **Don't** use purple gradients, generic “AI sparkle” palettes, or dark-mode-first layouts (light is default).
- **Don't** hide the import pipeline — file and RAW flows must show Recibir → Procesar → Clasificar → Guardar when processing.
- **Don't** fabricate social proof, certification claims, or production metrics in UI chrome.
- **Don't** use “TechContent AI” in user-facing strings — product name is **TechISOlutions**.
