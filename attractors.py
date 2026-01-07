"""Enhanced Qt GUI for exploring classic chaotic attractors in 3D."""

import sys
import time
import numpy as np
import psutil
import matplotlib
matplotlib.use('QtAgg')

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

try:
    from PyQt6 import QtWidgets, QtCore, QtGui
    from PyQt6.QtWidgets import *
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QAction
except ImportError:
    print("ERROR: PyQt6 is required. Install with: pip install PyQt6")
    sys.exit(1)


def lorenz(state, p):
    """Compute derivatives for the Lorenz attractor system.

    Args:
        state: Current state [x, y, z]
        p: Parameter dictionary with keys: sigma, rho, beta

    Returns:
        Array of derivatives [dx/dt, dy/dt, dz/dt]
    """
    x, y, z = state
    dx = p["sigma"] * (y - x)
    dy = x * (p["rho"] - z) - y
    dz = x * y - p["beta"] * z
    return np.array([dx, dy, dz], dtype=float)


def rossler(state, p):
    """Compute derivatives for the Rössler attractor system.

    Args:
        state: Current state [x, y, z]
        p: Parameter dictionary with keys: a, b, c

    Returns:
        Array of derivatives [dx/dt, dy/dt, dz/dt]
    """
    x, y, z = state
    dx = -y - z
    dy = x + p["a"] * y
    dz = p["b"] + z * (x - p["c"])
    return np.array([dx, dy, dz], dtype=float)


def thomas(state, p):
    """Compute derivatives for the Thomas attractor system.

    Args:
        state: Current state [x, y, z]
        p: Parameter dictionary with key: b

    Returns:
        Array of derivatives [dx/dt, dy/dt, dz/dt]
    """
    x, y, z = state
    b = p["b"]
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return np.array([dx, dy, dz], dtype=float)


def aizawa(state, p):
    """Compute derivatives for the Aizawa attractor system.

    Args:
        state: Current state [x, y, z]
        p: Parameter dictionary with keys: a, b, c, d, e, f

    Returns:
        Array of derivatives [dx/dt, dy/dt, dz/dt]
    """
    x, y, z = state
    dx = (z - p["b"]) * x - p["d"] * y
    dy = p["d"] * x + (z - p["b"]) * y
    dz = p["c"] + p["a"] * z - (z ** 3) / 3 - (x ** 2 + y ** 2) * (1 + p["e"] * z) + p["f"] * z * (x ** 3)
    return np.array([dx, dy, dz], dtype=float)


ATTRACTORS = {
    "Lorenz": {
        "deriv": lorenz,
        "params": {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
        "init": [0.1, 0.0, 0.0],
        "equations": [
            "dx/dt = σ(y - x)",
            "dy/dt = x(ρ - z) - y",
            "dz/dt = xy - βz"
        ],
        "description": "The Lorenz attractor is a set of chaotic solutions to the Lorenz system, discovered by Edward Lorenz in 1963. It represents a simplified model of atmospheric convection and is one of the most iconic examples of chaos theory. The system exhibits sensitive dependence on initial conditions - the famous 'butterfly effect'. The attractor has a distinctive butterfly or figure-8 shape with two lobes.",
        "tooltips": {
            "sigma": "Prandtl number - ratio of momentum to thermal diffusivity",
            "rho": "Rayleigh number - temperature difference driving convection",
            "beta": "Geometric factor related to physical dimensions"
        }
    },
    "Rossler": {
        "deriv": rossler,
        "params": {"a": 0.2, "b": 0.2, "c": 5.7},
        "init": [0.0, 1.0, 0.0],
        "equations": [
            "dx/dt = -y - z",
            "dy/dt = x + ay",
            "dz/dt = b + z(x - c)"
        ],
        "description": "The Rössler attractor, discovered by Otto Rössler in 1976, is a system of three nonlinear ordinary differential equations that exhibit chaotic behavior. It was originally designed to be simpler than the Lorenz attractor while still displaying continuous chaos. The attractor produces a characteristic spiral pattern that folds back on itself, creating a band-like structure in phase space.",
        "tooltips": {
            "a": "Controls rate of rotation in xy-plane",
            "b": "Linear term in z equation",
            "c": "Controls z-height of rotation center"
        }
    },
    "Thomas": {
        "deriv": thomas,
        "params": {"b": 0.208186},
        "init": [0.1, 0.0, 0.0],
        "equations": [
            "dx/dt = sin(y) - bx",
            "dy/dt = sin(z) - by",
            "dz/dt = sin(x) - bz"
        ],
        "description": "The Thomas attractor is a cyclically symmetric chaotic system discovered by René Thomas. It features time-reversal symmetry and exhibits a smooth flowing pattern. The attractor is characterized by its elegant, intertwined looping structure that demonstrates conservative chaos. The parameter b controls the damping, with the standard value of ~0.208186 producing particularly aesthetic trajectories.",
        "tooltips": {
            "b": "Damping parameter - controls dissipation rate"
        }
    },
    "Aizawa": {
        "deriv": aizawa,
        "params": {"a": 0.95, "b": 0.7, "c": 0.6, "d": 3.5, "e": 0.25, "f": 0.1},
        "init": [0.1, 0.0, 0.0],
        "equations": [
            "dx/dt = (z - b)x - dy",
            "dy/dt = dx + (z - b)y",
            "dz/dt = c + az - z³/3 - (x² + y²)(1 + ez) + fz(x³)"
        ],
        "description": "The Aizawa attractor is a complex chaotic system with rich dynamic behavior. It produces intricate toroidal structures with multiple twisted bands. The system has six parameters that can be tuned to produce a variety of different attractor shapes, from simple limit cycles to highly complex strange attractors. The standard parameter set creates a distinctive multi-lobed structure.",
        "tooltips": {
            "a": "Linear z coefficient",
            "b": "Shift parameter for x and y equations",
            "c": "Constant term in z equation",
            "d": "Coupling coefficient between x and y",
            "e": "Nonlinear z coupling factor",
            "f": "Cubic x coupling to z"
        }
    },
}


def rk4_integrate(deriv, initial, params, dt, steps):
    """Integrate a chaotic system using 4th-order Runge-Kutta method.

    This is the classical RK4 method, which provides high accuracy for
    chaotic systems while being computationally efficient.

    Args:
        deriv: Derivative function that takes (state, params) and returns derivatives
        initial: Initial state as numpy array [x0, y0, z0]
        params: Dictionary of parameters for the derivative function
        dt: Time step size (smaller = more accurate but slower)
        steps: Number of integration steps to compute

    Returns:
        Numpy array of shape (steps, 3) containing the trajectory

    Performance:
        ~200ms for 20,000 steps on typical hardware
    """
    data = np.empty((steps, 3), dtype=float)
    data[0] = initial
    for i in range(1, steps):
        state = data[i - 1]
        k1 = deriv(state, params)
        k2 = deriv(state + 0.5 * dt * k1, params)
        k3 = deriv(state + 0.5 * dt * k2, params)
        k4 = deriv(state + dt * k3, params)
        data[i] = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
    return data


class AttractorWindow(QMainWindow):
    """Main window for the Attractor Explorer application.

    This class provides an interactive GUI for visualizing classic chaotic attractors
    in 3D space. It supports both static plotting and real-time animation modes.

    Features:
        - 4 classic attractors (Lorenz, Rössler, Thomas, Aizawa)
        - Interactive parameter adjustment with physics tooltips
        - Multiple rendering modes (line, scatter, combined)
        - Real-time animation with configurable speed and trail length
        - Dark/light theme support
        - Performance monitoring (FPS/memory)
        - Equations overlay on plot

    Performance Optimizations:
        - Cached redraw pattern: visual changes don't re-integrate
        - Memory-efficient animation with trail length limiting
        - Fixed axis scaling option to prevent bouncing
        - Helper methods to eliminate code duplication
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attractor Explorer (Qt Enhanced)")
        self.setGeometry(100, 100, 1200, 750)

        self.data = None
        self.current_attractor = None
        self.line_color = "#1f77b4"
        self.scatter_color = "#d62728"
        self.draw_line = True
        self.draw_scatter = False
        self.show_grid = True
        self.show_axis = True
        self.dark_mode = False
        self.show_stats = False

        # Plot settings (moved from left panel)
        self.steps = 20000
        self.dt = 0.01
        self.stride = 2

        # Performance tracking
        self.last_plot_time = 0
        self.stats_text = None
        self.equations_text = None  # Equations overlay on plot

        # Animation state
        self.animation_mode = False
        self.animation_running = False
        self.animation_timer = None
        self.animation_step = 0
        self.animation_data = None
        self.animation_state = None
        self.animation_scatter = None
        self.animation_speed = 30  # FPS
        self.steps_per_frame = 5
        self.animation_auto_rotate = False
        self.animation_fade = False
        self.animation_trail_length = 1000  # Number of points to keep visible
        self.animation_azim = -60
        self.animation_fixed_scale = True  # Fixed axis scaling during animation
        self.animation_axis_limits = None  # Stored axis limits

        self._build_ui()
        self._build_menus()

    def _build_ui(self):
        """Build the main user interface.

        Creates a two-panel layout:
        - Left: Scrollable control panel (max 320px wide)
        - Right: 3D plot area with equations overlay (~81% of figure)
        """
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Scrollable left panel
        self.left_panel = QScrollArea()
        self.left_panel.setWidgetResizable(True)
        self.left_panel.setMaximumWidth(320)
        scroll_content = QWidget()
        controls_layout = QVBoxLayout(scroll_content)
        self.left_panel.setWidget(scroll_content)

        # Attractor selection
        attractor_group = QGroupBox("Attractor")
        attractor_layout = QFormLayout()
        self.attractor_combo = QComboBox()
        self.attractor_combo.addItems(ATTRACTORS.keys())
        self.attractor_combo.setToolTip("Select which chaotic attractor to visualize")
        self.attractor_combo.currentTextChanged.connect(self.on_attractor_changed)
        attractor_layout.addRow("Type:", self.attractor_combo)
        attractor_group.setLayout(attractor_layout)
        controls_layout.addWidget(attractor_group)

        # Parameters
        self.params_group = QGroupBox("Parameters")
        self.params_layout = QFormLayout()
        self.param_fields = {}
        self.params_group.setLayout(self.params_layout)
        controls_layout.addWidget(self.params_group)

        # Initial conditions
        init_group = QGroupBox("Initial Conditions")
        init_layout = QFormLayout()
        self.x0_field = QLineEdit("0.1")
        self.y0_field = QLineEdit("0.0")
        self.z0_field = QLineEdit("0.0")
        self.x0_field.setToolTip("Initial X coordinate for the trajectory")
        self.y0_field.setToolTip("Initial Y coordinate for the trajectory")
        self.z0_field.setToolTip("Initial Z coordinate for the trajectory")
        init_layout.addRow("x0:", self.x0_field)
        init_layout.addRow("y0:", self.y0_field)
        init_layout.addRow("z0:", self.z0_field)
        init_group.setLayout(init_layout)
        controls_layout.addWidget(init_group)

        # Animation toggle
        self.animation_checkbox = QCheckBox("Series Animation")
        self.animation_checkbox.setToolTip("Enable real-time step-by-step animation")
        self.animation_checkbox.stateChanged.connect(self.toggle_animation_mode)
        controls_layout.addWidget(self.animation_checkbox)

        # Animation controls group (initially hidden)
        self.animation_group = QGroupBox("Animation Controls")
        animation_layout = QVBoxLayout()

        # Speed slider
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Speed (FPS):"))
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(60)
        self.speed_slider.setValue(30)
        self.speed_slider.setToolTip("Animation speed in frames per second")
        self.speed_slider.valueChanged.connect(self.update_animation_speed)
        speed_layout.addWidget(self.speed_slider)
        self.speed_label = QLabel("30")
        self.speed_label.setMinimumWidth(30)
        speed_layout.addWidget(self.speed_label)
        animation_layout.addLayout(speed_layout)

        # Total steps field (synced with Plot Settings)
        total_steps_layout = QHBoxLayout()
        total_steps_layout.addWidget(QLabel("Total Steps:"))
        self.animation_steps_field = QLineEdit(str(self.steps))
        self.animation_steps_field.setToolTip("Total integration steps (synced with Plot Settings)")
        self.animation_steps_field.textChanged.connect(self.on_animation_steps_changed)
        total_steps_layout.addWidget(self.animation_steps_field)
        animation_layout.addLayout(total_steps_layout)

        # Steps per frame slider
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Steps/Frame:"))
        self.steps_per_frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.steps_per_frame_slider.setMinimum(1)
        self.steps_per_frame_slider.setMaximum(20)
        self.steps_per_frame_slider.setValue(5)
        self.steps_per_frame_slider.setToolTip("Number of integration steps computed per frame")
        self.steps_per_frame_slider.valueChanged.connect(self.update_steps_per_frame)
        steps_layout.addWidget(self.steps_per_frame_slider)
        self.steps_per_frame_label = QLabel("5")
        self.steps_per_frame_label.setMinimumWidth(30)
        steps_layout.addWidget(self.steps_per_frame_label)
        animation_layout.addLayout(steps_layout)

        # Control buttons
        anim_btn_layout = QHBoxLayout()
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self.play_animation)
        self.play_btn.setToolTip("Start the animation")
        anim_btn_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self.pause_animation)
        self.pause_btn.setToolTip("Pause the animation")
        self.pause_btn.setEnabled(False)
        anim_btn_layout.addWidget(self.pause_btn)

        self.reset_anim_btn = QPushButton("↻ Reset")
        self.reset_anim_btn.clicked.connect(self.reset_animation)
        self.reset_anim_btn.setToolTip("Clear and restart animation")
        anim_btn_layout.addWidget(self.reset_anim_btn)
        animation_layout.addLayout(anim_btn_layout)

        # Progress label
        self.progress_label = QLabel("Progress: 0 / 20,000")
        self.progress_label.setStyleSheet("font-family: 'Courier New', Monaco, monospace;")
        animation_layout.addWidget(self.progress_label)

        # Animation options
        self.auto_rotate_checkbox = QCheckBox("Auto-rotate view")
        self.auto_rotate_checkbox.setToolTip("Slowly rotate the view during animation")
        self.auto_rotate_checkbox.stateChanged.connect(self.toggle_auto_rotate)
        animation_layout.addWidget(self.auto_rotate_checkbox)

        self.fade_checkbox = QCheckBox("Fade old points")
        self.fade_checkbox.setToolTip("Gradually fade older points for comet tail effect")
        self.fade_checkbox.stateChanged.connect(self.toggle_fade)
        animation_layout.addWidget(self.fade_checkbox)

        # Trail length slider
        trail_layout = QHBoxLayout()
        trail_layout.addWidget(QLabel("Trail Length:"))
        self.trail_length_slider = QSlider(Qt.Orientation.Horizontal)
        self.trail_length_slider.setMinimum(100)
        self.trail_length_slider.setMaximum(5000)
        self.trail_length_slider.setValue(1000)
        self.trail_length_slider.setToolTip("Number of points to keep visible (affects memory usage)")
        self.trail_length_slider.valueChanged.connect(self.update_trail_length)
        trail_layout.addWidget(self.trail_length_slider)
        self.trail_length_label = QLabel("1000")
        self.trail_length_label.setMinimumWidth(50)
        trail_layout.addWidget(self.trail_length_label)
        animation_layout.addLayout(trail_layout)

        # Fixed scale checkbox
        self.fixed_scale_checkbox = QCheckBox("Fixed axis scaling")
        self.fixed_scale_checkbox.setChecked(True)
        self.fixed_scale_checkbox.setToolTip("Keep axis limits fixed to prevent bouncing when points are added/removed")
        self.fixed_scale_checkbox.stateChanged.connect(self.toggle_fixed_scale)
        animation_layout.addWidget(self.fixed_scale_checkbox)

        self.animation_group.setLayout(animation_layout)
        self.animation_group.setVisible(False)
        controls_layout.addWidget(self.animation_group)

        # Buttons (shown when not in animation mode)
        self.buttons_widget = QWidget()
        btn_layout = QHBoxLayout(self.buttons_widget)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.create_btn = QPushButton("Create Plot")
        self.create_btn.clicked.connect(self.create_plot)
        self.create_btn.setToolTip("Generate and display the attractor with current settings")
        btn_layout.addWidget(self.create_btn)

        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setToolTip("Reset parameters and initial conditions to default values")
        btn_layout.addWidget(self.reset_btn)

        controls_layout.addWidget(self.buttons_widget)

        controls_layout.addStretch()

        # Right panel - plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)

        # Custom toolbar with info button
        toolbar_container = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_container)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        # Adjust subplot to fill ~80% of the figure (reduce margins)
        self.fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        # Set default zoom (10% closer than default)
        self.ax.dist = 10 * 0.9  # Default is 10, so 9 zooms in 10%
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, toolbar_container)

        # Add info button to toolbar
        self.info_btn = QPushButton("?")
        self.info_btn.setMaximumWidth(30)
        self.info_btn.setToolTip("Information about current attractor")
        self.info_btn.clicked.connect(self.show_attractor_info)

        toolbar_layout.addWidget(self.toolbar)
        toolbar_layout.addWidget(self.info_btn)

        plot_layout.addWidget(toolbar_container)
        plot_layout.addWidget(self.canvas)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Add to main layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(plot_widget)

        # Initialize
        self.rebuild_params()
        # Display equations at startup
        self.update_equations()
        self.canvas.draw()

    def _build_menus(self):
        """Build the menu system.

        Menus:
            File: Quit
            Settings: Colors, draw modes, grid, axis, dark mode, stats
            View: Control panel toggle
            Plot: Create, settings dialog, reset view
            About: Application info, license
        """
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Settings menu
        settings_menu = menubar.addMenu("Settings")

        # Color submenu
        line_color_action = QAction("Line Color...", self)
        line_color_action.triggered.connect(lambda: self.pick_color("line"))
        settings_menu.addAction(line_color_action)

        scatter_color_action = QAction("Scatter Color...", self)
        scatter_color_action.triggered.connect(lambda: self.pick_color("scatter"))
        settings_menu.addAction(scatter_color_action)

        settings_menu.addSeparator()
        reset_colors_action = QAction("Reset Colors", self)
        reset_colors_action.triggered.connect(self.reset_colors)
        settings_menu.addAction(reset_colors_action)

        settings_menu.addSeparator()

        # Draw mode toggles
        self.draw_line_action = QAction("Draw Line", self, checkable=True)
        self.draw_line_action.setChecked(self.draw_line)
        self.draw_line_action.triggered.connect(self.toggle_draw_line)
        settings_menu.addAction(self.draw_line_action)

        self.draw_scatter_action = QAction("Draw Scatter", self, checkable=True)
        self.draw_scatter_action.setChecked(self.draw_scatter)
        self.draw_scatter_action.triggered.connect(self.toggle_draw_scatter)
        settings_menu.addAction(self.draw_scatter_action)

        settings_menu.addSeparator()

        # Grid toggle
        self.show_grid_action = QAction("Show Grid", self, checkable=True)
        self.show_grid_action.setChecked(self.show_grid)
        self.show_grid_action.triggered.connect(self.toggle_grid)
        settings_menu.addAction(self.show_grid_action)

        # Axis toggle
        self.show_axis_action = QAction("Show Axis", self, checkable=True)
        self.show_axis_action.setChecked(self.show_axis)
        self.show_axis_action.triggered.connect(self.toggle_axis)
        settings_menu.addAction(self.show_axis_action)

        settings_menu.addSeparator()

        # Dark mode toggle
        self.dark_mode_action = QAction("Dark Mode", self, checkable=True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        settings_menu.addAction(self.dark_mode_action)

        settings_menu.addSeparator()

        # Stats display toggle
        self.show_stats_action = QAction("Show FPS/Memory", self, checkable=True)
        self.show_stats_action.setChecked(self.show_stats)
        self.show_stats_action.triggered.connect(self.toggle_stats)
        settings_menu.addAction(self.show_stats_action)

        # View menu
        view_menu = menubar.addMenu("View")
        self.toggle_panel_action = QAction("Show Control Panel", self, checkable=True)
        self.toggle_panel_action.setChecked(True)
        self.toggle_panel_action.setShortcut("Ctrl+P")
        self.toggle_panel_action.triggered.connect(self.toggle_left_panel)
        view_menu.addAction(self.toggle_panel_action)

        # Plot menu
        plot_menu = menubar.addMenu("Plot")
        create_action = QAction("Create Plot", self)
        create_action.setShortcut("Ctrl+R")
        create_action.triggered.connect(self.create_plot)
        plot_menu.addAction(create_action)

        plot_menu.addSeparator()
        plot_settings_action = QAction("Plot Settings...", self)
        plot_settings_action.triggered.connect(self.show_plot_settings)
        plot_menu.addAction(plot_settings_action)

        plot_menu.addSeparator()
        reset_view_action = QAction("Reset View", self)
        reset_view_action.triggered.connect(self.reset_view)
        plot_menu.addAction(reset_view_action)

        # About menu
        about_menu = menubar.addMenu("About")
        about_action = QAction("About Attractor Explorer", self)
        about_action.triggered.connect(self.show_about)
        about_menu.addAction(about_action)

        license_action = QAction("License", self)
        license_action.triggered.connect(self.show_license)
        about_menu.addAction(license_action)

    def on_attractor_changed(self, attractor_name):
        """Handle attractor selection change.

        Updates parameters and initial conditions to match the selected attractor.
        If data exists, automatically regenerates the plot.

        Args:
            attractor_name: Name of the selected attractor
        """
        should_replot = (attractor_name != self.current_attractor and self.data is not None)
        self.current_attractor = attractor_name
        self.rebuild_params()
        if should_replot:
            self.create_plot()

    def _apply_color_theme(self):
        """Apply dark mode or light mode colors to the plot."""
        if self.dark_mode:
            bg_color, text_color = '#2b2b2b', 'white'
        else:
            bg_color, text_color = 'white', 'black'

        self.fig.patch.set_facecolor(bg_color)
        self.ax.set_facecolor(bg_color)
        self.ax.xaxis.pane.set_facecolor(bg_color)
        self.ax.yaxis.pane.set_facecolor(bg_color)
        self.ax.zaxis.pane.set_facecolor(bg_color)
        self.ax.tick_params(colors=text_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.zaxis.label.set_color(text_color)

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

    def _redraw_plot(self):
        """Redraw plot using cached data without recomputing."""
        if self.data is None:
            return

        # Clear stats and equations text before clearing axis to prevent memory leak
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

        # Apply all visual settings
        self._apply_grid_settings()
        self._apply_axis_settings()
        self._apply_color_theme()
        self._apply_tick_settings()

        # Update stats if enabled
        if self.show_stats:
            self.update_stats()

        # Update equations overlay
        self.update_equations()

        self.canvas.draw()

    def rebuild_params(self):
        """Rebuild parameter fields for the currently selected attractor.

        Dynamically creates input fields based on the attractor's parameter
        definition in the ATTRACTORS dictionary. Applies tooltips to explain
        the physical meaning of each parameter.
        """
        # Clear existing params
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        self.param_fields.clear()

        # Add new params
        attractor_name = self.attractor_combo.currentText()
        attractor_data = ATTRACTORS[attractor_name]
        params = attractor_data["params"]
        tooltips = attractor_data.get("tooltips", {})

        for pname, value in params.items():
            field = QLineEdit(str(value))
            if pname in tooltips:
                field.setToolTip(tooltips[pname])
            self.param_fields[pname] = field
            self.params_layout.addRow(f"{pname}:", field)

        # Update initial conditions
        init = attractor_data["init"]
        self.x0_field.setText(str(init[0]))
        self.y0_field.setText(str(init[1]))
        self.z0_field.setText(str(init[2]))

    def reset_to_defaults(self):
        """Reset parameters and initial conditions to default values."""
        self.rebuild_params()
        self.statusBar().showMessage("Parameters and initial conditions reset to defaults")

    def pick_color(self, color_type):
        """Open color picker dialog for line or scatter color.

        Args:
            color_type: Either "line" or "scatter"
        """
        initial = QtGui.QColor(self.line_color if color_type == "line" else self.scatter_color)
        color = QColorDialog.getColor(initial, self, f"Choose {color_type} color")
        if color.isValid():
            hex_color = color.name()
            if color_type == "line":
                self.line_color = hex_color
            else:
                self.scatter_color = hex_color
            self.statusBar().showMessage(f"{color_type.capitalize()} color changed to {hex_color}")

    def reset_colors(self):
        """Reset line and scatter colors to default values."""
        self.line_color = "#1f77b4"
        self.scatter_color = "#d62728"
        self.statusBar().showMessage("Colors reset to defaults")

    def toggle_draw_line(self):
        """Toggle line rendering mode.

        Uses cached data redraw for instant response (no re-integration).
        """
        self.draw_line = self.draw_line_action.isChecked()
        self.statusBar().showMessage(f"Draw line: {'ON' if self.draw_line else 'OFF'}")
        if self.data is not None:
            self._redraw_plot()

    def toggle_draw_scatter(self):
        """Toggle scatter rendering mode.

        Uses cached data redraw for instant response (no re-integration).
        """
        self.draw_scatter = self.draw_scatter_action.isChecked()
        self.statusBar().showMessage(f"Draw scatter: {'ON' if self.draw_scatter else 'OFF'}")
        if self.data is not None:
            self._redraw_plot()

    def toggle_grid(self):
        """Toggle grid visibility and pane fill."""
        self.show_grid = self.show_grid_action.isChecked()
        self._apply_grid_settings()
        self.canvas.draw()
        self.statusBar().showMessage(f"Grid: {'ON' if self.show_grid else 'OFF'}")

    def toggle_axis(self):
        """Toggle axis labels and ticks visibility."""
        self.show_axis = self.show_axis_action.isChecked()
        self._apply_axis_settings()
        self.canvas.draw()
        self.statusBar().showMessage(f"Axis: {'ON' if self.show_axis else 'OFF'}")

    def toggle_dark_mode(self):
        """Toggle between dark and light theme."""
        self.dark_mode = self.dark_mode_action.isChecked()
        self._apply_color_theme()
        self.canvas.draw()
        self.statusBar().showMessage(f"Dark mode: {'ON' if self.dark_mode else 'OFF'}")

    def toggle_stats(self):
        """Toggle FPS and memory usage display in lower-left corner."""
        self.show_stats = self.show_stats_action.isChecked()
        if not self.show_stats and self.stats_text:
            self.stats_text.remove()
            self.stats_text = None
            self.canvas.draw()
        elif self.show_stats:
            self.update_stats()
        self.statusBar().showMessage(f"Stats display: {'ON' if self.show_stats else 'OFF'}")

    def update_stats(self):
        """Update or create the FPS and memory usage overlay.

        Displays in lower-left corner with theme-appropriate colors.
        FPS is calculated from time between updates.
        """
        # Calculate FPS
        current_time = time.time()
        if self.last_plot_time > 0:
            fps = 1.0 / (current_time - self.last_plot_time) if (current_time - self.last_plot_time) > 0 else 0
        else:
            fps = 0
        self.last_plot_time = current_time

        # Get memory usage
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        # Update or create stats text
        stats_str = f"FPS: {fps:.1f}\nMem: {memory_mb:.1f} MB"

        if self.stats_text:
            self.stats_text.set_text(stats_str)
        else:
            text_color = 'white' if self.dark_mode else 'black'
            bg_color = 'black' if self.dark_mode else 'white'
            self.stats_text = self.fig.text(0.02, 0.02, stats_str,
                                           fontsize=9, family='Courier New',
                                           color=text_color,
                                           bbox=dict(boxstyle='round', facecolor=bg_color,
                                                    alpha=0.7, edgecolor=text_color))

    def update_equations(self):
        """Display equations overlay on the plot."""
        if not self.current_attractor:
            return

        # Get equations for current attractor
        attractor_data = ATTRACTORS.get(self.current_attractor, {})
        equations = attractor_data.get("equations", [])
        if not equations:
            return

        # Format equations text
        equations_str = "\n".join(equations)

        # Determine text color based on theme
        text_color = 'white' if self.dark_mode else 'black'
        bg_color = 'black' if self.dark_mode else 'white'

        # Create equations text in upper left corner
        self.equations_text = self.fig.text(0.02, 0.98, equations_str,
                                           fontsize=9, family='Courier New',
                                           color=text_color,
                                           verticalalignment='top',
                                           horizontalalignment='left',
                                           bbox=dict(boxstyle='round', facecolor=bg_color,
                                                    alpha=0.7, edgecolor=text_color))

    def show_attractor_info(self):
        """Display detailed information about the current attractor.

        Shows a modal dialog with:
        - Historical background
        - Mathematical equations
        - Physical interpretation
        """
        attractor_name = self.attractor_combo.currentText()
        attractor_data = ATTRACTORS.get(attractor_name, {})
        description = attractor_data.get("description", "No description available.")
        equations = attractor_data.get("equations", [])

        info_text = f"<h2>{attractor_name} Attractor</h2>"
        info_text += f"<p>{description}</p>"
        info_text += "<h3>Equations:</h3>"
        info_text += "<p style='font-family: \"Courier New\", Monaco, monospace;'>"
        info_text += "<br>".join(equations)
        info_text += "</p>"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"{attractor_name} Attractor Information")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(info_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def reset_view(self):
        """Reset 3D view to default elevation and azimuth angles."""
        self.ax.view_init(elev=20, azim=-60)
        self.canvas.draw()
        self.statusBar().showMessage("View reset")

    def toggle_left_panel(self):
        """Show or hide the left control panel (Ctrl+P)."""
        visible = self.toggle_panel_action.isChecked()
        self.left_panel.setVisible(visible)
        self.statusBar().showMessage(f"Control panel: {'visible' if visible else 'hidden'}")

    def toggle_animation_mode(self):
        """Toggle between animation mode and regular plotting mode."""
        self.animation_mode = self.animation_checkbox.isChecked()

        # Show/hide appropriate UI elements
        self.animation_group.setVisible(self.animation_mode)
        self.buttons_widget.setVisible(not self.animation_mode)

        # Stop animation if switching away from animation mode
        if not self.animation_mode and self.animation_running:
            self.pause_animation()

        self.statusBar().showMessage(f"Animation mode: {'ON' if self.animation_mode else 'OFF'}")

    def update_animation_speed(self, value):
        """Update animation speed from slider."""
        self.animation_speed = value
        self.speed_label.setText(str(value))

        # Update timer if running
        if self.animation_running and self.animation_timer:
            self.animation_timer.setInterval(1000 // self.animation_speed)

    def on_animation_steps_changed(self, text):
        """Handle changes to the animation steps field.

        Synchronizes with Plot Settings and updates progress display.
        Only processes valid integer inputs.
        """
        try:
            if text:  # Only process non-empty text
                steps = int(text)
                if steps > 0:
                    self.steps = steps
                    # Update progress label format
                    self.progress_label.setText(f"Progress: {self.animation_step:,} / {self.steps:,}")
        except ValueError:
            pass  # Ignore invalid input during typing

    def update_steps_per_frame(self, value):
        """Update steps per frame from slider."""
        self.steps_per_frame = value
        self.steps_per_frame_label.setText(str(value))

    def toggle_auto_rotate(self):
        """Toggle auto-rotation during animation."""
        self.animation_auto_rotate = self.auto_rotate_checkbox.isChecked()

    def toggle_fade(self):
        """Toggle point fading effect."""
        self.animation_fade = self.fade_checkbox.isChecked()

    def update_trail_length(self, value):
        """Update trail length from slider."""
        self.animation_trail_length = value
        self.trail_length_label.setText(str(value))

    def toggle_fixed_scale(self):
        """Toggle fixed axis scaling during animation."""
        self.animation_fixed_scale = self.fixed_scale_checkbox.isChecked()

    def play_animation(self):
        """Start or resume the animation."""
        if not self.animation_mode:
            return

        # Get parameters
        try:
            attractor_name = self.attractor_combo.currentText()
            self.current_attractor = attractor_name
            deriv = ATTRACTORS[attractor_name]["deriv"]

            params = {}
            for pname, field in self.param_fields.items():
                params[pname] = float(field.text())

            initial = np.array([
                float(self.x0_field.text()),
                float(self.y0_field.text()),
                float(self.z0_field.text())
            ])

            # Initialize animation if starting fresh
            if self.animation_state is None:
                self.animation_step = 0
                self.animation_state = initial.copy()
                self.animation_data = [initial.copy()]
                self.animation_deriv = deriv
                self.animation_params = params

                # Pre-compute axis limits if fixed scaling is enabled
                if self.animation_fixed_scale:
                    # Run a quick integration to determine typical bounds
                    from attractors import rk4_integrate
                    sample_data = rk4_integrate(deriv, initial, params, self.dt, min(2000, self.steps))
                    x_min, x_max = sample_data[:, 0].min(), sample_data[:, 0].max()
                    y_min, y_max = sample_data[:, 1].min(), sample_data[:, 1].max()
                    z_min, z_max = sample_data[:, 2].min(), sample_data[:, 2].max()

                    # Add 10% padding
                    x_padding = (x_max - x_min) * 0.1
                    y_padding = (y_max - y_min) * 0.1
                    z_padding = (z_max - z_min) * 0.1

                    self.animation_axis_limits = {
                        'x': (x_min - x_padding, x_max + x_padding),
                        'y': (y_min - y_padding, y_max + y_padding),
                        'z': (z_min - z_padding, z_max + z_padding)
                    }
                else:
                    self.animation_axis_limits = None

                # Clear equations text before clearing axis
                if self.equations_text:
                    self.equations_text.remove()
                    self.equations_text = None

                # Clear plot
                self.ax.clear()
                self.ax.set_xlabel("x")
                self.ax.set_ylabel("y")
                self.ax.set_zlabel("z")

                # Apply visual settings
                self._apply_grid_settings()
                self._apply_axis_settings()
                self._apply_color_theme()
                self._apply_tick_settings()

                # Update equations overlay
                self.update_equations()

                # Initialize scatter plot
                self.animation_scatter = None
                self.animation_azim = -60

            # Start timer
            if not self.animation_timer:
                self.animation_timer = QtCore.QTimer()
                self.animation_timer.timeout.connect(self.animate_step)

            self.animation_timer.start(1000 // self.animation_speed)
            self.animation_running = True

            # Update button states
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)

            # Disable steps field while running
            self.animation_steps_field.setEnabled(False)

            self.statusBar().showMessage("Animation started")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start animation:\n{str(e)}")
            self.statusBar().showMessage(f"Error: {str(e)}")

    def pause_animation(self):
        """Pause the animation."""
        if self.animation_timer:
            self.animation_timer.stop()

        self.animation_running = False

        # Update button states
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

        # Enable steps field when paused
        self.animation_steps_field.setEnabled(True)

        self.statusBar().showMessage("Animation paused")

    def reset_animation(self):
        """Reset animation to the beginning."""
        # Stop if running
        if self.animation_running:
            self.pause_animation()

        # Clear animation state
        self.animation_step = 0
        self.animation_state = None
        self.animation_data = None
        self.animation_scatter = None
        self.animation_azim = -60
        self.animation_axis_limits = None

        # Clear equations text before clearing axis
        if self.equations_text:
            self.equations_text.remove()
            self.equations_text = None

        # Clear plot
        self.ax.clear()
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")

        # Apply visual settings
        self._apply_grid_settings()
        self._apply_axis_settings()
        self._apply_color_theme()
        self._apply_tick_settings()

        # Update equations overlay
        self.update_equations()

        self.canvas.draw()

        # Update progress and ensure steps field is enabled
        self.progress_label.setText(f"Progress: 0 / {self.steps:,}")
        self.animation_steps_field.setEnabled(True)

        self.statusBar().showMessage("Animation reset")

    def animate_step(self):
        """Perform one animation step.

        Computes steps_per_frame integration steps and updates the plot.
        Implements memory optimization by limiting trail length to prevent
        unbounded memory growth during long animations.
        """
        if self.animation_step >= self.steps:
            # Animation complete
            self.pause_animation()
            self.statusBar().showMessage("Animation complete")
            return

        # Compute multiple steps per frame
        for _ in range(self.steps_per_frame):
            if self.animation_step >= self.steps:
                break

            # RK4 integration step
            state = self.animation_state
            dt = self.dt
            k1 = self.animation_deriv(state, self.animation_params)
            k2 = self.animation_deriv(state + 0.5 * dt * k1, self.animation_params)
            k3 = self.animation_deriv(state + 0.5 * dt * k2, self.animation_params)
            k4 = self.animation_deriv(state + dt * k3, self.animation_params)
            new_state = state + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)

            self.animation_state = new_state
            self.animation_data.append(new_state.copy())
            self.animation_step += 1

        # Limit memory by keeping only last N points
        # This frees memory used by points that have faded to zero
        if len(self.animation_data) > self.animation_trail_length:
            self.animation_data = self.animation_data[-self.animation_trail_length:]

        # Update plot
        data_array = np.array(self.animation_data)
        x, y, z = data_array[:, 0], data_array[:, 1], data_array[:, 2]

        # Clear and redraw scatter (scatter artists can't be updated directly)
        if self.animation_scatter:
            # Store the collection and remove it from axes
            try:
                self.animation_scatter.remove()
            except NotImplementedError:
                # Fallback: clear axes artists manually
                for artist in self.ax.collections[:]:
                    artist.remove()

        # Determine alpha values based on fade setting
        if self.animation_fade and len(data_array) > 100:
            # Create fade effect - newer points are more opaque
            alphas = np.linspace(0.1, 0.8, len(data_array))
        else:
            alphas = 0.6

        # Draw scatter points
        self.animation_scatter = self.ax.scatter(x, y, z,
                                                c=self.scatter_color,
                                                s=1,
                                                alpha=alphas)

        # Apply fixed axis limits if enabled
        if self.animation_fixed_scale and self.animation_axis_limits:
            self.ax.set_xlim(self.animation_axis_limits['x'])
            self.ax.set_ylim(self.animation_axis_limits['y'])
            self.ax.set_zlim(self.animation_axis_limits['z'])

        # Auto-rotate if enabled
        if self.animation_auto_rotate:
            self.animation_azim += 0.5
            self.ax.view_init(elev=20, azim=self.animation_azim)

        # Update progress label
        self.progress_label.setText(f"Progress: {self.animation_step:,} / {self.steps:,}")

        # Redraw
        self.canvas.draw()

    def show_plot_settings(self):
        """Display dialog for adjusting integration parameters.

        Settings:
            steps: Number of integration steps
            dt: Time step size (smaller = more accurate)
            stride: Plot every Nth point (higher = faster)
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Plot Settings")
        dialog.setModal(True)

        layout = QFormLayout(dialog)

        steps_field = QLineEdit(str(self.steps))
        steps_field.setToolTip("Total number of integration steps to compute")
        layout.addRow("Steps:", steps_field)

        dt_field = QLineEdit(str(self.dt))
        dt_field.setToolTip("Time step size for numerical integration (smaller = more accurate)")
        layout.addRow("dt:", dt_field)

        stride_field = QLineEdit(str(self.stride))
        stride_field.setToolTip("Plot every Nth point (higher = faster but less detailed)")
        layout.addRow("Stride:", stride_field)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addRow(btn_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.steps = int(steps_field.text())
                self.dt = float(dt_field.text())
                self.stride = int(stride_field.text())

                # Sync animation steps field
                self.animation_steps_field.setText(str(self.steps))
                self.progress_label.setText(f"Progress: {self.animation_step:,} / {self.steps:,}")

                self.statusBar().showMessage(f"Plot settings updated: steps={self.steps}, dt={self.dt}, stride={self.stride}")
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", f"Please enter valid numbers: {e}")
                self.statusBar().showMessage("Plot settings update failed")

    def show_about(self):
        """Display the About dialog with author information."""
        about_text = """<h2>Attractor Explorer</h2>
        <p>Interactive visualization of classic chaotic attractors</p>
        <p><b>Author:</b> Daniel Lowell</p>
        <p><b>Email:</b> <a href="mailto:redratio1@gmail.com">redratio1@gmail.com</a></p>
        <p>Version 1.0</p>"""

        QMessageBox.about(self, "About Attractor Explorer", about_text)

    def show_license(self):
        """Display the MIT License dialog."""
        license_text = """MIT License

Copyright (c) 2025 Daniel Lowell

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

        msg = QMessageBox(self)
        msg.setWindowTitle("MIT License")
        msg.setText(license_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()

    def create_plot(self):
        """Create or regenerate the attractor plot.

        Performs RK4 integration with current parameters and displays the result.
        Data is cached in self.data for efficient redrawing when only visual
        settings change.

        Performance: ~200ms for 20,000 steps on typical hardware.
        """
        try:
            # Get parameters
            attractor_name = self.attractor_combo.currentText()
            deriv = ATTRACTORS[attractor_name]["deriv"]

            params = {}
            for pname, field in self.param_fields.items():
                params[pname] = float(field.text())

            initial = np.array([
                float(self.x0_field.text()),
                float(self.y0_field.text()),
                float(self.z0_field.text())
            ])

            # Use instance variables for plot settings
            steps = self.steps
            dt = self.dt
            stride = self.stride

            # Integrate
            data = rk4_integrate(deriv, initial, params, dt, steps)
            self.data = data[::stride]
            self.current_attractor = attractor_name

            # Use efficient redraw method
            self._redraw_plot()
            self.statusBar().showMessage(f"{attractor_name} plot created with {len(self.data)} points")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create plot:\n{str(e)}")
            self.statusBar().showMessage(f"Error: {str(e)}")


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    window = AttractorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
