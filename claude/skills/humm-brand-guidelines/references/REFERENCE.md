# Humm Brand Quick Reference

## Brand Identity

**Name**: Humm (lowercase "humm" in wordmark)
**Tagline**: "Analytics for Post-Sale Teams"
**Value Prop**: "Stop churn. Expand revenue. Boost productivity."
**Product Message**: "Ask. Analyze. Answer."

---

## Quick Checklist

### Must-Have
- [ ] Humm logo (hummingbird + wordmark)
- [ ] Correct theme colors (light/dark)
- [ ] Geist for UI, Source Serif 4 for editorial
- [ ] Rounded corners (0.875rem base)
- [ ] Coral (#FE4B4B) for accents only
- [ ] Chart colors from official palette

### Never Use
- Humm Coral for body text (accessibility)
- ALL CAPS headings
- Sharp corners (always use border-radius)
- Generic chart colors outside palette
- Decorative/script fonts
- "AI-powered magic" language

---

## Color Codes

### Brand Primary
```
Humm Coral:     #FE4B4B
Brand OKLCH:    oklch(0.6691 0.2156 25.17)
```

### Light Theme
```
Background:     oklch(0.9895 0.0090 78.2827)   ~#FBF9F4  Warm cream
Foreground:     oklch(0.3511 0.0070 182.6352)  ~#3D4A47  Dark teal-gray
Card:           oklch(0.9511 0.0108 76.5977)   ~#F2EDE2  Content areas
Primary:        oklch(0.8472 0.0367 53.6516)   ~#DBC9B0  Interactive
Muted:          oklch(0.9651 0.0074 80.7210)   ~#F7F4ED  Subdued bg
Muted FG:       oklch(0.4652 0.0041 67.7244)   ~#6B6B66  Secondary text
Border:         oklch(0.9297 0.0120 79.7830)   ~#E8E2D6  Dividers
```

### Dark Theme
```
Background:     oklch(0.3494 0.0041 196.9688)  ~#3A4548  Deep blue-gray
Foreground:     oklch(0.9694 0.0096 72.6624)   ~#F9F5EA  Warm white
Card:           oklch(0.2686 0 0)              ~#333333  Content areas
Primary:        oklch(0.4408 0.0230 166.9612)  ~#4A6560  Interactive
Accent:         oklch(0.9278 0.0502 158.6988)  ~#C4E8D8  Mint green
```

### Chart Colors (Light - Earthy)
```
1. #2d7d5c  Forest Green  (primary)
2. #789e75  Sage
3. #b4bf9a  Moss
4. #e8e3ca  Sand
5. #e7c48e  Wheat
6. #f09c5f  Amber
7. #fb694a  Coral         (accent)
```

### Chart Colors (Dark - Cool)
```
1. #344eb4  Deep Blue     (primary)
2. #9479c7  Lavender
3. #d1adde  Mauve
4. #ffe9fb  Pale Pink
5. #ffbcd9  Rose
6. #ff8e9c  Salmon
7. #fb694a  Coral         (accent)
```

### Status Colors
```
Success:  oklch(0.5 0.15 145)   Light  |  oklch(0.65 0.15 145)  Dark
Error:    oklch(0.55 0.2 25)    Light  |  oklch(0.65 0.18 25)   Dark
Warning:  oklch(0.7 0.15 55)    Light  |  oklch(0.75 0.15 55)   Dark
Info:     oklch(0.55 0.15 250)  Light  |  oklch(0.65 0.15 250)  Dark
```

---

## Typography

### Font Stack
```css
--font-sans: Geist, sans-serif;
--font-serif: Source Serif 4, serif;
--font-mono: 'Fira Code', 'JetBrains Mono', monospace;
```

### Usage
| Context | Font | Style |
|---------|------|-------|
| UI, buttons | Geist | Regular/Semibold |
| Headlines (marketing) | Source Serif 4 | *Italic* |
| Reports, long-form | Source Serif 4 | Regular |
| Code, data, SQL | Fira Code | Regular |

---

## Design Tokens

### Border Radius
```css
--radius: 0.875rem;     /* Base 14px */
--radius-sm: 0.625rem;  /* 10px */
--radius-md: 0.75rem;   /* 12px */
--radius-lg: 0.875rem;  /* 14px */
--radius-xl: 1.125rem;  /* 18px */
```

### Shadows
```css
/* Light */
--shadow-sm: 0px 4px 8px -1px hsl(0 0% 0% / 0.10);

/* Dark */
--shadow-sm: 0px 4px 8px -1px hsl(0 0% 0% / 0.30);
```

---

## Logo Assets

### URLs
```
Dark:  https://v1-public.s3.us-east-1.amazonaws.com/humm/hum_logo_dark.svg
Light: https://v1-public.s3.us-east-1.amazonaws.com/humm/humm_logo.png
```

### Sizes
- App header: 28x28px icon + "Humm" text
- Favicon: 32x32px / 16x16px

---

## Key Phrases

### Do Say
- "Analytics for Post-Sale Teams"
- "Stop churn. Expand revenue. Boost productivity."
- "Ask. Analyze. Answer."
- "An analyst for everyone"
- "Simple to setup. Easy to use."

### Don't Say
- "AI-powered magic"
- "Revolutionary breakthrough"
- "Just ask anything"
- Technical database jargon to end users

---

## Common Mistakes

1. **Wrong coral** - Use #FE4B4B, not generic red
2. **Missing logo** - Always include on branded materials
3. **Theme mismatch** - Light colors on dark backgrounds
4. **Sharp corners** - Always use border-radius
5. **Wrong fonts** - Use Geist/Source Serif, not system fonts
6. **Chart chaos** - Use the official palette only
7. **Coral for text** - Only for accents (accessibility)
8. **ALL CAPS** - Use sentence case for headings
