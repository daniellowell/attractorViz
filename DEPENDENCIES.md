# Attractors Project - Dependency List

## Core Dependencies

### Python 3.9+
**Purpose:** Programming language runtime
**Why needed:** Project uses modern Python features and type hints

### numpy >= 1.24.0
**Purpose:** Numerical computing library
**Why needed:**
- Array operations for state vectors
- RK4 numerical integration
- Random number generation for initial conditions
- Mathematical operations (sin, array arithmetic)

### matplotlib >= 3.7.0
**Purpose:** Plotting and visualization library
**Why needed:**
- 3D plotting via `mpl_toolkits.mplot3d`
- Interactive plot canvas
- Animation support
- Toolbar for rotation/zoom controls
- TkAgg backend for Tkinter integration

### tkinter (built-in)
**Purpose:** GUI framework
**Why needed:**
- Main application window
- Control widgets (buttons, entries, comboboxes)
- Layout management
- Event handling
- Dialog boxes

## Transitive Dependencies

These are installed automatically with matplotlib:

### contourpy 1.3.0
**Purpose:** Contour calculation for matplotlib

### cycler 0.12.1
**Purpose:** Composable style cycles for matplotlib

### fonttools 4.60.2
**Purpose:** Font manipulation for matplotlib text rendering

### kiwisolver 1.4.7
**Purpose:** Constraint solver for matplotlib layouts

### packaging 25.0
**Purpose:** Version parsing for dependency management

### pillow 11.3.0
**Purpose:** Image library for matplotlib figure export

### pyparsing 3.3.1
**Purpose:** Text parsing for matplotlib math expressions

### python-dateutil 2.9.0.post0
**Purpose:** Date/time utilities for matplotlib axes

### importlib-resources 6.5.2
**Purpose:** Resource access for Python 3.9 compatibility

### six 1.17.0
**Purpose:** Python 2/3 compatibility utilities

### zipp 3.23.0
**Purpose:** Backport of zipfile features

## Development Environment

### Virtual Environment (venv/)
**Purpose:** Isolated Python environment
**Why needed:**
- Prevents dependency conflicts
- Reproducible setup
- Clean project isolation

## Installation Summary

```bash
# Create virtual environment
python3 -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Dependency Tree

```
Attractors Project
├── Python 3.9+
├── numpy 2.0.2
└── matplotlib 3.9.4
    ├── contourpy 1.3.0
    ├── cycler 0.12.1
    ├── fonttools 4.60.2
    ├── kiwisolver 1.4.7
    ├── packaging 25.0
    ├── pillow 11.3.0
    ├── pyparsing 3.3.1
    ├── python-dateutil 2.9.0.post0
    │   └── six 1.17.0
    └── importlib-resources 6.5.2
        └── zipp 3.23.0
```

## Version Constraints

The minimum versions are specified for compatibility:
- **numpy >= 1.24.0**: Ensures modern array API and typing support
- **matplotlib >= 3.7.0**: Required for stable 3D plotting and TkAgg backend

## Platform Compatibility

The project is cross-platform:
- macOS (tested on macOS 14 ARM64)
- Linux (any distribution with Python 3.9+)
- Windows (with Python 3.9+)

Note: tkinter must be available in your Python installation. Some minimal Python installations may require separate tkinter installation.
