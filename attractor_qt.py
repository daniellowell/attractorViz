"""Interactive GUI for exploring classic chaotic attractors in 3D using Qt backend."""

import sys
import numpy as np
import matplotlib
matplotlib.use('QtAgg')  # Use Qt instead of Tk

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D

try:
    from PyQt6 import QtWidgets, QtCore
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                  QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QGroupBox, QFormLayout)
    QT_VERSION = 6
except ImportError:
    try:
        from PyQt5 import QtWidgets, QtCore
        from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                      QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QGroupBox, QFormLayout)
        QT_VERSION = 5
    except ImportError:
        print("ERROR: PyQt6 or PyQt5 is required. Install with:")
        print("  pip install PyQt6")
        print("  or")
        print("  pip install PyQt5")
        sys.exit(1)


def lorenz(state, p):
    """Compute the Lorenz system derivatives for a state vector."""
    x, y, z = state
    dx = p["sigma"] * (y - x)
    dy = x * (p["rho"] - z) - y
    dz = x * y - p["beta"] * z
    return np.array([dx, dy, dz], dtype=float)


def rossler(state, p):
    """Compute the Rossler system derivatives for a state vector."""
    x, y, z = state
    dx = -y - z
    dy = x + p["a"] * y
    dz = p["b"] + z * (x - p["c"])
    return np.array([dx, dy, dz], dtype=float)


def thomas(state, p):
    """Compute the Thomas system derivatives for a state vector."""
    x, y, z = state
    b = p["b"]
    dx = np.sin(y) - b * x
    dy = np.sin(z) - b * y
    dz = np.sin(x) - b * z
    return np.array([dx, dy, dz], dtype=float)


def aizawa(state, p):
    """Compute the Aizawa system derivatives for a state vector."""
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
    },
    "Rossler": {
        "deriv": rossler,
        "params": {"a": 0.2, "b": 0.2, "c": 5.7},
        "init": [0.0, 1.0, 0.0],
    },
    "Thomas": {
        "deriv": thomas,
        "params": {"b": 0.208186},
        "init": [0.1, 0.0, 0.0],
    },
    "Aizawa": {
        "deriv": aizawa,
        "params": {"a": 0.95, "b": 0.7, "c": 0.6, "d": 3.5, "e": 0.25, "f": 0.1},
        "init": [0.1, 0.0, 0.0],
    },
}


def rk4_integrate(deriv, initial, params, dt, steps):
    """Integrate a 3D system forward using fixed-step RK4."""
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
        self.setWindowTitle("Attractor Explorer (Qt)")
        self.setGeometry(100, 100, 1200, 700)

        self.data = None

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # Left panel - controls
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        controls_widget.setMaximumWidth(300)

        # Attractor selection
        attractor_group = QGroupBox("Attractor")
        attractor_layout = QFormLayout()
        self.attractor_combo = QComboBox()
        self.attractor_combo.addItems(ATTRACTORS.keys())
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
        init_layout.addRow("x0:", self.x0_field)
        init_layout.addRow("y0:", self.y0_field)
        init_layout.addRow("z0:", self.z0_field)
        init_group.setLayout(init_layout)
        controls_layout.addWidget(init_group)

        # Plot settings
        plot_group = QGroupBox("Plot Settings")
        plot_layout = QFormLayout()
        self.steps_field = QLineEdit("20000")
        self.dt_field = QLineEdit("0.01")
        self.stride_field = QLineEdit("2")
        plot_layout.addRow("Steps:", self.steps_field)
        plot_layout.addRow("dt:", self.dt_field)
        plot_layout.addRow("Stride:", self.stride_field)
        plot_group.setLayout(plot_layout)
        controls_layout.addWidget(plot_group)

        # Create button
        self.create_btn = QPushButton("Create Plot")
        self.create_btn.clicked.connect(self.create_plot)
        controls_layout.addWidget(self.create_btn)

        controls_layout.addStretch()

        # Right panel - plot
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)

        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)

        # Add to main layout
        main_layout.addWidget(controls_widget)
        main_layout.addWidget(plot_widget)

        # Initialize
        self.on_attractor_changed("Lorenz")

    def on_attractor_changed(self, name):
        """Update parameter fields when attractor changes."""
        # Clear existing params
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)
        self.param_fields.clear()

        # Add new params
        params = ATTRACTORS[name]["params"]
        for pname, value in params.items():
            field = QLineEdit(str(value))
            self.param_fields[pname] = field
            self.params_layout.addRow(f"{pname}:", field)

        # Update initial conditions
        init = ATTRACTORS[name]["init"]
        self.x0_field.setText(str(init[0]))
        self.y0_field.setText(str(init[1]))
        self.z0_field.setText(str(init[2]))

    def create_plot(self):
        """Generate and plot the attractor."""
        try:
            # Get parameters
            name = self.attractor_combo.currentText()
            deriv = ATTRACTORS[name]["deriv"]

            params = {}
            for pname, field in self.param_fields.items():
                params[pname] = float(field.text())

            initial = np.array([
                float(self.x0_field.text()),
                float(self.y0_field.text()),
                float(self.z0_field.text())
            ])

            steps = int(self.steps_field.text())
            dt = float(self.dt_field.text())
            stride = int(self.stride_field.text())

            # Integrate
            data = rk4_integrate(deriv, initial, params, dt, steps)
            self.data = data[::stride]

            # Plot
            self.ax.clear()
            self.ax.set_xlabel("x")
            self.ax.set_ylabel("y")
            self.ax.set_zlabel("z")
            self.ax.set_title(f"{name} Attractor")

            x, y, z = self.data[:, 0], self.data[:, 1], self.data[:, 2]
            self.ax.plot(x, y, z, linewidth=0.5, alpha=0.8)

            self.canvas.draw()

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    app = QApplication(sys.argv)
    window = AttractorWindow()
    window.show()
    sys.exit(app.exec() if QT_VERSION == 6 else app.exec_())


if __name__ == "__main__":
    main()
