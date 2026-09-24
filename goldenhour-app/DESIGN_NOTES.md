# 🎨 GoldenHour — Design System Notes & Token Parity

Pixel-ported from `OptiMeal_hero_interactive_updated (5).html` (the source of truth).

## 1. Palette Tokens

| Token | Hex / Value | Description |
|---|---|---|
| `--ink` | `#17221b` | Deep dark charcoal for high-contrast headlines |
| `--deep` | `#173d2a` | Forest green primary brand color |
| `--green` | `#8fd35a` | Radiant electric green accent for CTAs and safe timers |
| `--green-dark` | `#69a83f` | Darkened green for indicators and badges |
| `--soft` | `#e6f1df` | Pastel lime green tint for pills and cards |
| `--paper` | `#f7f6f1` | Warm off-white paper canvas background |
| `--white` | `#ffffff` | Clean white for floating elevated cards |
| `--cream` | `#f1e8d2` | Soft organic backdrop accent |
| `--muted` | `#68736b` | Sage gray for secondary copy |
| `--line` | `#dce5da` | Subtle hairline borders |
| `--red` | `#d96b4b` | Warm terracotta red for critical countdown alerts |
| `--peach` | `#f0a083` | Tight buffer warning tint |
| `--blue` | `#8db8c9` | Ambient secondary tint |
| `--blue-text` | `#4d869d` | Recipient / shelter accent |
| `--blue-tint` | `#f1f7fa` | Recipient card background |

## 2. Typography

- **Headings & Body:** `DM Sans` (400, 500, 600, 700, 800)
- **Serif Accent Emphases:** `Instrument Serif` (Italic, 400)
- **Monospace Container Tags & OTPs:** `JetBrains Mono` / System Monospace

## 3. Signature Animations & Micro-Interactions

- **Button Hover:** `-3px` translateY lift with `cubic-bezier(.16, 1, .3, 1)` easing.
- **Button Arrow:** `+4px` translateX slide on hover.
- **Toggle:** 31×18px pill toggle with 14px circular knob sliding with `--ease` and soft halo glow.
- **Live Dot Pulse:** 2s keyframe ring expansion from `#69a83f55` to transparent.
- **CountdownRing:** Real-time SVG stroke-dashoffset transition with 3 dynamic color states (Safe -> Tight -> Critical).
- **Background Orbs:** Subtle 14s-16s floating radial gradients with organic breathing.
