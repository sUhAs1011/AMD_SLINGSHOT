# Kalpana UI - React Frontend Theme Proposal

Based on the Health Hack 4.0 badge, the theme should evoke a bold, modern, and empathetic feel, utilizing a blend of deep plum/purple and vibrant hot pink/magenta. This creates a strong tech-forward aesthetic while remaining approachable and warm for a mental health application.

## 🎨 Color Palette

The color palette is directly inspired by the "Weal" hackathon badge.

### Core Colors
*   **Deep Aubergine (Primary Dark):** `#3A0CA3` or `#2E0A4E`
    *   *Usage:* App background (dark mode), sidebar backgrounds, heavy text.
*   **Vibrant Magenta (Primary Accent):** `#D81B60` or `#E6007A`
    *   *Usage:* Primary buttons (like "Send Message"), active states, peer match modal highlights.
*   **Soft Pink (Secondary Accent):** `#F48FB1` or `#FFB6C1`
    *   *Usage:* Timestamp text, secondary borders, subtle hover effects.
*   **Midnight Black (Base):** `#12041A`
    *   *Usage:* Deepest backgrounds, providing contrast for the glowing magenta elements.

### Tailwind UI Color Mapping Suggestions
If using TailwindCSS, you can configure your `tailwind.config.js` to match these semantic colors:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        kalpana: {
          900: '#1A0B2E', // Deep background
          800: '#2E0A4E', // Cards and message bubbles
          500: '#D81B60', // Primary buttons and accents (The WEAL Pink)
          300: '#F48FB1', // Soft accents
          100: '#FDF8FD', // Light text
        }
      }
    }
  }
}
```

## 📐 Design & UI/UX Principles

1.  **Glassmorphism & Gradients:** 
    *   Since the badge features fluid, organic shapes, the UI should use soft gradients and glassmorphism (frosted glass effects via `backdrop-blur`).
    *   The background can be a static CSS gradient blending Dark Purple and Midnight Black, with floating blurred magenta blobs to mimic the badge's fluid art.
2.  **Organic Shapes & Waves:**
    *   Instead of sharp, rigid squares, use rounded corners (`rounded-2xl` or `rounded-3xl` in Tailwind) for chat bubbles and buttons.
    *   Use SVG wave dividers between the header and chat body to match the fluid artwork on the badge.
3.  **Typography:**
    *   Use a clean, modern sans-serif font like **'Inter'** or **'Outfit'**. 
    *   The badge text is slightly blocky, but for a chat app, readability is key. Use high-contrast white text (`text-slate-100`) on the deep purple backgrounds.
4.  **Micro-Animations (The "Alive" Feel):**
    *   When Kalpana is "thinking," use a pulsating magenta glow (`animate-pulse`) instead of standard grey loading dots.
    *   The "Peer Match Found" modal should slide up with a soft bounce and a glowing magenta border (`shadow-[0_0_15px_rgba(216,27,96,0.5)]`).

## 🧱 Suggested React Component Architecture

If you build this in React (e.g., using Vite + React + Tailwind), structure it like this:

*   `App.jsx` - Main layout wrapper with the dark purple gradient background.
*   `components/`
    *   `ChatWindow.jsx` - The main scrollable chat area with a frosted glass background (`bg-white/5 backdrop-blur-md`).
    *   `MessageBubble.jsx` - Renders individual messages. User messages are **Solid Magenta**, Kalpana messages are **Translucent Purple Glass**.
    *   `ChatInput.jsx` - The bottom text area with a glowing send button.
    *   `PeerMatchModal.jsx` - A highly stylized pop-up that triggers when risk scores cross the threshold, featuring a strong magenta gradient to draw attention.
    *   `FluidBackground.jsx` - A purely decorative background component that renders slow-moving, blurry SVG blobs (matching the badge's pink liquid shapes) behind the chat window.

## 🚀 Getting Started with React

When you are ready to build this, you can initialize your new frontend using Vite with this command:

```bash
npm create vite@latest kalpana-frontend -- --template react
cd kalpana-frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```
