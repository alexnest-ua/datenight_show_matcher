# Frontend brand & design spec — "Warm Premium on Void"

The DateNight Show Matcher demo wears a premium, technical aesthetic: a deep
true-void background with glass-morphism panels, ultra-thin borders, a faint
blockchain-style grid texture, warm colored glows, gradient-text accents, and
precise snappy motion. The palette is anchored to the **PlayFix red** primary
plus a **warm gold** value/highlight accent (date-night warmth, not crypto
orange). **Dark is the default and the star**; light is a tasteful warm override
that softens glows into neutral shadows.

Type: **Space Grotesk** for headings, **Inter** for body, **JetBrains Mono** for
data, labels, badges, JSON, and micro-copy.

## Design tokens (define once in `:root`, override under `[data-theme="light"]`)

### Dark (default) — true-void depth
```
--bg:            #050506   /* true void */
--bg-elev:       #0b0c0e
--surface:       #101114
--surface-2:     #16181c
--glass:         rgba(255,255,255,0.04)   /* translucent panel fill */
--glass-2:       rgba(255,255,255,0.06)
--border:        rgba(255,255,255,0.08)
--border-subtle: rgba(255,255,255,0.05)
--border-strong: rgba(255,255,255,0.14)
--text:          #f7f8fa
--text-muted:    #9ba3b0
--text-dim:      #6b7280
```

### Light — warm premium (not pure white)
```
--bg:            #faf7f4
--bg-elev:       #ffffff
--surface:       #ffffff
--surface-2:     #f4efea
--border:        rgba(0,0,0,0.08)
--border-strong: rgba(0,0,0,0.14)
--text:          #1a1614
--text-muted:    #5c5550
--text-dim:      #8a817a
```

### Accents
```
--primary:       #ef4444   /* PlayFix red — CTAs, active state, logo "Fix" */
--primary-deep:  #dc2626
--accent:        #f5b53f   /* warm gold — value / highlight / available */
--accent-deep:   #e09a2a
--success:       #34d399
--warn:          #f5b53f
--link:          var(--accent)   /* gold links read better on void than blue */
--gradient-warm: linear-gradient(90deg, #ef4444, #f5b53f)
```
Light overrides: `--primary:#dc2626`, `--accent:#c2841a`, `--success:#15803d`
(darkened for ≥4.5:1 contrast on the warm-white background).

### Platform badges (tuned for void)
```
--netflix:       #e50914
--hbo:           #a06bff
--prime:         #2ab6e6
```

### Glows & shadows (the luminescence)
On **dark**, elevation is colored glow, not black drop shadow:
```
--glow-primary:        0 0 28px -8px rgba(239,68,68,0.45)
--glow-primary-strong: 0 0 38px -8px rgba(239,68,68,0.60)
--glow-accent:         0 0 24px -6px rgba(245,181,63,0.40)
--glow-card:           0 0 50px -16px rgba(239,68,68,0.12)
--shadow:              0 1px 2px rgba(0,0,0,.4), 0 18px 40px -24px rgba(0,0,0,.7)
```
On **light**, all `--glow-*` are redefined as subtle neutral drop shadows and
platform-badge glows are disabled — so the aesthetic stays calm in daylight.

### Texture
```
--grid-line:     rgba(255,255,255,0.035)   /* light: rgba(0,0,0,0.04) */
```
The ambient background (`.void-bg`) layers a faint 3rem grid behind a radial
mask (fades at the edges) plus two large, blurred, low-opacity radial blobs
(red + gold) for depth. It is fixed, decorative, and `aria-hidden`.

## Type
- **Headings:** `Space Grotesk` 400–700 (`--font-heading`). Tight tracking on
  display (`-0.025em`), large hero (`--fs-3xl` 3.25rem at ≥48rem).
- **Body:** `Inter` 400–700 (`--font-sans`).
- **Data / labels / badges / JSON / micro-copy:** `JetBrains Mono` 400–500
  (`--font-mono`). Use the `.mono-label` utility for uppercase tracked labels
  (`letter-spacing: 0.12em`).
- **Gradient text:** `.gradient-text` (and the logo's "Fix") clip
  `--gradient-warm` to the glyphs, with a solid-colour fallback.
- **Font sizes in `rem`, minimum `1rem`** — no exceptions, including mono labels
  (kept at 1rem with tracking). Loaded via Google Fonts with `display=swap` and
  preconnect (self-hosting preferable for prod — see README).

## Shape & motion
- Radii: `--radius-lg: 1rem` (cards), `--radius: 0.75rem` (inner), pill `9999px`
  (buttons / badges / chips / pills).
- Borders: ultra-thin 1px from `--border`; hover lifts to `--primary` at ~40%.
- **Glass cards:** translucent `--glass` fill + `backdrop-filter: blur()` + 1px
  border; hover → `translateY(-2px)` + border to primary + soft `--glow-card`.
- **Icon "node" containers** (`.stage-node`): rounded square, tinted bg, 1px
  border; the running stage glows primary and shows a pulsing dot
  (`.stage-live-dot`). A thin vertical gradient connector runs behind the stage
  list (`.stage-list::before`) for a ledger feel.
- **Pill buttons:** primary = warm gradient + `--glow-primary`, hover
  `scale(1.02)` + intensified glow; ghost/outline variant per reference.
- Transitions: 150–200ms `ease-out` (`--ease`). No bounce/elastic, no
  outer-glow on light. All non-essential motion (pulse, spin, lift, shimmer,
  float) is wrapped by `prefers-reduced-motion`.
- Layout with **Flexbox** (not Grid). Mobile-first `min-width` media queries.

## Logo
Wordmark as styled text (offline-safe, no hotlinking): **"Play"** in `--text` +
**"Fix"** with `--gradient-warm` clipped to the glyphs (solid `--primary`
fallback), Space Grotesk 700, tight tracking. Exposed as `<Logo/>` with a
comment noting the official asset can be dropped in.

## Product framing
Header: PlayFix logo + mono tag "DateNight Show Matcher", theme toggle
(sun/moon, dark default, persisted to `localStorage`, initial value respects
`prefers-color-scheme` only if no stored choice). A mono mode pill shows **LIVE**
(green, pulsing dot) when a backend is connected or **DEMO** (gold) when
replaying a recording. The four pipeline stages render as glass cards with icon
node containers; the active stage glows and pulses.

## A11y / performance (hard floor)
WCAG 2.1 AA: semantic HTML, one `<h1>`, ordered headings, skip-to-content link,
keyboard operable, visible `:focus-visible` ring (uses `--primary`), labels on
inputs, `aria-live="polite"` on the pipeline status region, ≥4.5:1 text
contrast (muted/gold-on-void verified), 44×44px touch targets, `alt`/`aria` on
icons (all glyphs `aria-hidden`; meaning carried by text). Targets: LCP < 1.5s,
CLS < 0.05, no render-blocking JS, `font-display: swap`, declared sizes.
External CSS only — **no inline `style`, no CSS-in-JS.** Reusable class names +
CSS variables; avoid one-off selectors.
