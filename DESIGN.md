---
name: AIID Expert Search
description: A sage paper workspace for evidence-based expert comparison.
colors:
  ink: "#233c34"
  primary: "#154d40"
  primary-hover: "#0a382d"
  muted: "#5e7169"
  canvas: "#f5f7f4"
  surface: "#fff"
  sidebar: "#edf2ec"
  line: "#dce4de"
  wash: "#eaf1eb"
  tag: "#e5ede4"
  focus: "#b07728"
typography:
  headline:
    fontFamily: "'Segoe UI', Arial, sans-serif"
    fontSize: "clamp(2rem,3.2vw,2.85rem)"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-.025em"
  title:
    fontFamily: "'Segoe UI', Arial, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 650
    letterSpacing: "-.025em"
  body:
    fontFamily: "'Segoe UI', Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "'Segoe UI', Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 650
rounded:
  tag: "4px"
  example: "6px"
  control: "8px"
  notice: "12px"
  dossier: "14px"
  dialog: "16px"
spacing:
  compact: "8px"
  small: "12px"
  medium: "16px"
  section: "20px"
  wide: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "13px 22px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-example:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.example}"
    padding: "8px 10px"
  query-field:
    textColor: "{colors.ink}"
    padding: "2px"
  navigation-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.control}"
    padding: "13px 12px"
  recognized-tag:
    backgroundColor: "{colors.tag}"
    rounded: "{rounded.tag}"
    padding: "5px 9px"
  expert-card:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.dossier}"
    padding: "22px"
---

# Design System: AIID Expert Search

## Overview

**Creative North Star: "The Comparison Dossier"**

A quiet operational workspace built from sage paper, forest-green controls and white expert dossiers. The density supports reading requirements, evidence and candidate differences in one session. No raster assets or portraits are used.

The system UI font stack supports offline operation and familiar forms. It is a deliberate workspace choice; there is no separate display typography role.

**Key Characteristics:**
- Sage canvas and white evidence surfaces.
- Forest-green primary actions and selected navigation.
- Explicit labels, factual status text and visible keyboard focus.

## Colors

Muted greens connect the workspace; neutral surfaces separate evidence without decoration. Frontmatter values are normative.

### Primary
- **Forest Green** (`primary`): submit action, selected navigation, coverage figures and profile links.
- **Deep Forest** (`primary-hover`): enabled primary-button hover.

### Neutral
- **Deep Ink** (`ink`): query content and modal text.
- **Muted Sage Ink** (`muted`): secondary explanations and metadata.
- **Sage Paper** (`canvas`), **Sidebar Sage** (`sidebar`) and **Soft Wash** (`wash`): workspace layers.
- **White Dossier** (`surface`): forms, profiles, tables and modal.
- **Sage Divider** (`line`): boundaries between content and controls.
- **Recognized Sage** (`tag`): parsed requirement chips.

Amber focus outlines are independent of availability and warning colors. Availability always includes a readable label; it is never conveyed by color alone.

**The Evidence Accent Rule.** Forest green marks actions, selection and coverage; factual prose keeps the quieter ink colors.

## Typography

Use the frontmatter's system stack throughout. Headings are moderately weighted with tight tracking; paragraphs retain an open line height. The main heading is the headline role, section headings use title, and forms use label. Expert names use a compact heading treatment (18px, line height 1.35); supporting metadata generally uses 12–14px. Coverage numerals are tabular (26px, weight 600).

## Layout

The desktop workspace has a fixed navigation rail (232px), a compact service header, and a centered content area capped at 1600px. Main horizontal padding is 40px, expanding to 60px above 1600px. Three equal expert columns use a 16px gap.

At 1200px the rail becomes 200px, main gutters become 24px, and candidates become full-width dossiers with two internal columns. At 800px the rail becomes an icon column (76px) and gutters become 20px. At 520px navigation moves into the document flow, cards stack internally, examples and submit action fill the width, and form controls wrap. Comparison tables scroll horizontally rather than compressing their cells.

## Elevation & Depth

There are no box shadows. White surfaces, pale green layers and thin borders provide separation. The profile dialog uses a dark translucent backdrop; that is the only substantial overlay. Motion is limited to smooth anchor scrolling and a one-second loading spinner. Reduced-motion preference removes animation and smooth scrolling.

**The Paper Layer Rule.** Use tonal separation and borders for workspace depth.

## Shapes

Small rectangular chips, gently rounded controls and larger rounded dossiers create a restrained hierarchy. The asymmetric brand monogram is a local identity detail, not a general component silhouette. Borders are thin and quiet. The dialog has the largest established radius.

## Components

### Buttons
Primary actions have forest fill, white text, a minimum height of 46px and a darker enabled hover state. Example-query buttons are white with a thin divider border; hover changes the border and introduces a sage fill. Disabled submit actions use reduced opacity and a wait cursor. Keyboard focus uses the shared amber outline (3px, offset 4px).

### Inputs / Fields
The query textarea sits inside the bordered white search form, with a visible label above it and guidance below. The textarea is borderless, vertically resizable, and uses a green caret. The industry select has a pale background and inline SVG chevron. Mobile increases query height and wraps the filter row.

### Navigation
Navigation combines inline stroke SVGs and readable text. The active destination has a forest fill. Intermediate widths show icons; accessible names remain in the links. On small phones the navigation is horizontal beside the wordmark.

### Chips
Recognized requirements use compact sage rectangles. Matched skills add a small SVG check. Availability chips use green, amber or muted red with a text label. These chips report facts rather than acting as controls.

### Cards / Containers
White expert dossiers carry a thin border, generous internal padding and evidence separated by horizontal rules. Ranking and availability precede the name; coverage, reasons, missing conditions and actions follow. The modal retains the same paper surface with a darker backdrop.

## Do's and Don'ts

### Do:
- **Do** preserve the sage-paper, white-dossier and forest-action relationship.
- **Do** keep labels and factual text alongside color-coded status.
- **Do** retain visible focus and reduced-motion support.
- **Do** let long comparison content scroll horizontally on narrow screens.

### Don't:
- **Don't** add fabricated portraits, contact details or decorative metric claims.
- **Don't** describe coverage as a probability of suitability.
- **Don't** introduce shadows as the default surface separator.
