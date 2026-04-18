# Loading Screen Design — Step 2 Onboarding

## Overview
The active loading screen (`/starter/loading`) appears after the user completes OAuth authentication (Google consent). Instead of a boring spinner, it displays **3 animated milestones** that explain what's happening and increase perceived value while the backend initializes data in the background.

**Total Duration**: ~7 seconds (auto-redirects to dashboard)

---

## Visual Structure

```
┌─────────────────────────────────────────────┐
│                                             │
│  🚀 Lokigi                                  │
│  Inicializando tu cuenta                    │
│  Estamos preparando todo para ti            │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  🔐 Conectando con Google          (1.5s)  │
│     Autenticando y verificando acceso       │
│     • • •  (animated dots)                  │
│                                             │
│  ✅ Conectando con Google          (2s)    │
│     Autenticando y verificando acceso       │
│                                             │
│  📚 Analizando historial...        (2.5s)  │
│     Extrayendo datos y patrones             │
│     • • •  (animated dots)                  │
│                                             │
│  ✅ Analizando historial...        (3s)    │
│     Extrayendo datos y patrones             │
│                                             │
│  🧠 Entrenando IA con tu tono     (2s)    │
│     Adaptando respuestas a tu voz           │
│     • • •  (animated dots)                  │
│                                             │
├─────────────────────────────────────────────┤
│  Progreso  [████░░░░░░░░░░░░░░░░]  47%    │
├─────────────────────────────────────────────┤
│              ✨                             │
│  ¡Casi listo! Redirigiendo en unos         │
│  momentos…                                  │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Timeline & Animations

### Milestone 1: "Conectando con Google..." (0-2s)
- **Duration**: 2000ms
- **Icon**: 🔐 (lock icon)
- **State Progression**:
  - 0-2s: Icon pulses with blue glow, dots animate
  - 2s: Icon becomes static green checkmark ✅
- **Description**: "Autenticando y verificar acceso"

### Milestone 2: "Analizando historial de reseñas..." (2-4.5s)
- **Duration**: 2500ms (slightly longer to suggest more processing)
- **Icon**: 📚 (books icon)
- **State Progression**:
  - 0-2s: Opacity ~0.5, awaiting activation
  - 2s-4.5s: Icon pulses with blue glow, dots animate
  - 4.5s: Icon becomes static green checkmark ✅
- **Description**: "Extrayendo datos y patrones"

### Milestone 3: "Entrenando IA con tu tono..." (4.5-6.5s)
- **Duration**: 2000ms
- **Icon**: 🧠 (brain icon)
- **State Progression**:
  - 0-4.5s: Opacity ~0.5, awaiting activation
  - 4.5-6.5s: Icon pulses with blue glow, dots animate
  - 6.5s: Icon becomes static green checkmark ✅
- **Description**: "Adaptando respuestas a tu voz"

### Progress Bar
- Linear fill from 0% → 100% over ~6.5 seconds
- **Color Gradient**: Teal (#0f766e) → Green (#10b981)
- Represents overall completion

---

## Color Palette

| Element | Color | Purpose |
|---------|-------|---------|
| Accent (pulses) | `#0f766e` (teal) | Primary brand, active state |
| Accent Dark | `#115e59` (darker teal) | Gradient end, depth |
| Success | `#10b981` (green) | Completed milestone ✅ |
| Background | `#f3f7f6` (off-white) | Main page background |
| Card | `#ffffff` (white) | Container |
| Text | `#1f2937` (dark gray) | Primary text |
| Muted | `#6b7280` (medium gray) | Secondary/helper text |

---

## Animations

### Icon Pulse (Active Milestone)
```css
@keyframes pulse-icon {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.08); }
}
animation: pulse-icon 1.5s ease-in-out infinite;
box-shadow: 0 0 20px rgba(15, 118, 110, 0.4);
```

### Dot Bounce Loader
```css
@keyframes bounce {
    0%, 80%, 100% { opacity: 0.3; transform: translateY(0); }
    40% { opacity: 1; transform: translateY(-6px); }
}
```
- 3 dots in sequence, each with 0.2s delay
- Repeats infinitely, disappears when milestone completes

---

## UX Benefits

| Benefit | Implementation |
|---------|-----------------|
| **Reduced anxiety** | Milestones explain what's happening (no mysterious wait) |
| **Value perception** | "Training AI" + "Analyzing reviews" sounds sophisticated |
| **Engagement** | Animations are subtle but engaging (not annoying) |
| **Time perception** | 7 seconds feels shorter because something is visibly happening |
| **Branding** | Consistent colors/fonts with rest of Lokigi |
| **Mobile-friendly** | Responsive design, readable on small screens |

---

## Technical Details

- **No npm/build required**: Pure HTML5 + CSS + vanilla JavaScript
- **Auto-redirect**: After ~6.5s of milestones, JavaScript redirects to `/starter/dashboard`
- **Responsive**: Works on mobile (max-width: variable, uses flexbox)
- **Accessible**: Semantic HTML, readable color contrast ratios

---

## Integration in Onboarding Flow

```
1. User at /starter/onboarding
   ↓
2. User clicks "Conectar Google Maps"
   ↓ /starter/connect-google (redirects)
   ↓
3. Google OAuth consent screen (user authorizes)
   ↓ (returns to /oauth/google/callback)
   ↓
4. Backend creates GoogleConnection, validates location
   ↓ REDIRECT to /starter/loading
   ↓
5. Loading screen displays milestones (7 seconds)
   ↓
6. Auto-redirect to /starter/dashboard
   ↓
7. User sees their reviews + connection status ✅
```

**Total time**: ~2-3 min (OAuth waiting) + 7 sec (loading screen) = ~2:10 min from click to dashboard

---

## Future Enhancements

- Add real progress events from backend (WebSocket or Server-Sent Events)
- Customize milestone text per user (e.g., "Analyzing your 47 reviews...")
- Add confetti animation when done
- A/B test different milestone titles ("Gathering insights..." vs "Analyzing reviews...")
