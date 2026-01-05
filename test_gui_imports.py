#!/usr/bin/env python3
"""Test that all GUI imports work correctly."""

import sys

print("Testing GUI imports...")
print("=" * 60)

try:
    print("Importing tkinter...")
    import tkinter as tk
    from tkinter import ttk, messagebox
    print("  ✓ tkinter imported successfully")
except ImportError as e:
    print(f"  ✗ Error importing tkinter: {e}")
    sys.exit(1)

try:
    print("Importing numpy...")
    import numpy as np
    print(f"  ✓ numpy {np.__version__} imported successfully")
except ImportError as e:
    print(f"  ✗ Error importing numpy: {e}")
    sys.exit(1)

try:
    print("Importing matplotlib...")
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.backends._backend_tk import NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    print(f"  ✓ matplotlib {matplotlib.__version__} imported successfully")
    print(f"  ✓ TkAgg backend available")
    print(f"  ✓ 3D toolkit available")
except ImportError as e:
    print(f"  ✗ Error importing matplotlib: {e}")
    sys.exit(1)

try:
    print("Importing attractor_gui module...")
    from attractor_gui import (
        lorenz, rossler, thomas, aizawa,
        rk4_integrate, ATTRACTORS, AttractorApp
    )
    print("  ✓ All attractor functions imported")
    print(f"  ✓ {len(ATTRACTORS)} attractors available: {', '.join(ATTRACTORS.keys())}")
except ImportError as e:
    print(f"  ✗ Error importing attractor_gui: {e}")
    sys.exit(1)

print("=" * 60)
print("✓ All imports successful!")
print("\nThe GUI should now work. Try running:")
print("  python attractor_gui.py")
print("=" * 60)
