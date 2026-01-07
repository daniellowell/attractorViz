# Attractor Explorer - Quick Reference

## Table of Contents

- [Running the Application](#running-the-application)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Attractors](#attractors)
- [Common Tasks](#common-tasks)
- [Menu Quick Reference](#menu-quick-reference)
- [Performance Tips](#performance-tips)
- [Equations Reference](#equations-reference)
- [Troubleshooting](#troubleshooting)
- [File Locations](#file-locations)
- [Environment Info](#environment-info)
- [Performance Metrics](#performance-metrics)

## Running the Application

```bash
# Activate environment
source venv/bin/activate

# Launch
python attractors.py

# Run tests
python test_attractors.py
```

## Keyboard Shortcuts

- **Ctrl+R** - Create/regenerate plot
- **Ctrl+P** - Toggle control panel
- **Ctrl+Q** - Quit

## Attractors

1. **Lorenz** - Butterfly (σ=10, ρ=28, β=8/3)
2. **Rössler** - Spiral (a=0.2, b=0.2, c=5.7)
3. **Thomas** - Symmetric (b=0.208186)
4. **Aizawa** - Toroidal (6 parameters)

## Common Tasks

### Generate Plot
1. Select attractor from dropdown
2. Adjust parameters (tooltips explain each)
3. Click "Create Plot" or Ctrl+R

### Customize Appearance
- **Colors:** Settings → Line/Scatter Color
- **Grid:** Settings → Show Grid
- **Axis:** Settings → Show Axis
- **Theme:** Settings → Dark Mode

### View Stats
- Settings → Show FPS/Memory
- Displays in lower-left corner
- Shows frames per second and memory usage

### 3D Navigation
- **Drag** to rotate view
- **Scroll** to zoom
- **Default view:** 10% closer zoom for better detail
- **Reset:** Plot → Reset View

### Adjust Plot Settings
- Plot → Plot Settings...
- Configure: steps, dt, stride
- Settings persist across plots
- Animation mode: Total Steps field synced with Plot Settings
- Steps field is editable when animation is paused, greyed out while running

### Hide Control Panel
- View → Show Control Panel (uncheck)
- Or press Ctrl+P
- Maximizes plot viewing area

### View Equations
- Equations overlay displayed in upper left corner of plot
- Visible at startup and updated when switching attractors
- Click **?** button for detailed attractor descriptions and history

## Menu Quick Reference

```
File
  └─ Quit (Ctrl+Q)

Settings
  ├─ Line Color...
  ├─ Scatter Color...
  ├─ Reset Colors
  ├─ Draw Line ✓
  ├─ Draw Scatter
  ├─ Show Grid ✓
  ├─ Show Axis ✓
  ├─ Dark Mode
  └─ Show FPS/Memory

View
  └─ Show Control Panel ✓ (Ctrl+P)

Plot
  ├─ Create Plot (Ctrl+R)
  ├─ Plot Settings...
  └─ Reset View

About
  ├─ About Attractor Explorer
  └─ License
```

## Performance Tips

- **Slow plotting?** Reduce steps to 10,000
- **Want more detail?** Decrease stride to 1
- **Toggle operations** are instant (no recomputation)
- **Default settings** (20k steps, stride 2) work well

## Equations Reference

### Lorenz
```
dx/dt = σ(y - x)
dy/dt = x(ρ - z) - y
dz/dt = xy - βz
```

### Rössler
```
dx/dt = -y - z
dy/dt = x + ay
dz/dt = b + z(x - c)
```

### Thomas
```
dx/dt = sin(y) - bx
dy/dt = sin(z) - by
dz/dt = sin(x) - bz
```

### Aizawa
```
dx/dt = (z - b)x - dy
dy/dt = dx + (z - b)y
dz/dt = c + az - z³/3 - (x² + y²)(1 + ez) + fz(x³)
```

## Troubleshooting

### Application won't start
```bash
# Check Python version
python --version  # Should be 3.13+

# Verify environment
which python  # Should show venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

### Import errors
```bash
# Install missing packages
pip install PyQt6 psutil

# Or reinstall all
pip install -r requirements.txt --force-reinstall
```

### Performance issues
- Close other applications
- Reduce plot steps (try 5000-10000)
- Increase stride (try 4-5)
- Disable scatter mode if enabled

## File Locations

```
Attractors/
├── attractors.py          # Main app
├── requirements.txt       # Dependencies
├── test_attractors.py     # Tests
├── venv/                  # Environment
└── logs/                  # Error logs
```

## Environment Info

- Python: 3.13.11
- numpy: 2.4.0
- matplotlib: 3.10.8
- PyQt6: 6.10.1
- psutil: 5.9+

## Performance Metrics

- **FPS:** 55-60 fps
- **Plot time:** ~200ms (10k points)
- **Memory:** ~235 MB loaded
- **Toggle speed:** 70% faster (optimized)

## UI Layout

- **Plot area:** ~81% of graph panel (optimized margins)
- **Equations:** Overlay in upper left corner of plot
- **Axes:** Limited to 5 ticks per axis for cleaner appearance
- **Default zoom:** 10% closer than matplotlib default
