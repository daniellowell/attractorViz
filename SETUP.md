# Attractors Project - Setup Guide

## Project Overview
Interactive Python GUI for visualizing classic chaotic attractors (Lorenz, Rossler, Thomas, Aizawa) using Tkinter and Matplotlib 3D.

## Dependencies

The project requires:
- Python 3.9 or later
- numpy >= 1.24.0 (numerical computations)
- matplotlib >= 3.7.0 (3D plotting)
- tkinter (included with Python)

## Setup Instructions

### 1. Virtual Environment Created
A virtual environment has been set up in `venv/` directory.

### 2. Activate the Virtual Environment

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 3. Dependencies Installed
All required packages are already installed via:
```bash
pip install -r requirements.txt
```

## Running the Application

### Main GUI Application
```bash
python attractor_gui.py
```

### Alternative Explorer
```bash
python attractor_explorer.py
```

### Test Script
To validate the core functionality without GUI:
```bash
python test_attractors.py
```

## Installed Packages

- numpy 2.0.2
- matplotlib 3.9.4
- contourpy 1.3.0
- cycler 0.12.1
- fonttools 4.60.2
- kiwisolver 1.4.7
- packaging 25.0
- pillow 11.3.0
- pyparsing 3.3.1
- python-dateutil 2.9.0.post0
- importlib-resources 6.5.2
- six 1.17.0
- zipp 3.23.0

## Features

- Dropdown to select attractor type
- Editable parameters and initial conditions
- Random seed + range for randomized initial conditions
- Plot settings: steps, dt, burn-in, stride, point size
- Plot modes: line, scatter, or line+scatter
- Play/Pause animation with configurable step and delay
- Mouse rotation and zoom via Matplotlib toolbar
- Error reporting dialog + log file in `logs/`

## Validation Results

All attractor computations have been validated:
- ✓ Lorenz attractor
- ✓ Rossler attractor
- ✓ Thomas attractor
- ✓ Aizawa attractor

Each system correctly integrates using RK4 method and produces valid trajectories.

## Project Files

- [attractor_gui.py](attractor_gui.py) - Main GUI application with logging
- [attractor_explorer.py](attractor_explorer.py) - Alternative simplified GUI
- [test_attractors.py](test_attractors.py) - Validation test script
- [requirements.txt](requirements.txt) - Python dependencies
- [README.md](README.md) - User documentation
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Architecture notes
- `venv/` - Virtual environment directory
- `logs/` - Runtime logs (created on first run)

## Troubleshooting

If you encounter issues:
1. Ensure you've activated the virtual environment
2. Check that Python 3.9+ is installed: `python --version`
3. Review logs in `logs/attractor_gui.log` for detailed error messages
4. Run the test script to verify core functionality

## Next Steps

The project is ready to use! Simply activate the virtual environment and run the GUI:
```bash
source venv/bin/activate  # or venv\Scripts\activate on Windows
python attractor_gui.py
```
