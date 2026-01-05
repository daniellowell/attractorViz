# Project Context: Attractors GUI

## Purpose
This folder contains a Tkinter + Matplotlib 3D GUI for exploring chaotic attractors. The primary app is `attractor_gui.py`. It integrates classic systems (Lorenz, Rossler, Thomas, Aizawa), renders 3D trajectories, and supports animation.

## Key Files
- `attractor_gui.py`: main application with UI, integration loop, and animation.
- `attractor_explorer.py`: alternate GUI variant (similar functionality).
- `REDQME.md`: user-facing usage notes and setup.
- `logs/attractor_gui.log`: runtime error reporting (created on first run).

## Architecture Overview
- **Attractor definitions**: `lorenz`, `rossler`, `thomas`, `aizawa` functions, bundled in `ATTRACTORS` dict.
- **Integrator**: `rk4_integrate` performs fixed-step RK4 integration for performance and simplicity.
- **GUI**: `AttractorApp` builds the UI, controls, and plot area.
- **Plotting**: Matplotlib 3D axes (`Axes3D`), line/point modes, and a toolbar for rotate/zoom.
- **Animation**: timer-driven updates with configurable step size and delay.
- **Error reporting**: `logs/attractor_gui.log` captures exceptions; UI shows friendly dialogs.

## Running
```bash
python /Users/Daddy/Documents/MathExploration/Attractors/attractor_gui.py
```

## Known Assumptions / Constraints
- No external config file; parameters are supplied via the UI.
- The integrator is fixed-step RK4; no adaptive step size.
- Error handling is best-effort and logs to `logs/`.

## Extension Points
- Add attractors by introducing a new derivative function and entry in `ATTRACTORS`.
- Add plotting styles by extending `_render_plot` and `_setup_animation_artists`.
- Add export (CSV/PNG) by wiring a menu action and using `numpy.savetxt` / `fig.savefig`.

## Testing
No automated tests are included. Manual validation steps:
- Create each attractor and verify the plot renders.
- Toggle play/pause and confirm animation stops/starts.
- Try invalid numeric inputs to verify error dialogs/logging.
