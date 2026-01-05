# Attractor Explorer GUI

Interactive Python GUI for visualizing classic chaotic attractors (Lorenz, Rossler, Thomas, Aizawa). The app uses Matplotlib's 3D toolkit for plotting with Qt or Tkinter UI.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the main Tkinter version (RECOMMENDED)
python attractor_gui.py

# Or run the Qt version (alternative)
python attractor_qt.py
```

## Requirements

This project now uses **Python 3.13** with **Tk 9.0**, which provides excellent compatibility and performance.

## Features

### attractor_gui.py (Tkinter - **Recommended**)
- ✅ Dropdown to select attractor type
- ✅ Editable parameters and initial conditions
- ✅ Random seed + range for randomized initial conditions
- ✅ Plot settings: steps, dt, burn-in, stride, point size
- ✅ Plot modes: line, scatter, or line+scatter
- ✅ Play/Pause animation with configurable step and delay
- ✅ Mouse rotation and zoom via Matplotlib toolbar
- ✅ Error reporting dialog + log file in `logs/`
- ✅ **Works with Python 3.13 + Tk 9.0**

### attractor_qt.py (Qt/PyQt6 - Alternative)
- ✅ Dropdown to select attractor type
- ✅ Editable parameters and initial conditions
- ✅ Plot settings: steps, dt, stride
- ✅ Mouse rotation and zoom via Matplotlib toolbar
- ✅ Modern, native macOS appearance

## Dependencies
- Python 3.13 (with Tk 9.0)
- numpy 2.4+
- matplotlib 3.10+
- PyQt6 6.10+ (optional, for Qt version)

## Notes
- Logs are written to `logs/attractor_gui.log` inside the project folder.
- If the plot looks too sparse or dense, adjust `steps`, `stride`, and `point size`.

## Files
- `attractor_gui.py`: main GUI application.
- `attractor_explorer.py`: alternate GUI version.
- `logs/attractor_gui.log`: error log output (created on first run).
