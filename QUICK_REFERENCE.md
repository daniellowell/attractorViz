# Attractors Project - Quick Reference

## Environment Info

- **Python:** 3.13.11
- **Tk/Tcl:** 9.0
- **numpy:** 2.4.0
- **matplotlib:** 3.10.8
- **PyQt6:** 6.10.1

## Run Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Main GUI (Tkinter) - Full features with animation
python attractor_gui.py

# Alternative GUI (Qt) - Simpler, modern UI
python attractor_qt.py

# Run tests
python test_attractors.py
```

## Available Attractors

1. **Lorenz** - Classic butterfly attractor
   - Parameters: sigma, rho, beta
   - Default init: (0.1, 0.0, 0.0)

2. **Rossler** - Spiral attractor
   - Parameters: a, b, c
   - Default init: (0.0, 1.0, 0.0)

3. **Thomas** - Cyclically symmetric attractor
   - Parameters: b
   - Default init: (0.1, 0.0, 0.0)

4. **Aizawa** - Complex toroidal attractor
   - Parameters: a, b, c, d, e, f
   - Default init: (0.1, 0.0, 0.0)

## Key Features

### attractor_gui.py (Tkinter)
- Parameter editing
- Initial conditions (manual or random)
- Plot settings (steps, dt, burn-in, stride, point size)
- Plot modes (line, scatter, line+scatter)
- Animation controls (play/pause)
- 3D rotation/zoom
- Error logging to `logs/attractor_gui.log`

### attractor_qt.py (Qt)
- Parameter editing
- Initial conditions
- Plot settings (steps, dt, stride)
- 3D rotation/zoom
- Clean, modern interface

## File Structure

```
Attractors/
├── attractor_gui.py          # Main Tkinter GUI
├── attractor_explorer.py     # Alternative Tkinter GUI
├── attractor_qt.py            # Qt GUI
├── test_attractors.py         # Validation tests
├── test_gui_imports.py        # Import tests
├── requirements.txt           # Dependencies
├── venv/                      # Python 3.13 virtual environment
├── venv-old-python39/         # Backup of old environment
├── logs/                      # Runtime logs (created on first run)
├── README.md                  # User documentation
├── PROJECT_CONTEXT.md         # Architecture notes
├── SETUP.md                   # Original setup guide
├── DEPENDENCIES.md            # Dependency details
├── TROUBLESHOOTING.md         # Tk 8.5 compatibility issues
├── UPGRADE_SUMMARY.md         # Python 3.13 upgrade details
└── QUICK_REFERENCE.md         # This file
```

## Troubleshooting

**GUI won't start:**
```bash
# Check Python version
python --version  # Should be 3.13.11

# Check Tk version
python -c "import tkinter; print(tkinter.TkVersion)"  # Should be 9.0

# Verify you're in the venv
which python  # Should show venv/bin/python
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

**Old Python still active:**
```bash
# Deactivate and reactivate
deactivate
source venv/bin/activate
```

## Common Tasks

**Generate a specific attractor:**
1. Launch `python attractor_gui.py`
2. Select attractor from dropdown
3. Adjust parameters if desired
4. Click "Create Plot"

**Animate the trajectory:**
1. Create plot first
2. Set animation step size (default: 100)
3. Click "Play"
4. Adjust delay (ms) for speed control

**Save a view:**
- Use the matplotlib toolbar "Save" button
- Supports PNG, PDF, SVG formats

**Randomize initial conditions:**
1. Check "Use random"
2. Set seed (for reproducibility) or leave blank
3. Set range (default: 1.0)
4. Click "Create Plot"

## Performance Tips

- **Reduce steps** if plotting is slow (try 10000 instead of 20000)
- **Increase stride** to plot fewer points (try 4-5)
- **Use line mode only** for fastest rendering
- **Disable animation** for complex attractors

## Support

For issues or questions, see:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common problems
- [README.md](README.md) - Full documentation
- [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md) - What changed in Python 3.13 upgrade
