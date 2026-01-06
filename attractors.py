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
    x, y, z = state
    dx = p["sigma"] * (y - x)
    dy = x * (p["rho"] - z) - y
    dz = x * y - p["beta"] * z
    return np.array([dx, dy, dz], dtype=float)


def rossler(state, p):
    x, y, z = state
    dx = -y - z
    dy = x + p["a"] * y
    dz = p["b"] + z * (x - p["c"])
    return np.array([dx, dy, dz], dtype=float)


def thomas(state, p):
    x, y, z = state
    b = p["b"]
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return np.array([dx, dy, dz], dtype=float)


def aizawa(state, p):
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

        self._build_ui()
        self._build_menus()

    def _build_ui(self):
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

        # Equations display
        self.equations_group = QGroupBox("Equations")
        self.equations_layout = QVBoxLayout()
        self.equations_label = QLabel()
        self.equations_label.setWordWrap(True)
        self.equations_label.setStyleSheet("font-family: monospace; padding: 5px;")
        self.equations_layout.addWidget(self.equations_label)
        self.equations_group.setLayout(self.equations_layout)
        controls_layout.addWidget(self.equations_group)

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

        # Buttons
        btn_layout = QHBoxLayout()
        self.create_btn = QPushButton("Create Plot")
        self.create_btn.clicked.connect(self.create_plot)
        self.create_btn.setToolTip("Generate and display the attractor with current settings")
        btn_layout.addWidget(self.create_btn)
        controls_layout.addLayout(btn_layout)

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

    def _build_menus(self):
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

    def on_attractor_changed(self, attractor_name):
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
        if self.ax.get_title():
            self.ax.title.set_color(text_color)

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

    def _redraw_plot(self):
        """Redraw plot using cached data without recomputing."""
        if self.data is None:
            return

        # Clear stats text before clearing axis to prevent memory leak
        if self.stats_text:
            self.stats_text.remove()
            self.stats_text = None

        self.ax.clear()
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")
        self.ax.set_title(f"{self.current_attractor} Attractor")

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

        # Update stats if enabled
        if self.show_stats:
            self.update_stats()

        self.canvas.draw()

    def rebuild_params(self):
        # Clear existing params
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        self.param_fields.clear()

        # Add new params
        attractor_name = self.attractor_combo.currentText()
        attractor_data = ATTRACTORS[attractor_name]
        params = attractor_data["params"]
        tooltips = attractor_data.get("tooltips", {})

        # Update equations display
        equations = attractor_data.get("equations", [])
        equations_text = "\n".join(equations)
        self.equations_label.setText(equations_text)

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

    def pick_color(self, color_type):
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
        self.line_color = "#1f77b4"
        self.scatter_color = "#d62728"
        self.statusBar().showMessage("Colors reset to defaults")

    def toggle_draw_line(self):
        self.draw_line = self.draw_line_action.isChecked()
        self.statusBar().showMessage(f"Draw line: {'ON' if self.draw_line else 'OFF'}")
        if self.data is not None:
            self._redraw_plot()

    def toggle_draw_scatter(self):
        self.draw_scatter = self.draw_scatter_action.isChecked()
        self.statusBar().showMessage(f"Draw scatter: {'ON' if self.draw_scatter else 'OFF'}")
        if self.data is not None:
            self._redraw_plot()

    def toggle_grid(self):
        self.show_grid = self.show_grid_action.isChecked()
        self._apply_grid_settings()
        self.canvas.draw()
        self.statusBar().showMessage(f"Grid: {'ON' if self.show_grid else 'OFF'}")

    def toggle_axis(self):
        self.show_axis = self.show_axis_action.isChecked()
        self._apply_axis_settings()
        self.canvas.draw()
        self.statusBar().showMessage(f"Axis: {'ON' if self.show_axis else 'OFF'}")

    def toggle_dark_mode(self):
        self.dark_mode = self.dark_mode_action.isChecked()
        self._apply_color_theme()
        self.canvas.draw()
        self.statusBar().showMessage(f"Dark mode: {'ON' if self.dark_mode else 'OFF'}")

    def toggle_stats(self):
        self.show_stats = self.show_stats_action.isChecked()
        if not self.show_stats and self.stats_text:
            self.stats_text.remove()
            self.stats_text = None
            self.canvas.draw()
        elif self.show_stats:
            self.update_stats()
        self.statusBar().showMessage(f"Stats display: {'ON' if self.show_stats else 'OFF'}")

    def update_stats(self):
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
                                           fontsize=9, family='monospace',
                                           color=text_color,
                                           bbox=dict(boxstyle='round', facecolor=bg_color,
                                                    alpha=0.7, edgecolor=text_color))

    def show_attractor_info(self):
        attractor_name = self.attractor_combo.currentText()
        attractor_data = ATTRACTORS.get(attractor_name, {})
        description = attractor_data.get("description", "No description available.")
        equations = attractor_data.get("equations", [])

        info_text = f"<h2>{attractor_name} Attractor</h2>"
        info_text += f"<p>{description}</p>"
        info_text += "<h3>Equations:</h3>"
        info_text += "<p style='font-family: monospace;'>"
        info_text += "<br>".join(equations)
        info_text += "</p>"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(f"{attractor_name} Attractor Information")
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(info_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.exec()

    def reset_view(self):
        self.ax.view_init(elev=20, azim=-60)
        self.canvas.draw()
        self.statusBar().showMessage("View reset")

    def toggle_left_panel(self):
        visible = self.toggle_panel_action.isChecked()
        self.left_panel.setVisible(visible)
        self.statusBar().showMessage(f"Control panel: {'visible' if visible else 'hidden'}")

    def show_plot_settings(self):
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
                self.statusBar().showMessage(f"Plot settings updated: steps={self.steps}, dt={self.dt}, stride={self.stride}")
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Input", f"Please enter valid numbers: {e}")
                self.statusBar().showMessage("Plot settings update failed")

    def create_plot(self):
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
    app = QApplication(sys.argv)
    window = AttractorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
