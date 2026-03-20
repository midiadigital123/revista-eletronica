# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Escala Interativa** is a single-page web application for analyzing educational assessment results and proficiency scales for Brazilian Portuguese language instruction. It covers grade levels 5º EF, 9º EF, and 3ª EM, presenting descriptors (D01–D40) mapped to BNCC competencies and proficiency patterns.

## Running the Application

No build process — open `escala.html` directly in a browser.

Images and assets are served from `http://localhost:3845/assets/` (Figma Desktop local server). The `.vscode/mcp.json` configures the Figma MCP integration at `http://127.0.0.1:3845/mcp`.

## Architecture

Three files make up the entire application:

- **`escala.html`** — Structure: hero → intro → interactive section (filter buttons, descriptor grid, scale visualization, BNCC info) → sticky sidebar menu
- **`script.js`** — Logic
- **`styles.css`** — Styling

### JavaScript (`script.js`)

Seven manager classes coordinate through a shared `appState` object and custom DOM events:

```
appState = { currentFilter: '5ef', currentDescriptor: 'D01', scrolling: false }
```

| Class                  | Responsibility                                    |
| ---------------------- | ------------------------------------------------- |
| `FilterManager`        | Grade level filter buttons (5ef, 9ef, 3em)        |
| `DescriptorManager`    | Descriptor selection and content rendering        |
| `NavigationManager`    | Previous/Next button navigation                   |
| `StickyMenuManager`    | Right-side sticky menu positioning and scroll     |
| `AccessibilityManager` | Keyboard nav (Ctrl+Arrow), ARIA labels            |
| `PerformanceManager`   | Lazy loading via IntersectionObserver, debouncing |
| `App`                  | Initialization and wiring                         |

Data flow: user interaction → manager updates `appState` → DOM updated → CSS transitions animate changes.

`FilterManager` dispatches a custom `filterChanged` event that `DescriptorManager` and others listen to for synchronization.

### Data Structure

All content lives in `descriptorsData` (inline in `script.js`):

```javascript
descriptorsData[filter][descriptor] = {
    topic, description,
    prerequisites[],
    bncc: { practices, knowledge, skills[] },
    scale: { 'padrao-1', 'padrao-2', 'padrao-3', 'padrao-4' }
}
```

### CSS (`styles.css`)

Uses CSS custom properties for the entire design system (colors, spacing, typography, transitions). Responsive breakpoints at: 1400px, 1200px, 800px, 768px, 600px, 500px.

The proficiency scale section uses a CSS grid layout with 4 color-coded patterns (Padrão 01–04), each containing multiple proficiency levels with visual markers and aligned descriptive content.

### Who is you?

name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, or applications. Generates creative, polished code that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt

---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:

- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.
