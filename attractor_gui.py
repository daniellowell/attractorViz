"""Interactive GUI for exploring classic chaotic attractors in 3D."""

import logging
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, cast

import numpy as np
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Line3D, Path3DCollection


def lorenz(state, p):
    """Compute the Lorenz system derivatives for a state vector."""
    x, y, z = state
    sigma = p["sigma"]
    rho = p["rho"]
    beta = p["beta"]
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return np.array([dx, dy, dz], dtype=float)


def rossler(state, p):
    """Compute the Rossler system derivatives for a state vector."""
    x, y, z = state
    a = p["a"]
    b = p["b"]
    c = p["c"]
    dx = -y - z
    dy = x + a * y
    dz = b + z * (x - c)
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
    a = p["a"]
    b = p["b"]
    c = p["c"]
    d = p["d"]
    e = p["e"]
    f = p["f"]
    dx = (z - b) * x - d * y
    dy = d * x + (z - b) * y
    dz = c + a * z - (z ** 3) / 3 - (x ** 2 + y ** 2) * (1 + e * z) + f * z * (x ** 3)
    return np.array([dx, dy, dz], dtype=float)


ATTRACTORS = {
    "Lorenz": {
        "deriv": lorenz,
        "params": {"sigma": 10.0, "rho": 28.0, "beta": 8.0 / 3.0},
    },
    "Rossler": {
        "deriv": rossler,
        "params": {"a": 0.2, "b": 0.2, "c": 5.7},
    },
    "Thomas": {
        "deriv": thomas,
        "params": {"b": 0.208186},
    },
    "Aizawa": {
        "deriv": aizawa,
        "params": {"a": 0.95, "b": 0.7, "c": 0.6, "d": 3.5, "e": 0.25, "f": 0.1},
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


class AttractorApp:
    """Tkinter application hosting attractor controls and a Matplotlib 3D plot."""

    def __init__(self, root):
        """Initialize the app, wire up controls, and create the plot canvas."""
        self.root = root
        self.root.title("Attractor Explorer")
        self.animating = False
        self.anim_after_id = None

        self.logger = self._init_logging()
        self.status_var = tk.StringVar(value="Ready")

        self.data = None
        self.line: Optional[Line3D] = None
        self.scatter: Optional[Path3DCollection] = None
        self.anim_idx = 0

        self._build_ui()
        self._set_default_params()
        self._create_plot()

    def _build_ui(self):
        """Create the left-hand controls and the right-hand plot area."""
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        controls = ttk.Frame(self.root, padding=10)
        controls.grid(row=0, column=0, sticky="ns")

        plot_frame = ttk.Frame(self.root, padding=5)
        plot_frame.grid(row=0, column=1, sticky="nsew")
        plot_frame.rowconfigure(0, weight=1)
        plot_frame.columnconfigure(0, weight=1)

        self.attractor_var = tk.StringVar(value="Lorenz")
        ttk.Label(controls, text="Attractor").grid(row=0, column=0, sticky="w")
        self.attractor_combo = ttk.Combobox(
            controls,
            textvariable=self.attractor_var,
            values=list(ATTRACTORS.keys()),
            state="readonly",
            width=18,
        )
        self.attractor_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self.attractor_combo.bind("<<ComboboxSelected>>", self._on_attractor_change)

        self.params_frame = ttk.LabelFrame(controls, text="Parameters", padding=8)
        self.params_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.param_vars = {}
        self.param_entries = {}

        init_frame = ttk.LabelFrame(controls, text="Initial Conditions", padding=8)
        init_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        self.x0_var = tk.StringVar(value="0.1")
        self.y0_var = tk.StringVar(value="0.0")
        self.z0_var = tk.StringVar(value="0.0")
        self._add_labeled_entry(init_frame, "x0", self.x0_var, 0)
        self._add_labeled_entry(init_frame, "y0", self.y0_var, 1)
        self._add_labeled_entry(init_frame, "z0", self.z0_var, 2)

        self.random_init_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(init_frame, text="Use random", variable=self.random_init_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        self.seed_var = tk.StringVar(value="123")
        self.rand_range_var = tk.StringVar(value="1.0")
        self._add_labeled_entry(init_frame, "seed", self.seed_var, 4)
        self._add_labeled_entry(init_frame, "range", self.rand_range_var, 5)

        settings = ttk.LabelFrame(controls, text="Plot Settings", padding=8)
        settings.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.steps_var = tk.StringVar(value="20000")
        self.dt_var = tk.StringVar(value="0.01")
        self.burn_var = tk.StringVar(value="1000")
        self.stride_var = tk.StringVar(value="2")
        self.point_size_var = tk.StringVar(value="0.5")

        self._add_labeled_entry(settings, "steps", self.steps_var, 0)
        self._add_labeled_entry(settings, "dt", self.dt_var, 1)
        self._add_labeled_entry(settings, "burn-in", self.burn_var, 2)
        self._add_labeled_entry(settings, "stride", self.stride_var, 3)
        self._add_labeled_entry(settings, "point size", self.point_size_var, 4)

        ttk.Label(settings, text="mode").grid(row=5, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="line")
        self.mode_combo = ttk.Combobox(
            settings,
            textvariable=self.mode_var,
            values=["line", "scatter", "line+scatter"],
            state="readonly",
            width=12,
        )
        self.mode_combo.grid(row=5, column=1, sticky="ew", pady=(2, 0))

        anim = ttk.LabelFrame(controls, text="Animation", padding=8)
        anim.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        self.anim_step_var = tk.StringVar(value="100")
        self.anim_delay_var = tk.StringVar(value="30")
        self._add_labeled_entry(anim, "step", self.anim_step_var, 0)
        self._add_labeled_entry(anim, "delay ms", self.anim_delay_var, 1)

        self.play_button = ttk.Button(anim, text="Play", command=self._toggle_play)
        self.play_button.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        controls.columnconfigure(0, weight=1)

        action_frame = ttk.Frame(controls)
        action_frame.grid(row=6, column=0, sticky="ew")
        action_frame.columnconfigure(0, weight=1)
        action_frame.columnconfigure(1, weight=1)

        ttk.Button(action_frame, text="Create Plot", command=self._create_plot).grid(
            row=0, column=0, sticky="ew", padx=(0, 4)
        )
        ttk.Button(action_frame, text="Show Full", command=self._show_full).grid(
            row=0, column=1, sticky="ew", padx=(4, 0)
        )

        self.fig = Figure(figsize=(7, 7), dpi=100)
        self.ax = cast(Axes3D, self.fig.add_subplot(111, projection="3d"))
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Create toolbar with pack, then convert to grid
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.grid(row=1, column=0, sticky="ew")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        self._build_menu()

        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w")
        status.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))

    def _build_menu(self):
        """Populate the application menu."""
        menubar = tk.Menu(self.root)
        plot_menu = tk.Menu(menubar, tearoff=0)
        plot_menu.add_command(label="Create Plot", command=self._create_plot)
        plot_menu.add_command(label="Show Full", command=self._show_full)
        plot_menu.add_separator()
        plot_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="Plot", menu=plot_menu)
        self.root.config(menu=menubar)

    def _add_labeled_entry(self, parent, label, var, row):
        """Add a labeled text entry to a layout grid."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w")
        entry = ttk.Entry(parent, textvariable=var, width=10)
        entry.grid(row=row, column=1, sticky="ew", pady=2)
        parent.columnconfigure(1, weight=1)
        return entry

    def _set_default_params(self):
        """Populate parameter entries for the default attractor."""
        self._rebuild_params()

    def _on_attractor_change(self, event=None):
        """Update parameter widgets when a new attractor is selected."""
        self._rebuild_params()

    def _rebuild_params(self):
        """Recreate the parameter input fields for the current attractor."""
        for child in self.params_frame.winfo_children():
            child.destroy()

        self.param_vars.clear()
        self.param_entries.clear()

        params = ATTRACTORS[self.attractor_var.get()]["params"]
        for idx, (name, value) in enumerate(params.items()):
            var = tk.StringVar(value=str(value))
            self.param_vars[name] = var
            entry = self._add_labeled_entry(self.params_frame, name, var, idx)
            self.param_entries[name] = entry

    def _parse_float(self, value, label):
        """Parse a float with a clear label for error reporting."""
        try:
            return float(value)
        except ValueError:
            raise ValueError(f"Invalid {label} value: {value}")

    def _parse_int(self, value, label):
        """Parse an integer with a clear label for error reporting."""
        try:
            return int(float(value))
        except ValueError:
            raise ValueError(f"Invalid {label} value: {value}")

    def _get_params(self):
        """Collect attractor parameters from the UI fields."""
        params = {}
        for name, var in self.param_vars.items():
            params[name] = self._parse_float(var.get(), name)
        return params

    def _get_initial_conditions(self):
        """Resolve initial conditions, optionally using a random seed."""
        if self.random_init_var.get():
            seed_text = self.seed_var.get().strip()
            try:
                seed = None if seed_text == "" else int(float(seed_text))
                rand_range = self._parse_float(self.rand_range_var.get(), "range")
                rng = np.random.default_rng(seed)
                vals = rng.uniform(-rand_range, rand_range, size=3)
                return vals
            except ValueError as exc:
                raise ValueError(f"Invalid random settings: {exc}") from exc

        x0 = self._parse_float(self.x0_var.get(), "x0")
        y0 = self._parse_float(self.y0_var.get(), "y0")
        z0 = self._parse_float(self.z0_var.get(), "z0")
        return np.array([x0, y0, z0], dtype=float)

    def _create_plot(self):
        """Generate and render a new attractor dataset."""
        try:
            steps = self._parse_int(self.steps_var.get(), "steps")
            dt = self._parse_float(self.dt_var.get(), "dt")
            burn = self._parse_int(self.burn_var.get(), "burn-in")
            stride = max(1, self._parse_int(self.stride_var.get(), "stride"))
            point_size = self._parse_float(self.point_size_var.get(), "point size")
            params = self._get_params()
            initial = self._get_initial_conditions()
        except ValueError as exc:
            self._report_error("Invalid input", exc)
            return
        except Exception as exc:
            self._report_error("Failed to read inputs", exc)
            return

        try:
            steps = max(10, steps)
            burn = max(0, burn)
            total_steps = steps + burn

            deriv = ATTRACTORS[self.attractor_var.get()]["deriv"]
            data = rk4_integrate(deriv, initial, params, dt, total_steps)
            if burn:
                data = data[burn:]
            data = data[::stride]

            self.data = data
            self.anim_idx = len(data)

            self._stop_animation()
            self._render_plot(point_size)
            self._set_status("Plot created.")
        except Exception as exc:
            self._report_error("Failed to create plot", exc)

    def _render_plot(self, point_size):
        """Render the current dataset using the selected plot mode."""
        mode = self.mode_var.get()
        self.ax.clear()
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")

        self.line = None
        self.scatter = None

        if self.data is None or len(self.data) == 0:
            self.canvas.draw_idle()
            return

        x, y, z = self.data[:, 0], self.data[:, 1], self.data[:, 2]

        if mode in ("line", "line+scatter"):
            self.line, = self.ax.plot(x, y, z, color="#1f77b4", linewidth=0.7, alpha=0.9)

        if mode in ("scatter", "line+scatter"):
            self.scatter = self.ax.scatter(x, y, z, s=point_size, c="#d62728", alpha=0.6)

        self._apply_aspect(x, y, z)
        self.canvas.draw_idle()

    def _apply_aspect(self, x, y, z):
        """Keep aspect ratio roughly consistent across axes when possible."""
        try:
            ranges = np.ptp(np.column_stack([x, y, z]), axis=0)
            ranges[ranges == 0] = 1.0
            self.ax.set_box_aspect(ranges)
        except Exception:
            pass

    def _show_full(self):
        """Show the full computed trajectory in the plot."""
        if self.data is None:
            return
        self.anim_idx = len(self.data)
        try:
            point_size = self._parse_float(self.point_size_var.get(), "point size")
        except ValueError:
            point_size = 0.5
        self._render_plot(point_size)

    def _toggle_play(self):
        """Toggle the animation state."""
        if self.data is None or len(self.data) == 0:
            self._set_status("No data to animate. Create a plot first.")
            return

        if self.animating:
            self._stop_animation()
        else:
            self._start_animation()

    def _start_animation(self):
        """Prepare plot artists and start the animation timer."""
        try:
            self.anim_step = max(1, self._parse_int(self.anim_step_var.get(), "step"))
            self.anim_delay = max(1, self._parse_int(self.anim_delay_var.get(), "delay ms"))
        except ValueError as exc:
            self._report_error("Invalid animation input", exc)
            return
        except Exception as exc:
            self._report_error("Failed to start animation", exc)
            return

        self.animating = True
        self.play_button.config(text="Pause")
        self.anim_idx = 1
        self._setup_animation_artists()
        self._animate_step()

    def _stop_animation(self):
        """Stop animation playback and clear any pending timers."""
        self.animating = False
        self.play_button.config(text="Play")
        if self.anim_after_id is not None:
            self.root.after_cancel(self.anim_after_id)
            self.anim_after_id = None

    def _setup_animation_artists(self):
        """Reset the plot artists for an incremental animation."""
        if self.data is None or len(self.data) == 0:
            return

        mode = self.mode_var.get()
        try:
            point_size = self._parse_float(self.point_size_var.get(), "point size")
        except ValueError:
            point_size = 0.5

        self.ax.clear()
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.ax.set_zlabel("z")

        x_full, y_full, z_full = self.data[:, 0], self.data[:, 1], self.data[:, 2]
        self._apply_aspect(x_full, y_full, z_full)

        self.line = None
        self.scatter = None

        if mode in ("line", "line+scatter"):
            self.line, = self.ax.plot([], [], [], color="#1f77b4", linewidth=0.7, alpha=0.9)
        if mode in ("scatter", "line+scatter"):
            self.scatter = self.ax.scatter([], [], [], s=point_size, c="#d62728", alpha=0.6)

        self.canvas.draw_idle()

    def _animate_step(self):
        """Advance the animation by one timer tick."""
        if not self.animating or self.data is None:
            return

        try:
            self.anim_idx = min(self.anim_idx + self.anim_step, len(self.data))
            segment = self.data[: self.anim_idx]
            x, y, z = segment[:, 0], segment[:, 1], segment[:, 2]

            if self.line is not None:
                self.line.set_data(x, y)
                self.line.set_3d_properties(z)
            if self.scatter is not None:
                self.scatter._offsets3d = (x, y, z)

            self.canvas.draw_idle()

            if self.anim_idx >= len(self.data):
                self._stop_animation()
                return

            self.anim_after_id = self.root.after(self.anim_delay, self._animate_step)
        except Exception as exc:
            self._report_error("Animation error", exc)
            self._stop_animation()

    def _set_status(self, message):
        """Update the status bar with a short message."""
        self.status_var.set(message)

    def _init_logging(self):
        """Initialize a file logger for error reporting."""
        logger = logging.getLogger("attractor_gui")
        if logger.handlers:
            return logger
        logger.setLevel(logging.INFO)
        try:
            log_dir = Path(__file__).resolve().parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / "attractor_gui.log"
            handler = logging.FileHandler(log_path, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.info("Logger initialized at %s", log_path)
        except Exception:
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger("attractor_gui")
            logger.exception("Failed to initialize file logging.")
        return logger

    def _report_error(self, title, exc):
        """Log the exception and surface a user-friendly dialog."""
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        self.logger.error("%s\n%s", title, details)
        self._set_status(f"Error: {title}")
        messagebox.showerror(title, f"{exc}\n\nSee logs/attractor_gui.log for details.")


def main():
    """Entry point for running the GUI as a script."""
    root = tk.Tk()
    app = AttractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
