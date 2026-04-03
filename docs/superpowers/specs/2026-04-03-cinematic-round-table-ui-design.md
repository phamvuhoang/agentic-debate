# Cinematic Round Table UI Design Spec

**Date:** 2026-04-03  
**Status:** Approved

---

## Overview

The current debate demo is a functional streaming shell: a fixed input header, a dark content column, and A2UI cards rendered into a single surface. It proves the debate engine works, but it does not deliver the product identity implied by "agentic debate."

This redesign replaces that shell with a spectacle-first, desktop-oriented, interactive 3D stage. The product becomes a live debate performance engine centered on a round table chamber. Users do not just read arguments arriving in a feed; they summon a council, steer the debate, spotlight speakers, trigger clashes, and reveal a final verdict inside a cinematic environment.

The new experience is intentionally optimized for public-facing demo impact. Mobile support is secondary and should degrade gracefully rather than constrain the primary desktop vision.

---

## Product Direction

Confirmed design decisions from brainstorming:

- Visual direction: cinematic round table
- Primary optimization: spectacle
- Product posture: public-facing demo stage
- Scene structure: full 3D stage, not a 3D intro attached to a 2D app
- User role during debate: active director, not passive viewer
- Data model constraint: backend and frontend may both be redesigned freely
- Device priority: desktop and laptop first, mobile as a reduced secondary experience

These choices imply a product that behaves more like a directed performance than a dashboard.

---

## Goals

- Create a memorable demo experience with a strong first impression.
- Make the round table chamber the primary interface, not decorative garnish.
- Support active user direction during a live debate without collapsing into conventional app chrome.
- Replace text-only streaming with a typed event model that can drive scene choreography.
- Preserve precise readability for current speaker output and key debate beats through lightweight overlays.
- Keep the system resilient enough to fall back to a 2D presentation if WebGL or performance constraints require it.

---

## Non-Goals

- Building a dense analyst workstation for power users
- Optimizing mobile before the desktop experience is proven
- Preserving A2UI as the main rendering primitive for debate content
- Shipping a full persistence/history system in the same milestone
- Solving authentication, user accounts, or multi-user collaboration
- Treating the first release as a generic visualization toolkit for any future product surface

---

## Experience Pillars

### 1. Chamber First

The chamber is the product. Architecture, lighting, seat state, and camera motion communicate the debate state before any user reads a line of text.

### 2. Directed Spectacle

The experience should feel intentional and choreographed. Camera moves, table energy, and transitions should reinforce the active speaker and current phase instead of firing independently.

### 3. Active Direction

Users should be able to intervene meaningfully: focus a speaker, inject a challenge, redirect the topic, advance rounds, or force a verdict.

### 4. Readable Core

Even in a spectacle-first demo, exact language still matters. The current speaker thesis, live output text, round state, and major debate beats must remain legible in the overlay layer.

### 5. Controlled Intensity

Only one part of the system is allowed to be visually dominant at once. The camera, table, and overlays must obey explicit motion priority rules to avoid incoherence.

---

## User Experience Flow

The product runs as five cinematic phases.

### Idle

The application opens directly into a quiet council chamber. The round table glows softly, seats remain empty or dormant, and the camera drifts in a restrained orbit. The prompt entry is presented as an invocation console rather than a standard toolbar.

### Summoning

When the user starts a debate, the chamber assembles itself. Seats activate one by one, each agent gains an identity treatment, and ambient energy rises. The user sees the cast being formed before the debate begins.

### Debate

The active speaker owns the room. Camera framing, seat emphasis, lighting, and table visuals all orient toward the current turn. Supporting overlay UI presents the readable transcript and control state.

### Clash

Challenges and rebuttals intensify the scene. Motion sharpens, opposing seats are linked visually, and the camera becomes more directional. This phase should feel more forceful without becoming noisy.

### Verdict

The chamber recenters. Peripheral noise falls away, the judge or synthesis authority takes control, and the final conclusion lands with a full-scene visual convergence.

---

## Interface Architecture

The interface consists of three coordinated layers.

### 1. Stage Layer

This is the dominant surface and is implemented in Three.js.

Core responsibilities:

- render the council chamber environment
- render the round table as the central state display
- render one seat per agent
- animate seat activation, focus, challenge links, consensus shifts, and verdict convergence
- manage atmosphere, lighting transitions, particles, and camera choreography

The stage should fill nearly the full viewport on desktop and remain the visual center at all times.

### 2. Performance Overlay

This is lightweight DOM UI layered over the scene. It exists for precise reading and navigation, not for visual dominance.

Core elements:

- invocation prompt bar
- live speaker header
- concise speaker thesis or status line
- readable caption/transcript panel
- round and phase indicator
- timeline rail for key debate beats
- quick focus chips for agents and judge

Overlay elements should live at the perimeter of the screen and stay visually subordinate to the chamber.

### 3. Director Controls

This is the user action layer for live intervention. It should feel like stage direction rather than generic application settings.

Core controls:

- start debate
- pause and resume
- focus a specific speaker
- inject a challenge
- redirect the topic
- advance round
- request verdict
- switch between guided and free camera modes

The default presentation should keep this dock compact or semi-hidden until the user signals intent.

---

## Scene Design

### Chamber

The chamber should evoke a circular council room with strong depth and hierarchy. It should feel physical and weighty rather than flat sci-fi HUD design. Geometry can be stylized, but the space needs a clear center and perimeter so users always understand orientation.

### Round Table

The table is the main narrative device. It visualizes:

- current speaker focus
- directional challenges between agents
- round progress
- consensus drift
- verdict convergence

The table should not be a passive prop. It is the debate state display in spatial form.

### Seats

Each agent occupies a fixed seat with a distinct identity treatment:

- name
- role
- stance
- color or emblem signature
- active/inactive/focused/challenged states

Seats create spatial memory. A user should quickly learn where each agent "lives" in the chamber.

### Camera

The camera should operate through named presets and target anchors, not arbitrary freeform animation. Likely modes:

- idle orbit
- summon reveal
- active speaker focus
- challenge confrontation
- round overview
- verdict center lock

Free camera can exist as a user-controlled mode, but the default experience should stay choreographed.

---

## Interaction Model

The user is an active director. Interaction should be high-value and low-clutter.

### Primary user actions

- enter a topic and begin a debate
- pause or resume the current performance
- select a speaker to inspect or focus
- inject a challenge to force tension or clarification
- redirect the debate with a new instruction
- advance to the next round
- request the verdict early
- scrub back to previous major beats

### Interaction principles

- controls should change the scene in visible ways
- interventions should be acknowledged in both the event stream and the chamber
- the product should never feel like a hidden admin panel layered on top of a demo reel
- when a control is used, the chamber should react immediately even if backend work continues asynchronously

---

## Event-Driven Product Model

The current frontend consumes streamed surface messages. That model is insufficient for a full 3D stage. The new system should use typed domain events that can drive both the scene and the readable overlay.

### Proposed debate events

- `debate_created`
- `agent_summoned`
- `speaker_activated`
- `argument_started`
- `argument_completed`
- `challenge_issued`
- `rebuttal_started`
- `consensus_shifted`
- `judge_intervened`
- `round_closed`
- `verdict_requested`
- `verdict_revealed`
- `debate_paused`
- `debate_resumed`
- `error_raised`

### Proposed user action events

- `pause_debate`
- `resume_debate`
- `focus_agent`
- `inject_challenge`
- `redirect_debate`
- `advance_round`
- `request_verdict`
- `move_camera`

### Event consumption split

The frontend should process the same canonical event stream through two consumers:

- `scene engine`
  - updates camera, lighting, seat states, table state, and animation intensity
- `overlay engine`
  - updates captions, titles, transcript snippets, timeline markers, and control availability

This separation ensures readable text does not depend on 3D scene internals.

---

## Motion System Rules

Motion is a product feature, not a decorative afterthought. It needs explicit limits.

### Priority rules

- only one visual climax can dominate at a time
- dramatic camera motion should coincide with simplified table/overlay motion
- intense table animation should coincide with calmer camera behavior
- overlays should reduce movement when users need to read exact language

### Motion mapping

- normal speaking turns: slow drift, local table activity, isolated speaker emphasis
- challenge events: directional energy across the table, stronger contrast between seats
- rebuttals: tighter framing and faster response cues
- verdict: central lock, reduced ambient noise, strongest scene-wide transformation

### Reduced-motion behavior

Reduced-motion mode should preserve state clarity by replacing dramatic movement with:

- fades
- seat highlights
- lighting changes
- fixed framing transitions

---

## Frontend Architecture

The current single-file frontend should be replaced with a modular structure.

```text
demo/frontend/
  src/
    app/
      bootstrap.ts
      session-controller.ts
    scene/
      renderer.ts
      chamber-scene.ts
      camera-controller.ts
      animation-orchestrator.ts
      objects/
        round-table.ts
        speaker-seat.ts
        atmosphere.ts
    state/
      debate-session-store.ts
      event-reducer.ts
      selectors.ts
      types.ts
    overlay/
      prompt-bar.ts
      speaker-banner.ts
      caption-panel.ts
      timeline-rail.ts
      director-dock.ts
    transport/
      live-session-client.ts
      replay-client.ts
      protocol.ts
    styles/
      tokens.css
      app.css
```

### Recommended stack direction

- retain `Vite`
- keep overlay UI lightweight; Lit remains acceptable for the DOM layer
- add `Three.js` as the stage runtime
- treat the 3D scene as a first-class application subsystem
- move away from `a2ui-surface` as the primary debate renderer

---

## Backend And Protocol Implications

Because both frontend and backend may change freely, the protocol should be redesigned around event semantics rather than raw UI fragments.

Backend responsibilities:

- create debate sessions with stable identifiers
- emit typed stage-ready events in chronological order
- accept live control actions during a session
- acknowledge control actions so the UI can stay synchronized
- support replay of key debate beats for the timeline

The frontend should not infer major narrative states from arbitrary text blobs. If the product needs a visual state, that state should exist explicitly in the protocol.

---

## Desktop And Mobile Strategy

### Desktop and laptop

Desktop is the reference experience:

- full 3D chamber
- broader camera movement
- persistent timeline and caption surfaces
- director dock available during live sessions

### Mobile

Mobile is a graceful reduction, not the source of truth. Likely compromises:

- simplified or static chamber camera
- reduced geometry and particle load
- fewer simultaneous overlays
- condensed control set
- more conventional stacked transcript presentation

The desktop experience should not be diluted to satisfy mobile prematurely.

---

## Accessibility And Resilience

The redesign is visual, but it cannot depend entirely on visuals.

Requirements:

- readable text counterpart for every major debate beat
- keyboard-accessible controls for primary actions
- reduced-motion mode
- color usage backed by labels or icons, not color alone
- 2D fallback shell when WebGL is unavailable or performance is inadequate

The fallback shell can be much simpler, but it must preserve functional debate control and readable session output.

---

## Performance Guardrails

To keep the spectacle from collapsing under runtime cost:

- degrade visual effects based on device capability
- keep geometry and shader complexity within predictable bounds
- separate state transitions from render loops
- drive major animations from explicit scene state, not scattered timers
- keep the overlay responsive even during heavy scene transitions

The system should prefer stable frame rate over maximal visual density.

---

## Testing Strategy

### Unit tests

- event reducer behavior
- selector correctness
- action-to-event mappings
- motion priority resolution

### Integration tests

- full session flow from topic submission to verdict
- user intervention handling during an active debate
- timeline replay behavior
- fallback behavior when the stage runtime is unavailable

### Manual verification

- large desktop displays
- smaller laptop displays
- reduced-motion mode
- performance sanity on mid-tier hardware
- mobile degradation path

---

## Migration Notes

The current demo can serve as a functional backend reference, but the frontend architecture should be treated as disposable.

Specific migration implications:

- replace the current `index.html` plus `main.js` shell with a modular app entry
- preserve debate-engine integration, but stop binding the product surface to streamed A2UI cards
- rework the `/debate` contract into a session-oriented event protocol
- keep a thin compatibility path only if it meaningfully accelerates development

The goal is not to skin the current feed. The goal is to establish a new product surface.

---

## Out Of Scope For This Design

- debate history persistence
- authentication and account models
- collaborative multi-user spectatorship
- advanced analytics dashboards
- generalized theming or white-label support
- non-round-table visual themes

---

## Final Principle

This redesign should be implemented under a single product assumption:

**Agentic Debate is a real-time debate performance engine with a cinematic 3D chamber as its primary interface, not a text streaming app with visual garnish.**
