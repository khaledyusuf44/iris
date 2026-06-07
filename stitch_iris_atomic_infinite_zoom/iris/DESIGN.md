---
name: IRIS
colors:
  surface: '#13131b'
  surface-dim: '#13131b'
  surface-bright: '#393841'
  surface-container-lowest: '#0d0d15'
  surface-container-low: '#1b1b23'
  surface-container: '#1f1f27'
  surface-container-high: '#292932'
  surface-container-highest: '#34343d'
  on-surface: '#e4e1ed'
  on-surface-variant: '#bac9cc'
  inverse-surface: '#e4e1ed'
  inverse-on-surface: '#303038'
  outline: '#849396'
  outline-variant: '#3b494c'
  surface-tint: '#00daf3'
  primary: '#c3f5ff'
  on-primary: '#00363d'
  primary-container: '#00e5ff'
  on-primary-container: '#00626e'
  inverse-primary: '#006875'
  secondary: '#b4cbce'
  on-secondary: '#1f3436'
  secondary-container: '#384d4f'
  on-secondary-container: '#a6bcbf'
  tertiary: '#ffeac0'
  on-tertiary: '#3e2e00'
  tertiary-container: '#fec931'
  on-tertiary-container: '#6f5500'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#9cf0ff'
  primary-fixed-dim: '#00daf3'
  on-primary-fixed: '#001f24'
  on-primary-fixed-variant: '#004f58'
  secondary-fixed: '#d0e7ea'
  secondary-fixed-dim: '#b4cbce'
  on-secondary-fixed: '#091f21'
  on-secondary-fixed-variant: '#364a4d'
  tertiary-fixed: '#ffdf96'
  tertiary-fixed-dim: '#f3bf26'
  on-tertiary-fixed: '#251a00'
  on-tertiary-fixed-variant: '#594400'
  background: '#13131b'
  on-background: '#e4e1ed'
  surface-variant: '#34343d'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '300'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '400'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '400'
    lineHeight: '1.2'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: 0.01em
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.5'
    letterSpacing: 0.08em
  label-xs:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.1em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  orbit-sm: 16px
  orbit-md: 32px
  orbit-lg: 64px
  orbit-xl: 128px
  gutter: 24px
  margin: 40px
---

## Brand & Style

The design system is built upon a "Spatial Atom" philosophy, emphasizing the vastness of the cosmos and the precision of scientific visualization. It targets a high-end audience seeking clarity, focus, and a sense of premium technological sophistication. The UI should evoke a feeling of weightlessness, floating in a deep, structured void.

The visual style is a blend of **Glassmorphism** and **Minimalism**, utilizing translucent layers and luminous outlines to define boundaries without closing them. Heavy use of negative space is mandatory to allow elements to "breathe" and "orbit" one another, maintaining a layout that feels intentional, quiet, and expansive.

## Colors

The palette is rooted in the depth of space. 
- **Primary (Electric Blue):** Reserved for "active" electrons, critical highlights, and interactive states. It represents energy and focus.
- **Secondary (Cool White/Cyan):** Used for structural outlines, orbital paths, and primary text. It provides a luminous, ethereal quality.
- **Background (Space Ink):** A near-black void that provides the canvas for all spatial elements.
- **Surface (Neutral):** Subtly lighter than the background, used for low-opacity glass layers and container backgrounds.

Color should be applied sparingly. Interaction is signaled by a shift from a dim, cold luminance to the vibrant electric blue.

## Typography

Typography functions as both data and decoration. **Inter** provides a modern, neutral geometric base for communication. **JetBrains Mono** is utilized for metadata, "technical thought" labels, and coordinates, reinforcing the scientific visualization aesthetic.

Headlines should use light weights and tight tracking to feel elegant and airy. Labels are always uppercase with increased letter spacing to create a sense of mechanical precision.

## Layout & Spacing

This design system uses a **Fluid Spatial Grid**. Rather than rigid columns, elements are positioned relative to central "nuclei" or along "orbital paths." 

- **Desktop:** A wide 12-column grid with generous 40px margins. Content is often centered or offset to create an asymmetrical, celestial balance.
- **Mobile:** A 4-column grid with 20px margins. Stacked elements should maintain vertical "lanes" that suggest a single axis of rotation.

Spacing units (Orbit) are multiples of 8, but should be applied to create large voids between functional groups.

## Elevation & Depth

Depth is conveyed through **Luminous Layers** rather than shadows.
- **Base Level:** The deep #050508 background.
- **Mid Level:** Semi-transparent containers (opacity 4-8%) with a subtle backdrop blur (20px).
- **High Level:** Luminous outlines (0.5px to 1px) using the Secondary color at low opacity (20-40%).

Active elements emit a soft, localized glow (Glow-spread: 20px, Color: Primary) instead of a drop shadow. This suggests the element is a light source within the void.

## Shapes

The shape language is strictly **Circular and Elliptical**. 
- Buttons, containers, and image masks should prioritize full "Pill" or "Circle" shapes.
- Avoid sharp corners entirely. If a rectangle is necessary for large data blocks, use the `rounded-xl` (1.5rem/24px) radius to maintain the soft, organic feel of a celestial body.
- Borders should be ultra-thin (0.5pt) to simulate the delicacy of a light ray or a mathematical plot line.

## Components

- **Buttons:** Large, pill-shaped. Default state is a delicate Secondary outline. Active/Hover state fills with the Primary electric blue and triggers a soft outer glow.
- **Chips:** Small pill shapes using JetBrains Mono. Used for status indicators and "electron" tags that orbit main content.
- **Cards:** Glassmorphic circles or large-radius rectangles with a 0.5px luminous border. No solid background; only a subtle backdrop blur and 5% tint.
- **Input Fields:** Bottom-border only, or a subtle pill-shaped outline that glows when focused.
- **Orbits (Special Component):** Concentric thin lines used to group related items or act as progress indicators.
- **Particles:** Small 2px by 2px squares (Primary color) used as data points or decorative "stardust" in the background.

**Motion:** All component transitions must be eased with a "slow-in, slow-out" cubic-bezier. Hovering over a card should cause "electrons" (status chips) to slightly adjust their orbital distance.