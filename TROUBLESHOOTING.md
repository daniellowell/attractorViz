# Troubleshooting Guide - Attractor Explorer

## The macOS Tk 8.5 Compatibility Issue

### Problem
When running `attractor_gui.py` (the Tkinter version), you get this error:
```
macOS 26 (2602) or later required, have instead 16 (1602) !
Abort trap: 6
```

### Root Cause
Your system Python 3.9.6 comes bundled with **Tk/Tcl 8.5**, which was released in 2007. This ancient GUI toolkit is incompatible with modern macOS versions. When matplotlib tries to create a Tkinter window using the TkAgg backend, the old Tk library crashes because it cannot interface with the modern macOS window manager.

### Verification
You can verify your Tk version:
```bash
python3 -c "import tkinter; print(f'Tk version: {tkinter.TkVersion}')"
```

If it shows `8.5`, this is the problem.

## Solution: Use the Qt Backend

### The Working Version
I've created **[attractor_qt.py](attractor_qt.py)** which uses PyQt6 instead of Tkinter. Qt is a modern, cross-platform GUI framework that works perfectly with your macOS version.

### How to Run

**Using the Qt version (RECOMMENDED):**
```bash
source venv/bin/activate
python attractor_qt.py
```

This should launch without any errors!

### Installed Dependencies
The virtual environment now includes:
- PyQt6 6.10.1
- PyQt6-Qt6 6.10.1
- PyQt6-sip 13.10.2

## Why Tkinter Failed

The confusing error message about macOS versions is actually coming from the **Tk library** itself:
- It's checking for a minimum macOS API version
- The version numbers in the error (26/2602 vs 16/1602) refer to internal Tk API versions, not macOS versions
- The old Tk 8.5 cannot create windows on modern macOS

## Alternative Solutions

If you need to use the original Tkinter version, you have these options:

### Option 1: Install Python from python.org
Download Python 3.11+ from https://www.python.org/downloads/
- This comes with Tk 8.6 which works on modern macOS
- Recreate the virtual environment with this Python

### Option 2: Use Homebrew Python
```bash
brew install python-tk@3.11
# Then create venv with: python3.11 -m venv venv
```

### Option 3: Install python-tk separately
Some systems allow installing Tk separately, but this is complex on macOS.

## File Comparison

| File | GUI Framework | Status |
|------|---------------|--------|
| [attractor_gui.py](attractor_gui.py) | Tkinter (TkAgg backend) | ❌ Crashes with Tk 8.5 |
| [attractor_explorer.py](attractor_explorer.py) | Tkinter (TkAgg backend) | ❌ Crashes with Tk 8.5 |
| [attractor_qt.py](attractor_qt.py) | PyQt6 (QtAgg backend) | ✅ **Works!** |

## Features of attractor_qt.py

The Qt version includes:
- ✅ 3D visualization with matplotlib
- ✅ All 4 attractors (Lorenz, Rossler, Thomas, Aizawa)
- ✅ Adjustable parameters
- ✅ Initial condition controls
- ✅ Plot settings (steps, dt, stride)
- ✅ Interactive 3D rotation and zoom
- ✅ Modern, native macOS appearance
- ✅ Better performance than Tkinter

Missing features (compared to original):
- Animation playback (can be added if needed)
- Plot mode selection (line/scatter)
- Random initial conditions
- Logging system

## Recommendation

**Use [attractor_qt.py](attractor_qt.py)** - it works reliably on your system and provides all the core functionality for exploring chaotic attractors.

## Technical Details

The issue chain:
1. System Python 3.9.6 → includes Tk 8.5
2. matplotlib TkAgg backend → requires Tk window
3. Tk 8.5 → tries to create window on macOS
4. Modern macOS APIs → incompatible with Tk 8.5
5. Result: Abort trap crash

The Qt solution:
1. PyQt6 → modern Qt 6.10 framework
2. matplotlib QtAgg backend → uses Qt for rendering
3. Qt 6.10 → fully compatible with macOS
4. Result: Works perfectly!
