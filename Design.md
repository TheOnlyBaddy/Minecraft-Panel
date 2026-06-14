# User Interface Design Guidelines (Design) - Deep Survival Theme

## 1. Design Principles
The interface for the Antigravity Panel is built to feel dark, immersive, and retro, drawing direct inspiration from Minecraft's deep underground structures and HUD interfaces. This theme implements a dark **Deep Survival Theme** utilizing deepslate grays, obsidian blacks, and emerald/diamond/redstone glowing accents.

### Visual Aesthetic
* **Deepslate Dark Tone**: The panel uses deep slate colors (#0D1117, #161B22, #1C2128) to make the admin area feel modern, premium, and focused.
* **Pixelated Repeating Backgrounds**: Uses a repeating pixelated deepslate tile texture (`deepslate_texture.png`) with custom CSS panning animations for authentic block branding on login and loading states.
* **Blocky & Flat Geometry**: Backdrops and cards use 0px to 4px border-radius values, completely eliminating rounded circular items in favor of blocky Minecraft GUI slots.
* **Signature HUD Accents**: Uses glowing borders and highlights mapped to classic Minecraft resources (Emerald Green for online/active, Redstone Red for stopped/error, Gold/Amber for warning/restarting, Diamond Blue for starting).
* **Retro Gaming Typography**: Uses the **`VT323`** pixel-art font (upscaled for readability) for headers, brand badges, and metrics, while relying on **`Inter`** for tables and forms, and **`JetBrains Mono`** for terminal logs.
* **Immersive 8-bit Audio**: Synthesizes authentic retro 8-bit blocky sound effects (chimes) client-side in the browser using the Web Audio API on state changes and player events.

---

## 2. Design System & Style Guide

### CSS Global Custom Properties (Variables)
These variables are declared in the root stylesheet (`index.css`) under the `@theme` directive:

```css
@theme {
  --color-bg-primary: #0D1117;
  --color-bg-secondary: #161B22;
  --color-bg-surface: #1C2128;
  --color-bg-elevated: #232A34;

  --color-mc-emerald: #2ECC71;
  --color-mc-diamond: #45D9FF;
  --color-mc-gold: #F5C542;
  --color-mc-redstone: #FF5D5D;
  --color-mc-amethyst: #B388FF;
  --color-mc-copper: #D88C4A;

  --color-status-online: #2ECC71;
  --color-status-offline: #7F8C8D;
  --color-status-warning: #F5C542;
  --color-status-error: #FF5D5D;
  --color-status-starting: #45D9FF;
  --color-status-stopping: #FF8A65;

  --color-text-primary: #FFFFFF;
  --color-text-secondary: #C7CDD5;
  --color-text-muted: #8A94A6;

  --font-sans: 'Inter', 'system-ui', 'sans-serif';
  --font-pixel: 'VT323', 'Silkscreen', monospace;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'monospace';
  
  --shadow-mc-sm: 1px 1px 0px 0px rgba(0, 0, 0, 0.4);
  --shadow-mc-md: 2px 2px 0px 0px rgba(0, 0, 0, 0.4);
  --shadow-mc-lg: 4px 4px 0px 0px rgba(0, 0, 0, 0.5);
}
```

### Typography Scale
* **Logo / Major Titles**: `2rem` to `2.5rem`, using `--font-pixel` (`VT323`), upscaled to combat typical pixel-font rendering limits.
* **Heading 2**: `1.5rem`, using `--font-pixel` (Page and tab titles).
* **Body Standard**: `0.875rem`, using `--font-sans` (`Inter` for high legibility in tables and properties lists).
* **Console / Terminals**: `0.9rem`, using `--font-mono` (`JetBrains Mono`).

### Audio Cue Synthesis Scale (Web Audio API)
* **Server Started**: Ascending arpeggio (G4 -> C5 -> E5 -> G5) at 80ms interval (triangle wave) + Square wave chirp at C6 (now + 0.32s). Volume: `0.45` gain.
* **Server Stopped**: Sawtooth frequency ramp-down (180Hz -> 60Hz over 0.35s) + low piston thud at E2 (82.41Hz) + low-pass filtered white noise puff. Volume: `0.42` / `0.5` gain.
* **Server Restarted**: Dual success chord (C5 -> G5 -> C6) + high sine sweep (523Hz -> 1200Hz over 0.4s). Volume: `0.4` gain.
* **Player Joined**: Quick ascending double-ding (E5 -> A5) at 80ms interval. Volume: `0.25` gain.
* **Player Disconnected**: Quick descending double-note (A4 -> E4) at 80ms interval. Volume: `0.22` gain.

---

## 3. Page Layouts & Wireframes

### Main Collapsible Sidebar Layout
All authenticated pages display this general structure:
```
+---------------------------------------------------------------------------------+
| BRAND LOGO      | Page Title (Dashboard)                     | User Profile V   |
| [ΛG PANEL]      |                                            | [admin]          |
| (Blinking Dot)  |                                            |                  |
+-----------------+--------------------------------------------+------------------+
| [■] Server      |                                                               |
| [■] Console     |   [ Main Content Grid / Deepslate Cards ]                     |
| [■] Options     |                                                               |
| [■] Players     |                                                               |
| [■] Files       |                                                               |
|                 |                                                               |
| (Toggle Collapse)                                                               |
+-----------------+---------------------------------------------------------------+
| Status: ONLINE  | IP: 127.0.0.1:25565 [Copy]                                    |
+---------------------------------------------------------------------------------+
```

---

## 4. Accessibility Standards (WCAG 2.1 AA)
* **Color Contrast**: Primary text (`--color-text-primary`) against dark surfaces (`--color-bg-secondary`) maintains high contrast ratios (> 7:1), well exceeding the 4.5:1 requirement.
* **Keyboard Focus**: Focusable inputs render with an emerald-green active border outline.

---

## 5. Mobile Responsiveness Requirements
1. **Collapsible Sidebar**: Shrinks to a compact 16px icon rail on tablets and mobiles.
2. **Auto-Wrap Grids**: Metrics charts and hardware graphs wrap from side-by-side to stacked columns below `768px`.
