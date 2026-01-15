# Create Distinctive Frontend UI

Build production-grade, visually distinctive UI components that avoid generic "AI slop" aesthetics. Execute with exceptional attention to aesthetic details and creative choices.

## Before Coding

Understand the context and commit to a **BOLD** aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme—brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work—the key is intentionality, not intensity.

Then implement working code that is:
- **Production-grade and functional**
- **Visually striking and memorable**
- **Cohesive with a clear aesthetic point-of-view**
- **Meticulously refined in every detail**

---

## Our Stack & Design System

### Technology
- **Framework**: Next.js 15 (App Router), React 19
- **Components**: ShadCN UI with class-variance-authority (CVA) for variants
- **Styling**: Tailwind CSS 4 with CSS variables from `globals.css`

### Typography (in `globals.css`)
- `--font-sans: Geist, sans-serif` — primary UI font
- `--font-serif: Source Serif 4, serif` — for editorial/luxury feels
- `--font-mono: Fira Code, JetBrains Mono...` — for data/technical contexts

Don't default to these—use them intentionally. For distinctive pieces, consider importing characterful Google Fonts (via `next/font`) that match the aesthetic direction.

### Color System (OKLCH-based)
Use CSS variables for consistency. Key tokens:
- Core: `--background`, `--foreground`, `--card`, `--popover`
- Interactive: `--primary`, `--secondary`, `--accent`, `--muted`, `--destructive`
- Status: `--status-success`, `--status-error`, `--status-warning`, `--status-info`
- Charts: `--chart-1` through `--chart-13`
- Brand: `--brand-primary` (our signature orange-red)

For bold aesthetics, extend the palette in `globals.css` rather than hardcoding hex/rgb values inline. **ALWAYS define new variables for both `:root` (Light Mode) and `.dark` (Dark Mode) to ensure full support.**

**Best Practice**: Avoid mixing color logic. Use semantic variables (e.g., `--badge-string-bg`) instead of utility classes (e.g., `bg-blue-500`) for component-specific theming. This keeps the design system clean and maintainable.

### Existing Animations
- `.animate-shimmer` — loading states
- `.animate-gradient` — gradient motion
- `.shimmer-text` — text loading effect
- Accordion keyframes built-in

---

## Aesthetic Guidelines

### Typography
Don't default to Geist. For distinctive UI:
- Pair a characterful display font with refined body text
- Consider fonts that match the aesthetic (geometric for brutalist, humanist for organic, etc.)
- Use `next/font/google` to add fonts performantly
- Avoid generic choices like Arial, Inter, or Roboto unless specifically required

### Color & Theme
- Dominant colors with sharp accents > timid, evenly-distributed palettes
- Add bold new CSS variables to `globals.css` when needed
- **Design for BOTH light and dark modes.** Ensure contrast and vibe work in both contexts.
- Never use generic purple gradients on white backgrounds

### Motion & Animation
- Use CSS transitions/animations over JS where possible
- For complex animations, use Motion library (Framer Motion)
- High-impact moments: page load stagger reveals (`animation-delay`), meaningful hover states
- Focus on intentional, high-impact moments—not scattered micro-interactions

### Spatial Composition
- Unexpected layouts—asymmetry, overlap, diagonal flow, grid-breaking elements
- Generous negative space OR controlled density (not lukewarm middle-ground)
- Consider scroll-triggered animations and reveals

### Backgrounds & Texture
- Create atmosphere—gradient meshes, noise textures, geometric patterns
- Layer transparencies, dramatic shadows, decorative borders
- Custom cursors, grain overlays where they enhance the aesthetic
- Never default to flat solid colors

### Creative Interpretation
- **NEVER converge on common choices** (like Space Grotesk) across generations.
- Interpret creatively and make unexpected choices that feel genuinely designed for the context.

---

## Anti-Patterns (AI Slop to AVOID)

- Overused fonts: Inter, Roboto, Arial, system fonts, Space Grotesk
- Clichéd schemes: purple/blue gradients on white, generic startup palettes
- Predictable layouts: centered cards, hero-CTA-features-footer templates
- Cookie-cutter: lack of context-specific character
- Generic shadows and rounded corners with no personality
- "Safe" design that could be any product

---

## Implementation Checklist

1. ✅ Use ShadCN components as a foundation, then **customize heavily**
2. ✅ Add CSS variables to `globals.css` for new colors/effects (for BOTH light/dark modes)
3. ✅ Use CVA for component variants with semantic names
4. ✅ Ensure dark mode works (test with `.dark` class)
5. ✅ **Match complexity to vision**—elaborate for maximalist, precise for minimal
6. ✅ Add meaningful animations that reinforce the aesthetic
7. ✅ Test responsive behavior

---

## Output

Provide:
1. Brief description of the chosen aesthetic direction and why
2. Working TSX component code using our stack
3. Any CSS additions for `globals.css` if needed
4. Notes on font imports if adding new fonts

Remember: Claude is capable of extraordinary creative work. Don't hold back—show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
