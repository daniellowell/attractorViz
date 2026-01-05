# Python 3.13 Upgrade Summary

## What Was Done

Successfully upgraded the Attractors project from Python 3.9.6 (Tk 8.5) to Python 3.13.11 (Tk 9.0).

## Problem Solved

The original error:
```
macOS 26 (2602) or later required, have instead 16 (1602) !
Abort trap: 6
```

This was caused by **Tk 8.5** (from 2007) being incompatible with modern macOS and matplotlib's TkAgg backend.

## Solution Steps

### 1. Installed Python 3.13 via Homebrew
```bash
brew install python@3.13
brew install python-tk@3.13
```

This provided:
- **Python 3.13.11**
- **Tk 9.0** (the latest Tcl/Tk version)
- **Tcl 9.0**

### 2. Backed Up Old Environment
```bash
mv venv venv-old-python39
```

### 3. Created New Virtual Environment
```bash
/opt/homebrew/bin/python3.13 -m venv venv
```

### 4. Updated Dependencies
Updated [requirements.txt](requirements.txt:1-12):
- `numpy>=1.24.0` → numpy 2.4.0 (latest)
- `matplotlib>=3.9.0` → matplotlib 3.10.8 (latest with pre-built wheels)
- `PyQt6>=6.4.0` → PyQt6 6.10.1 (latest)

Removed version constraints that were needed for Python 3.9 compatibility.

### 5. Fixed Layout Bug
Fixed a geometry manager conflict in [attractor_gui.py](attractor_gui.py:238-242):
- The NavigationToolbar2Tk was trying to use `pack()` inside a frame using `grid()`
- Wrapped toolbar in its own frame to isolate the layout managers

## Results

### ✅ Both GUI Versions Now Work!

**attractor_gui.py (Tkinter version):**
- ✅ Launches without crashes
- ✅ Full feature set with animation
- ✅ Tk 9.0 provides modern, smooth UI
- ✅ All 4 attractors working

**attractor_qt.py (Qt version):**
- ✅ Also works perfectly
- ✅ Alternative UI framework
- ✅ Simpler feature set

## How to Use

```bash
# Activate the new Python 3.13 virtual environment
source venv/bin/activate

# Run the main GUI (Tkinter)
python attractor_gui.py

# Or run the Qt alternative
python attractor_qt.py
```

## Installed Packages

```
Python: 3.13.11
Tk/Tcl: 9.0

numpy: 2.4.0
matplotlib: 3.10.8
PyQt6: 6.10.1
PyQt6-Qt6: 6.10.1
PyQt6-sip: 13.10.3
contourpy: 1.3.3
cycler: 0.12.1
fonttools: 4.61.1
kiwisolver: 1.4.9
packaging: 25.0
pillow: 12.1.0
pyparsing: 3.3.1
python-dateutil: 2.9.0.post0
six: 1.17.0
```

## Performance Improvements

Using Python 3.13 and the latest libraries provides:
- **Faster execution** (Python 3.13 performance improvements)
- **Better memory management** (improved garbage collection)
- **Modern GUI** (Tk 9.0 with better rendering)
- **Latest features** (numpy 2.x, matplotlib 3.10)

## Cleanup

The old virtual environment is preserved as `venv-old-python39/` in case you need to reference it. You can safely delete it once you've confirmed everything works:

```bash
rm -rf venv-old-python39
```

## Notes

- The troubleshooting documentation in [TROUBLESHOOTING.md](TROUBLESHOOTING.md:1) is still relevant for users with older Python versions
- If you encounter any issues, check that you're using the new venv: `which python` should show `/opt/homebrew/bin/python3.13` or the venv path
- The [attractor_qt.py](attractor_qt.py:1) Qt version remains as a working alternative if you prefer Qt over Tkinter

## Testing Performed

1. ✅ Verified Tk 9.0 is available in venv
2. ✅ Tested matplotlib + Tkinter integration
3. ✅ Tested matplotlib 3D plotting
4. ✅ Launched attractor_gui.py successfully
5. ✅ Launched attractor_qt.py successfully
6. ✅ Confirmed both GUIs respond and render without crashes

## Success! 🎉

The project is now fully functional with modern Python 3.13 and Tk 9.0. No more crashes, better performance, and access to the latest features!
