---
name: humm-brand-guidelines
description: Applies Humm's official brand colors, typography, and design standards to any artifact that may benefit from having Humm's look-and-feel. Use when creating presentations, documents, reports, marketing materials, or any visual deliverable for Humm. Triggers on requests like "Apply Humm branding", "Make this on-brand", "Use Humm style", or when creating Humm-branded content.
---

# Humm Brand Guidelines

Apply Humm's official brand colors, typography, and design standards to any artifact.

## Company Identity

**Company Name**: Humm (lowercase "humm" in wordmark)
**Product**: AI-powered analytics platform for post-sale teams
**Logo**: Hummingbird silhouette in muted pink/mauve circle
**URL**: heyhumm.ai

### Positioning
"The retention and analytics platform for Customer Success, Post-Sales, Growth Managers, and CX Leads"

### Taglines
- **Primary**: "Analytics for Post-Sale Teams"
- **Value Prop**: "Stop churn. Expand revenue. Boost productivity."
- **Product**: "Ask. Analyze. Answer."
- **Ease**: "Simple to setup. Easy to use. No coding required. Get answers in minutes."

### What Humm Does
- Spot churn risk early
- Find new revenue opportunities
- Automate key workflows (QBR prep, portfolio reviews, account deep dives)
- "An analyst for everyone" - analyst expertise without headcount

## Color System

### Brand Primary
| Color | Value | Usage |
|-------|-------|-------|
| Humm Coral | `#FE4B4B` | Logo accent, CTAs, loading spinners, gradient highlights |
| Brand Primary (OKLCH) | `oklch(0.6691 0.2156 25.17)` | Primary interactive elements |

### Light Theme (Warm Cream Palette)
| Role | OKLCH Value | Approx Hex | Usage |
|------|-------------|------------|-------|
| Background | `oklch(0.9895 0.0090 78.2827)` | #FBF9F4 | Warm cream page background |
| Foreground | `oklch(0.3511 0.0070 182.6352)` | #3D4A47 | Primary text (dark teal-gray) |
| Card | `oklch(0.9511 0.0108 76.5977)` | #F2EDE2 | Content cards |
| Primary | `oklch(0.8472 0.0367 53.6516)` | #DBC9B0 | Interactive elements |
| Muted | `oklch(0.9651 0.0074 80.7210)` | #F7F4ED | Subdued backgrounds |
| Muted Foreground | `oklch(0.4652 0.0041 67.7244)` | #6B6B66 | Secondary text |
| Border | `oklch(0.9297 0.0120 79.7830)` | #E8E2D6 | Borders, dividers |

### Dark Theme (Deep Blue-Gray Palette)
| Role | OKLCH Value | Approx Hex | Usage |
|------|-------------|------------|-------|
| Background | `oklch(0.3494 0.0041 196.9688)` | #3A4548 | Deep blue-gray background |
| Foreground | `oklch(0.9694 0.0096 72.6624)` | #F9F5EA | Primary text (warm white) |
| Card | `oklch(0.2686 0 0)` | #333333 | Content cards |
| Primary | `oklch(0.4408 0.0230 166.9612)` | #4A6560 | Interactive elements |
| Accent | `oklch(0.9278 0.0502 158.6988)` | #C4E8D8 | Mint green accent |

### Chart Colors

**Light Theme** - Earthy, natural palette (cool to warm):
```css
--chart-1: #2d7d5c;  /* forest green - primary */
--chart-2: #789e75;  /* sage */
--chart-3: #b4bf9a;  /* moss */
--chart-4: #e8e3ca;  /* sand */
--chart-5: #e7c48e;  /* wheat */
--chart-6: #f09c5f;  /* amber */
--chart-7: #fb694a;  /* coral - accent */
```

**Dark Theme** - Cool purple-to-pink gradient:
```css
--chart-1: #344eb4;  /* deep blue - primary */
--chart-2: #9479c7;  /* lavender */
--chart-3: #d1adde;  /* mauve */
--chart-4: #ffe9fb;  /* pale pink */
--chart-5: #ffbcd9;  /* rose */
--chart-6: #ff8e9c;  /* salmon */
--chart-7: #fb694a;  /* coral - accent (shared) */
```

### Status Colors
| Status | Light Mode | Dark Mode |
|--------|-----------|-----------|
| Success | `oklch(0.5 0.15 145)` | `oklch(0.65 0.15 145)` |
| Error | `oklch(0.55 0.2 25)` | `oklch(0.65 0.18 25)` |
| Warning | `oklch(0.7 0.15 55)` | `oklch(0.75 0.15 55)` |
| Info | `oklch(0.55 0.15 250)` | `oklch(0.65 0.15 250)` |

## Typography

### Font Stack
```css
--font-sans: Geist, sans-serif;           /* Primary UI */
--font-serif: Source Serif 4, serif;       /* Editorial, headlines, reports */
--font-mono: 'Fira Code', 'JetBrains Mono', monospace;  /* Code, data */
```

### Usage Guidelines
| Context | Font | Style |
|---------|------|-------|
| UI text, buttons, labels | Geist | Regular 400, Semibold 600 |
| Headlines (marketing) | Source Serif 4 | Italic for emphasis |
| Long-form content, reports | Source Serif 4 | Regular 400 |
| Data tables, code, SQL | Fira Code | Regular 400 |

### Text Hierarchy
- **Headings**: Semibold 600, sentence case (never ALL CAPS)
- **Body**: Regular 400, generous line spacing (1.4-1.6x)
- **Captions**: Regular 400, muted-foreground color

## Design Tokens

### Border Radius (Rounded, Friendly)
```css
--radius: 0.875rem;        /* Base (14px) */
--radius-sm: 0.625rem;     /* Small (10px) */
--radius-md: 0.75rem;      /* Medium (12px) */
--radius-lg: 0.875rem;     /* Large (14px) */
--radius-xl: 1.125rem;     /* Extra large (18px) */
```

### Shadows
```css
/* Light mode - subtle */
--shadow-sm: 0px 4px 8px -1px hsl(0 0% 0% / 0.10);
--shadow-md: 0px 4px 8px -1px hsl(0 0% 0% / 0.10), 0px 2px 4px -2px hsl(0 0% 0% / 0.10);

/* Dark mode - deeper */
--shadow-sm: 0px 4px 8px -1px hsl(0 0% 0% / 0.30);
--shadow-md: 0px 4px 8px -1px hsl(0 0% 0% / 0.30), 0px 2px 4px -2px hsl(0 0% 0% / 0.30);
```

## Logo Usage

### Assets
| Version | File | Description |
|---------|------|-------------|
| Dark mode | `hum_logo_dark.svg` | Coral circle with white hummingbird |
| Light mode | `humm_logo.png` | Full color logo |
| Favicon (light) | `favicon_light.png` | Hummingbird on coral-to-blue gradient |
| Favicon (dark) | `favicon_dark.png` | Hummingbird on gradient |

### Hosted URLs
```
https://v1-public.s3.us-east-1.amazonaws.com/humm/hum_logo_dark.svg
https://v1-public.s3.us-east-1.amazonaws.com/humm/humm_logo.png
```

### Logo Circle Color
The marketing website shows the logo in a **muted pink/mauve circle** - softer than the bright coral used for CTAs.

### Wordmark
- Use lowercase "humm" for the wordmark
- Pair with hummingbird icon to the left
- Standard size: 28x28px icon with text

## Tone of Voice

### Writing Style
- **Clear**: Direct, jargon-free explanations
- **Helpful**: Focus on enabling users to get insights
- **Professional**: Business-appropriate but approachable
- **Confident**: "We will..." not "We might..."
- **Data-driven**: Let the data tell the story

### Preferred Phrases
- "Ask questions in natural language"
- "Get insights from your data"
- "Analyze, visualize, understand"
- "Stop churn. Expand revenue."
- "An analyst for everyone"

### Avoid
- Overly technical database jargon to end users
- Vague promises about AI capabilities
- "AI-powered magic" or similar hype
- Complex explanations when simple ones suffice
- Excessive superlatives

## Document Types

### Presentations
- Warm cream backgrounds for content slides
- Use Source Serif 4 italic for headlines
- Humm coral (`#FE4B4B`) for accent elements only
- Chart colors from the earthy palette (light) or purple palette (dark)
- Include Humm logo in header/footer

### Reports & Documents
- Source Serif 4 for body text
- Geist for UI elements and labels
- Include Humm logo on title page
- Use status colors consistently
- Generous margins and whitespace

### Data Visualizations
- Follow the 7+ color chart palette
- Forest green (#2d7d5c) as primary data color in light mode
- Deep blue (#344eb4) as primary in dark mode
- Coral (#fb694a) for highlights/accents
- Always include clear labels and legends
- No 3D effects

## UI Components

### Buttons
- Default: `bg-primary text-primary-foreground`
- Destructive: Red/coral tones
- Ghost: Transparent with hover accent
- Rounded corners (`rounded-md` to `rounded-sm`)

### Cards
- `bg-card` background
- `rounded-lg` corners
- Subtle shadow on hover
- Orange/terracotta accent lines for emphasis (marketing style)

### Loading States
- Use `text-brand-primary` for spinners
- Shimmer animation for skeleton loading
- Gradient animation for progress indicators

## Quick Reference

For rapid lookup of color codes and values, see [REFERENCE.md](references/REFERENCE.md).
