# Attractor Explorer - Project Guide for LLM Agents

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Key Design Patterns](#key-design-patterns)
- [Code Organization](#code-organization)
- [Dependencies and Tools](#dependencies-and-tools)
- [Development Workflow](#development-workflow)
- [Performance Considerations](#performance-considerations)
- [Testing Strategy](#testing-strategy)
- [Common Development Tasks](#common-development-tasks)
- [Code Style Guidelines](#code-style-guidelines)

## Project Overview

### Purpose
An interactive Python GUI application for visualizing four classic chaotic attractors (Lorenz, Rössler, Thomas, and Aizawa) in 3D space using PyQt6 and Matplotlib.

### Target Audience
Students, educators, and enthusiasts interested in chaos theory, nonlinear dynamics, and scientific visualization.

### Core Functionality
- Real-time 3D visualization of chaotic attractors
- Interactive parameter adjustment with physics tooltips
- Multiple rendering modes (line, scatter, combined)
- Performance monitoring (FPS/memory)
- Dark/light theme support
- Configurable plot settings (steps, time step, stride)

## Architecture

### Single-Class Design
The application uses a monolithic design with one main class: `AttractorWindow(QMainWindow)`.

**Rationale:**
- Simplicity: All state and behavior in one place
- Small codebase (~788 lines)
- Tight coupling between UI and plotting logic makes separation unnecessary
- Easy to understand and modify for educational purposes

### Component Structure

```
AttractorWindow
├── UI Components
│   ├── Left Panel (scrollable control panel)
│   │   ├── Attractor selector dropdown
│   │   ├── Parameter fields (dynamic)
│   │   └── Initial conditions (x0, y0, z0)
│   └── Right Panel (plot area ~81% of figure)
│       ├── Matplotlib 3D canvas
│       │   ├── Equations overlay (upper left)
│       │   ├── Stats overlay (lower left, optional)
│       │   └── 10% closer default zoom
│       ├── Navigation toolbar
│       └── Info button
├── Menu System
│   ├── File (Quit)
│   ├── Settings (colors, draw modes, grid, axis, dark mode, stats)
│   ├── View (panel toggle)
│   ├── Plot (create, settings dialog, reset view)
│   └── About (application info, license)
└── State Management
    ├── Plot data cache (self.data)
    ├── Visual settings (colors, modes, flags)
    ├── Text overlays (equations_text, stats_text)
    ├── Integration parameters (steps, dt, stride)
    └── Animation steps field (synced with Plot Settings)
```

### Data Flow

1. **User Input** → Parameter fields / Menu actions
2. **Integration** → RK4 numerical integration (rk4_integrate function)
3. **Data Cache** → Stored in self.data (numpy array)
4. **Rendering** → Matplotlib 3D plot with visual settings applied
5. **Display** → Qt canvas with hardware acceleration

## Key Design Patterns

### 1. Helper Method Pattern (DRY Principle)

**Problem:** Visual settings (dark mode, grid, axis) were duplicated across multiple methods (~95 lines).

**Solution:** Extract common logic into reusable helper methods.

**Implementation:**
```python
def _apply_color_theme(self):
    """Apply dark mode or light mode colors to the plot."""
    if self.dark_mode:
        bg_color, text_color = '#2b2b2b', 'white'
    else:
        bg_color, text_color = 'white', 'black'

    # Apply to all plot elements
    self.fig.patch.set_facecolor(bg_color)
    self.ax.set_facecolor(bg_color)
    # ... apply to panes, ticks, labels

def _apply_grid_settings(self):
    """Apply grid visibility and pane fill settings."""
    self.ax.grid(self.show_grid)
    fill = self.show_grid
    self.ax.xaxis.pane.fill = fill
    self.ax.yaxis.pane.fill = fill
    self.ax.zaxis.pane.fill = fill

def _apply_axis_settings(self):
    """Apply axis visibility settings."""
    self.ax.set_axis_on() if self.show_axis else self.ax.set_axis_off()

def _apply_tick_settings(self):
    """Limit number of ticks to 5 per axis for cleaner visualization."""
    from matplotlib.ticker import MaxNLocator
    self.ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    self.ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    self.ax.zaxis.set_major_locator(MaxNLocator(nbins=5))
```

**Usage:** Called from `create_plot()`, `_redraw_plot()`, `play_animation()`, and `reset_animation()` to ensure consistent application.

### 2. Cached Redraw Pattern (Performance Optimization)

**Problem:** Toggle operations (draw mode, grid, colors) were calling `create_plot()`, which re-ran expensive RK4 integration (~200ms for 10k points).

**Solution:** Separate integration from rendering. Cache computed data and only redraw visuals.

**Implementation:**
```python
def _redraw_plot(self):
    """Redraw plot using cached data without recomputing."""
    if self.data is None:
        return

    # Clear stats and equations text BEFORE ax.clear() to prevent memory leak
    if self.stats_text:
        self.stats_text.remove()
        self.stats_text = None
    if self.equations_text:
        self.equations_text.remove()
        self.equations_text = None

    self.ax.clear()
    self.ax.set_xlabel("x")
    self.ax.set_ylabel("y")
    self.ax.set_zlabel("z")

    x, y, z = self.data[:, 0], self.data[:, 1], self.data[:, 2]

    # Draw based on settings
    if self.draw_line:
        self.ax.plot(x, y, z, color=self.line_color, linewidth=0.6, alpha=0.9)
    if self.draw_scatter:
        self.ax.scatter(x, y, z, c=self.scatter_color, s=1, alpha=0.6)

    # Apply all visual settings using helpers
    self._apply_grid_settings()
    self._apply_axis_settings()
    self._apply_color_theme()
    self._apply_tick_settings()

    # Update stats and equations if enabled
    if self.show_stats:
        self.update_stats()
    self.update_equations()

    self.canvas.draw()
```

**Performance Impact:** 70% faster toggle operations (from ~200ms to <60ms).

### 3. Data-Driven Configuration Pattern

**Problem:** Each attractor has different parameters, equations, tooltips, and descriptions.

**Solution:** Centralized ATTRACTORS dictionary containing all attractor metadata.

**Implementation:**
```python
ATTRACTORS = {
    "Lorenz": {
        "deriv": lorenz,                    # Derivative function
        "params": {"sigma": 10.0, ...},     # Default parameters
        "init": [0.1, 0.0, 0.0],            # Initial conditions
        "equations": ["dx/dt = ...", ...],   # LaTeX-style equations
        "description": "The Lorenz ...",     # Educational description
        "tooltips": {"sigma": "Prandtl..."} # Parameter explanations
    },
    # ... similar for Rossler, Thomas, Aizawa
}
```

**Benefits:**
- Easy to add new attractors (just add to dictionary)
- All metadata in one place
- UI dynamically rebuilds from data
- No hard-coded attractor logic in UI code

### 4. Module-Level Imports (Performance)

**Anti-Pattern:** Importing libraries inside methods.
```python
# BAD - imports on every call
def update_stats(self):
    import psutil
    import time
    # ...
```

**Correct Pattern:** Import at module level.
```python
# GOOD - imports once at startup
import psutil
import time

def update_stats(self):
    # ... use psutil and time directly
```

## Code Organization

### File Structure

```
Attractors/
├── attractors.py          # Main application (~788 lines)
│   ├── Derivative functions (lorenz, rossler, thomas, aizawa)
│   ├── ATTRACTORS dictionary (metadata)
│   ├── rk4_integrate() function
│   └── AttractorWindow class (UI and logic)
│       ├── UI with equations overlay (not in left panel)
│       ├── Maximized plot area (~81% of figure)
│       ├── 5 ticks per axis for cleaner appearance
│       └── 10% closer default zoom
│
├── test_attractors.py     # Validation tests (64 lines)
│   └── Tests for each attractor's computation
│
├── requirements.txt       # Python dependencies
├── README.md              # User documentation (detailed)
├── QUICK_REFERENCE.md     # Quick reference guide
├── PROJECT_GUIDE.md       # This file (developer guide)
│
├── .gitignore             # Git ignore patterns
├── venv/                  # Virtual environment (Python 3.13)
└── logs/                  # Application logs (auto-created)
```

### Code Sections in attractors.py

**Lines 1-12:** Imports and matplotlib backend setup
**Lines 14-51:** Derivative functions for each attractor
**Lines 54-119:** ATTRACTORS metadata dictionary
**Lines 121-138:** rk4_integrate() function (numerical integration)
**Lines 141-788:** AttractorWindow class
  - **Lines 143-393:** `_build_ui()` - UI construction (no equations QGroupBox)
  - **Lines 218-326:** `_build_menus()` - Menu system
  - **Lines 328-333:** `on_attractor_changed()` - Selector handler
  - **Lines 335-570:** Helper methods (_apply_*, _redraw_plot, update_equations)
  - **Lines 401-450:** UI callbacks and dialogs
  - **Lines 452-484:** `create_plot()` - Main integration and plotting
  - **Lines 673-698:** `update_equations()` - Equations overlay rendering

## Dependencies and Tools

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.13+ | Runtime environment |
| numpy | ≥1.24.0 | Numerical computing, array operations |
| matplotlib | ≥3.9.0 | Scientific plotting, 3D visualization |
| PyQt6 | ≥6.4.0 | GUI framework |
| psutil | ≥5.9.0 | System monitoring (FPS/memory) |

### Why These Versions?

- **Python 3.13:** Latest stable, Tk 9.0 support (previous Tk 8.5 had crashing issues)
- **numpy 2.4+:** Latest performance improvements
- **matplotlib 3.9+:** Modern 3D rendering, better Qt integration
- **PyQt6:** Latest Qt framework with hardware acceleration
- **psutil 5.9+:** Cross-platform system monitoring

### Virtual Environment

```bash
# Create environment
python3.13 -m venv venv

# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Development Workflow

### Setting Up

1. Clone/navigate to project directory
2. Create virtual environment: `python3.13 -m venv venv`
3. Activate: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `python test_attractors.py`
6. Launch app: `python attractors.py`

### Making Changes

#### Adding a New Attractor

1. **Define derivative function:**
```python
def new_attractor(state, params):
    x, y, z = state
    a, b = params['a'], params['b']
    dx = # ... your equation
    dy = # ... your equation
    dz = # ... your equation
    return np.array([dx, dy, dz], dtype=float)
```

2. **Add to ATTRACTORS dictionary:**
```python
"NewAttractor": {
    "deriv": new_attractor,
    "params": {"a": 1.0, "b": 2.0},
    "init": [0.1, 0.0, 0.0],
    "equations": ["dx/dt = ...", "dy/dt = ...", "dz/dt = ..."],
    "description": "Historical and mathematical description...",
    "tooltips": {"a": "Explanation of parameter a", "b": "..."}
}
```

3. **Add test in test_attractors.py:**
```python
# Test will automatically pick up new attractor from ATTRACTORS
```

4. **Test:** Run `python test_attractors.py` to verify

#### Adding a New Menu Action

1. **Add menu item in `_build_menus()`:**
```python
new_action = QAction("New Feature", self, checkable=True)
new_action.setShortcut("Ctrl+N")
new_action.triggered.connect(self.handle_new_feature)
menu.addAction(new_action)
```

2. **Implement handler:**
```python
def handle_new_feature(self):
    # Implement logic
    self.statusBar().showMessage("Feature activated")
```

#### Modifying Visual Settings

- Always use helper methods (`_apply_color_theme()`, etc.)
- Update both `create_plot()` and `_redraw_plot()` if needed
- Test with toggle operations to ensure caching works

### Testing

```bash
# Run all tests
python test_attractors.py

# Should output:
# Testing Lorenz attractor...
# ✓ Lorenz attractor test passed
# [... similar for others ...]
# ✓ All 4 attractor tests passed
```

**What tests verify:**
- Each attractor's derivative function works
- RK4 integration produces valid trajectories
- Output shape matches expected (steps × 3)
- No NaN or Inf values in results

## Performance Considerations

### Bottlenecks

1. **RK4 Integration** (~200ms for 20k steps)
   - Most expensive operation
   - Scales linearly with steps
   - Cannot be optimized without changing algorithm

2. **Matplotlib Rendering** (~50ms for 10k points)
   - 3D plotting is inherently slow
   - Hardware acceleration helps
   - Stride parameter reduces point count

3. **Memory Usage** (~235 MB loaded)
   - Mostly matplotlib/Qt overhead
   - Data arrays are small (20k × 3 × 8 bytes = ~480 KB)

### Optimization Strategies Applied

1. **Cached Redrawing** (70% speedup for toggles)
   - Store `self.data` after integration
   - Reuse for visual setting changes
   - Only re-integrate when parameters change

2. **Helper Methods** (eliminates ~95 lines duplication)
   - DRY principle
   - Consistent behavior
   - Easier maintenance

3. **Module-Level Imports** (faster startup)
   - Import libraries once
   - No repeated import overhead

4. **Memory Leak Prevention**
   - Clear stats_text and equations_text before ax.clear()
   - Prevents orphaned matplotlib objects

5. **Maximized Plot Area** (27% more viewing area)
   - Reduced margins from default 10% to 5% on all sides
   - Plot area increased from ~64% to ~81% of figure
   - Applied via `fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)`

6. **Cleaner Axes** (professional appearance)
   - Limited to 5 ticks per axis using MaxNLocator
   - Reduces clutter while maintaining readability
   - Applied consistently across all plotting methods

7. **Enhanced Default View** (better initial visualization)
   - Default zoom increased 10% (`self.ax.dist = 10 * 0.9`)
   - Provides better detail in initial view

### Performance Targets

- **FPS:** 55-60 fps (achieved)
- **Plot time:** <250ms for 20k points (achieved: ~200ms)
- **Toggle time:** <100ms (achieved: <60ms with caching)
- **Memory:** <300 MB (achieved: ~235 MB)

## Testing Strategy

### Unit Tests (test_attractors.py)

**What's tested:**
- Each attractor's derivative function
- RK4 integration correctness
- Output data validity (no NaN/Inf)
- Array shape correctness

**What's NOT tested:**
- UI components (would require Qt test framework)
- Visual rendering (subjective)
- User interactions (manual testing)

**Rationale:** Focus on mathematical correctness. UI is simple enough for manual testing.

### Manual Testing Checklist

When making changes, verify:
- [ ] All attractors plot correctly
- [ ] Parameter changes update plot
- [ ] Color pickers work
- [ ] Draw mode toggles work (line/scatter)
- [ ] Grid/axis toggles work
- [ ] Dark mode toggles theme
- [ ] FPS/memory display updates
- [ ] Info button shows correct descriptions
- [ ] Panel toggle hides/shows controls
- [ ] Plot settings dialog updates values
- [ ] Keyboard shortcuts work (Ctrl+R, Ctrl+P, Ctrl+Q)
- [ ] No errors in terminal/logs

## Common Development Tasks

### Debugging Integration Issues

```python
# Add debug prints in rk4_integrate
def rk4_integrate(deriv, initial, params, dt, steps):
    trajectory = np.zeros((steps, 3), dtype=float)
    state = initial.copy()

    for i in range(steps):
        # Debug print every 1000 steps
        if i % 1000 == 0:
            print(f"Step {i}: state = {state}")

        k1 = deriv(state, params)
        # ... rest of RK4
```

### Adding New Visual Settings

1. Add state variable: `self.new_setting = default_value`
2. Add menu action in `_build_menus()`
3. Add toggle method: `def toggle_new_setting(self):`
4. Update `_redraw_plot()` to apply setting
5. Test with existing plot

### Profiling Performance

```python
import time

def create_plot(self):
    start = time.time()
    # ... integration code
    integrate_time = time.time() - start
    print(f"Integration: {integrate_time*1000:.1f}ms")

    start = time.time()
    # ... plotting code
    plot_time = time.time() - start
    print(f"Plotting: {plot_time*1000:.1f}ms")
```

### Handling Errors

- Use try/except in `create_plot()` for parameter validation
- Show QMessageBox for user-facing errors
- Log to statusBar for minor issues
- Print to console for debugging

## Code Style Guidelines

### Python Style

- Follow PEP 8 generally
- Use descriptive variable names
- Max line length: ~100 characters (flexible)
- Docstrings for helper methods
- Type hints not required (but accepted)

### Naming Conventions

- **Classes:** PascalCase (`AttractorWindow`)
- **Functions:** snake_case (`rk4_integrate`)
- **Methods:** snake_case (`create_plot`)
- **Private methods:** Leading underscore (`_apply_color_theme`)
- **Constants:** UPPER_CASE (`ATTRACTORS`)
- **Variables:** snake_case (`line_color`)

### Comments

- Explain WHY, not WHAT
- Document non-obvious behavior
- Explain mathematical concepts
- Mark performance-critical sections

**Good:**
```python
# Clear stats before ax.clear() to prevent memory leak
if self.stats_text:
    self.stats_text.remove()
```

**Bad:**
```python
# Remove stats text
if self.stats_text:
    self.stats_text.remove()
```

### Method Organization

1. Initialization (`__init__`)
2. UI building (`_build_ui`, `_build_menus`)
3. Event handlers (`on_attractor_changed`, toggles)
4. Helper methods (`_apply_*`, `_redraw_plot`)
5. Dialog methods (`show_plot_settings`, `show_attractor_info`)
6. Main logic (`create_plot`)

### Import Organization

1. Standard library (sys)
2. Third-party numerical (numpy)
3. Third-party GUI (matplotlib, PyQt6)
4. Local imports (if any)

Separate groups with blank lines.

## Future Enhancement Ideas

### Short-term
- Export plot as PNG/SVG
- Save/load parameter presets
- Animation recording
- More color schemes

### Medium-term
- Additional attractors (Dadras, Chen, Halvorsen)
- Parameter sweep animations
- Bifurcation diagrams
- Poincaré sections

### Long-term
- GPU acceleration for integration
- Real-time parameter sliders
- Multiple attractors in one view
- Phase space analysis tools

## Notes for LLM Agents

### Key Principles
1. **Maintain simplicity** - Don't over-engineer
2. **Preserve educational value** - Keep code readable
3. **Respect performance optimizations** - Don't revert cached redraw pattern
4. **Use helper methods** - Don't duplicate visual setting code
5. **Test after changes** - Run test_attractors.py

### Common Pitfalls to Avoid
- Importing libraries inside methods (performance)
- Duplicating visual settings code (use helpers: _apply_tick_settings, etc.)
- Breaking cached redraw by removing self.data
- Creating memory leaks (clear stats_text AND equations_text before ax.clear())
- Calling create_plot() for visual-only changes (use _redraw_plot())
- Removing plot title (already removed for cleaner interface)
- Changing plot margins (optimized at 5% for ~81% plot area)
- Modifying default zoom (set to 10% closer for better detail)

### When Making Changes
- Always read relevant code sections first
- Understand the helper method pattern
- Preserve the data caching pattern
- Update tests if adding attractors
- Update documentation if changing features
- Test manually with the checklist above
