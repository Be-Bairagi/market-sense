# UI Enhancement Plan — Phase 1: Engine Loader & App Shell

**Goal:** The app's first impression must communicate intelligence and trustworthiness before the user sees any data.

## What to build
The Engine Initialization Loader is a multi-step animated sequence shown on every cold start (or when the user manually refreshes). It calls `/health` in the background while the animation plays.

### Features
- **Multi-step animated sequence (3-4 seconds total)**:
  - "Connecting to market data..."
  - "Loading AI prediction models..."
  - "Fetching today's news sentiment..."
  - "Running stock screener..."
  - "Your picks are ready."
- **Rotating "Pro Tips"**:
  - "Tip: We always show a Stop Loss. Never invest without one."
  - "Tip: Confidence above 75% means the AI is very sure."
  - "Tip: The Bear Case tells you what could go wrong."
- **Soft Banner Transition**: If `/health` returns DEGRADED, show a soft banner instead of a hard error.
- **Session State Persistence**: Loader only shows once per session.

## Implementation Details
- Use `st.empty()` containers with `time.sleep()` for status animation.
- Reference `st.session_state["loader_done"]` to prevent re-triggering on navigation.
- Store tips in a `TIPS` constant list.

## Checklist
- [ ] Multi-step loader with status messages renders on cold start
- [ ] Pro Tips rotate correctly beneath the status line
- [ ] Loader transitions cleanly to the main app after completion
- [ ] DEGRADED health state shows soft banner, not error screen
- [ ] Loader does not re-show on page navigation within the same session
- [ ] Tested on both desktop and mobile viewport widths
