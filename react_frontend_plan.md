# React Frontend UI Implementation Plan

This plan details how we will construct the Kalpana React frontend that connects to the FastAPI backend, utilizing the deep purple and vibrant magenta theme inspired by the WEAL health hackathon badge.

## Proposed Components Architecture

The frontend will be built out in the `kalpana-frontend/src` directory.

### 1. `App.jsx` (Main Container & State Management)
*   **Role**: Manages the global state (`messages`, `peerMatch`, `isTyping`).
*   **Logic**: Contains the asynchronous `fetch()` API calls to `http://127.0.0.1:8000/api/chat`.
*   **UI Layout**: Sets up the main full-screen container with the `FluidBackground`, centering the `ChatWindow` and `ChatInput`.

### 2. `components/FluidBackground.jsx` (Thematic Elements)
*   **Role**: Provides the deep organic theme.
*   **UI Layout**: Renders absolutely positioned SVG blobs floating slowly via CSS animations. The background itself will be a static gradient of deep aubergine (`#2E0A4E`) to midnight black (`#12041A`), while the blobs will be vibrant magenta (`#D81B60`).

### 3. `components/ChatWindow.jsx`
*   **Role**: The scrollable container for the chat history.
*   **UI Layout**: Uses a glassmorphic effect (`bg-white/5 backdrop-blur-md`) giving the frosted glass look over the fluid background. It will auto-scroll to the bottom when new messages are added.

### 4. `components/MessageBubble.jsx`
*   **Role**: Renders an individual message (either "user" or "kalpana" role).
*   **UI Layout**: 
    *   **User messages**: Solid Magenta background (`bg-[#D81B60]`), aligned to the right.
    *   **Kalpana messages**: Translucent Purple background (`bg-[#2E0A4E]/80 backdrop-blur-sm`), aligned to the left.
    *   Both will utilize heavy rounding (`rounded-2xl` or `rounded-3xl`).

### 5. `components/ChatInput.jsx`
*   **Role**: The bottom text input area.
*   **UI Layout**: A dark, translucent, rounded-full text input with a glowing magenta send button (`bg-[#D81B60] hover:bg-[#E6007A] shadow-[0_0_15px_rgba(216,27,96,0.5)]`).

### 6. `components/PeerMatchModal.jsx`
*   **Role**: Activated when the API returns a peer match.
*   **UI Layout**: A pop-up modal overlay that emphasizes the match, providing a prominent call-to-action button to "Connect.

## Tailwind Configuration (`tailwind.config.js`)
We will extend the Tailwind theme to include the custom Kalpana semantic colors for deep darks and vibrant magentas.

## Implementation Steps
1.  **Tailwind Setup**: Configure `tailwind.config.js` and `index.css`.
2.  **Component Scaffolding**: Create the `.jsx` files inside `src/components/`.
3.  **State Logic**: Implement the API call and state array logic inside `App.jsx`.
4.  **Styling Application**: Apply the Tailwind classes and custom CSS for glassmorphism and animations.
5.  **CORS & Proxy Setup**: Configure `vite.config.js` to proxy requests to `http://localhost:8000/api/chat` to avoid CORS issues during development.
