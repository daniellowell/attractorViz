import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass
from collections import OrderedDict

import numpy as np
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


@dataclass
class AttractorSpec:
    name: str
    params: OrderedDict
    func: callable
    default_init: tuple


def lorenz(state, p):
    x, y, z = state
    sigma = p["sigma"]
    rho = p["rho"]
    beta = p["beta"]
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return np.array([dx, dy, dz], dtype=float)


def rossler(state, p):
    x, y, z = state
    a = p["a"]
    b = p["b"]
    c = p["c"]
    dx = -(y + z)
    dy = x + a * y
    dz = b + z * (x - c)
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


ATTRACTORS = OrderedDict(
    [
        (
            "Lorenz",
            AttractorSpec(
                name="Lorenz",
                params=OrderedDict([("sigma", 10.0), ("rho", 28.0), ("beta", 8.0 / 3.0)]),
                func=lorenz,
                default_init=(0.0, 1.0, 1.05),
            ),
        ),
        (
            "Rossler",
            AttractorSpec(
                name="Rossler",
                params=OrderedDict([("a", 0.2), ("b", 0.2), ("c", 5.7)]),
                func=rossler,
                default_init=(0.0, 1.0, 0.0),
            ),
        ),
        (
            "Thomas",
            AttractorSpec(
                name="Thomas",
                params=OrderedDict([("b", 0.208186)]),
                func=thomas,
                default_init=(0.1, 0.0, 0.0),
            ),
        ),
        (
            "Aizawa",
            AttractorSpec(
                name="Aizawa",
                params=OrderedDict(
                    [("a", 0.95), ("b", 0.7), ("c", 0.6), ("d", 3.5), ("e", 0.25), ("f", 0.1)]
                ),
                func=aizawa,
                default_init=(0.1, 0.0, 0.0),
            ),
        ),
    ]
)


def rk4_step(state, dt, deriv, params):
    k1 = deriv(state, params)
    k2 = deriv(state + 0.5 * dt * k1, params)
    k3 = deriv(state + 0.5 * dt * k2, params)
    k4 = deriv(state + dt * k3, params)
    return state + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate(deriv, initial, dt, steps, params):
    states = np.zeros((steps, 3), dtype=float)
    state = np.array(initial, dtype=float)
    for i in range(steps):
        states[i] = state
        state = rk4_step(state, dt, deriv, params)
    return states


class AttractorExplorer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chaotic Attractor Explorer")
        self.geometry("1200x720")
        self.minsize(1100, 650)

        self.param_vars = {}
        self.init_vars = {}
        self.data = None
        self.plot_data = None
        self.animating = False
        self.anim_index = 0
        self.anim_after_id = None

        self._build_menu()
        self._build_layout()
        self._build_controls()
        self._build_plot()
        self._load_attractor("Lorenz")

    def _build_menu(self):
        menu = tk.Menu(self)
        self.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menu.add_cascade(label="File", menu=file_menu)

        action_menu = tk.Menu(menu, tearoff=0)
        action_menu.add_command(label="Generate", command=self.generate)
        action_menu.add_separator()
        action_menu.add_command(label="Reset View", command=self.reset_view)
        menu.add_cascade(label="Action", menu=action_menu)

    def _build_layout(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.control_frame = ttk.Frame(self, padding=10)
        self.control_frame.grid(row=0, column=0, sticky="nsw")

        self.plot_frame = ttk.Frame(self, padding=8)
        self.plot_frame.grid(row=0, column=1, sticky="nsew")
        self.plot_frame.rowconfigure(0, weight=1)
        self.plot_frame.columnconfigure(0, weight=1)

    def _build_controls(self):
        attractor_box = ttk.LabelFrame(self.control_frame, text="Attractor")
        attractor_box.grid(row=0, column=0, sticky="ew")
        attractor_box.columnconfigure(1, weight=1)

        ttk.Label(attractor_box, text="Type").grid(row=0, column=0, sticky="w")
        self.attractor_var = tk.StringVar(value="Lorenz")
        self.attractor_select = ttk.Combobox(
            attractor_box, textvariable=self.attractor_var, values=list(ATTRACTORS.keys()), state="readonly", width=16
        )
        self.attractor_select.grid(row=0, column=1, sticky="ew")
        self.attractor_select.bind("<<ComboboxSelected>>", self._on_attractor_change)

        self.param_frame = ttk.LabelFrame(self.control_frame, text="Parameters")
        self.param_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.param_frame.columnconfigure(1, weight=1)

        init_frame = ttk.LabelFrame(self.control_frame, text="Initial Conditions")
        init_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        init_frame.columnconfigure(1, weight=1)

        for row, label in enumerate(["x0", "y0", "z0"]):
            ttk.Label(init_frame, text=label).grid(row=row, column=0, sticky="w")
            var = tk.StringVar(value="0.0")
            self.init_vars[label] = var
            ttk.Entry(init_frame, textvariable=var, width=12).grid(row=row, column=1, sticky="ew")

        self.randomize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(init_frame, text="Randomize init", variable=self.randomize_var).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

        ttk.Label(init_frame, text="Seed").grid(row=4, column=0, sticky="w")
        self.seed_var = tk.StringVar(value="0")
        ttk.Entry(init_frame, textvariable=self.seed_var, width=12).grid(row=4, column=1, sticky="ew")

        ttk.Label(init_frame, text="Init scale").grid(row=5, column=0, sticky="w")
        self.init_scale_var = tk.StringVar(value="1.0")
        ttk.Entry(init_frame, textvariable=self.init_scale_var, width=12).grid(row=5, column=1, sticky="ew")

        plot_frame = ttk.LabelFrame(self.control_frame, text="Plot Settings")
        plot_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        plot_frame.columnconfigure(1, weight=1)

        self.points_var = tk.StringVar(value="8000")
        self.dt_var = tk.StringVar(value="0.01")
        self.stride_var = tk.StringVar(value="1")
        self.point_size_var = tk.StringVar(value="0.6")

        ttk.Label(plot_frame, text="Total points").grid(row=0, column=0, sticky="w")
        ttk.Entry(plot_frame, textvariable=self.points_var, width=12).grid(row=0, column=1, sticky="ew")
        ttk.Label(plot_frame, text="dt").grid(row=1, column=0, sticky="w")
        ttk.Entry(plot_frame, textvariable=self.dt_var, width=12).grid(row=1, column=1, sticky="ew")
        ttk.Label(plot_frame, text="Plot stride").grid(row=2, column=0, sticky="w")
        ttk.Entry(plot_frame, textvariable=self.stride_var, width=12).grid(row=2, column=1, sticky="ew")
        ttk.Label(plot_frame, text="Point size").grid(row=3, column=0, sticky="w")
        ttk.Entry(plot_frame, textvariable=self.point_size_var, width=12).grid(row=3, column=1, sticky="ew")

        anim_frame = ttk.LabelFrame(self.control_frame, text="Animation")
        anim_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        anim_frame.columnconfigure(1, weight=1)

        self.speed_var = tk.StringVar(value="4")
        ttk.Label(anim_frame, text="Step speed").grid(row=0, column=0, sticky="w")
        ttk.Entry(anim_frame, textvariable=self.speed_var, width=12).grid(row=0, column=1, sticky="ew")

        button_frame = ttk.Frame(self.control_frame)
        button_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)

        self.generate_button = ttk.Button(button_frame, text="Generate", command=self.generate)
        self.generate_button.grid(row=0, column=0, sticky="ew")

        self.play_button = ttk.Button(button_frame, text="Play", command=self.toggle_play)
        self.play_button.grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self.reset_button = ttk.Button(button_frame, text="Reset View", command=self.reset_view)
        self.reset_button.grid(row=2, column=0, sticky="ew", pady=(6, 0))

    def _build_plot(self):
        self.fig = Figure(figsize=(7.5, 6.5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")
        self.ax.set_title("Lorenz attractor")

        self.line, = self.ax.plot(
            [], [], [], linestyle="-", linewidth=0.6, marker=".", markersize=0.6, color="#1f77b4", alpha=0.85
        )

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        toolbar.update()
        toolbar.grid(row=1, column=0, sticky="ew")

    def _on_attractor_change(self, event=None):
        self._load_attractor(self.attractor_var.get())

    def _load_attractor(self, name):
        spec = ATTRACTORS[name]
        for child in self.param_frame.winfo_children():
            child.destroy()
        self.param_vars = {}

        for row, (key, value) in enumerate(spec.params.items()):
            ttk.Label(self.param_frame, text=key).grid(row=row, column=0, sticky="w")
            var = tk.StringVar(value=str(value))
            self.param_vars[key] = var
            ttk.Entry(self.param_frame, textvariable=var, width=12).grid(row=row, column=1, sticky="ew")

        for var, value in zip(self.init_vars.values(), spec.default_init):
            var.set(str(value))

        self.ax.set_title(f"{spec.name} attractor")
        self.canvas.draw_idle()

    def _parse_float(self, var, label):
        value = var.get().strip()
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"{label} must be a number.") from exc

    def _parse_int(self, var, label):
        value = var.get().strip()
        try:
            return int(float(value))
        except ValueError as exc:
            raise ValueError(f"{label} must be an integer.") from exc

    def _get_params(self):
        params = {}
        for key, var in self.param_vars.items():
            params[key] = self._parse_float(var, key)
        return params

    def _get_initial_conditions(self):
        if self.randomize_var.get():
            seed_text = self.seed_var.get().strip()
            seed = int(seed_text) if seed_text else None
            scale = self._parse_float(self.init_scale_var, "Init scale")
            rng = np.random.default_rng(seed)
            init = rng.uniform(-scale, scale, size=3)
            for var, value in zip(self.init_vars.values(), init):
                var.set(f"{value:.6f}")
            return init

        x0 = self._parse_float(self.init_vars["x0"], "x0")
        y0 = self._parse_float(self.init_vars["y0"], "y0")
        z0 = self._parse_float(self.init_vars["z0"], "z0")
        return np.array([x0, y0, z0], dtype=float)

    def generate(self):
        try:
            steps = max(100, self._parse_int(self.points_var, "Total points"))
            dt = self._parse_float(self.dt_var, "dt")
            stride = max(1, self._parse_int(self.stride_var, "Plot stride"))
            point_size = max(0.1, self._parse_float(self.point_size_var, "Point size"))
        except ValueError as err:
            messagebox.showerror("Invalid input", str(err))
            return

        spec = ATTRACTORS[self.attractor_var.get()]
        try:
            params = self._get_params()
            init = self._get_initial_conditions()
        except ValueError as err:
            messagebox.showerror("Invalid input", str(err))
            return

        self.data = integrate(spec.func, init, dt, steps, params)
        self.plot_data = self.data[::stride]

        self.anim_index = 0
        self._update_line(point_size, 0)
        self._apply_equal_aspect(self.plot_data)
        self.canvas.draw_idle()

    def _apply_equal_aspect(self, data):
        if data is None or len(data) == 0:
            return
        mins = data.min(axis=0)
        maxs = data.max(axis=0)
        ranges = maxs - mins
        span = np.max(ranges)
        if span == 0:
            span = 1.0
        centers = (maxs + mins) / 2.0
        self.ax.set_xlim(centers[0] - span / 2, centers[0] + span / 2)
        self.ax.set_ylim(centers[1] - span / 2, centers[1] + span / 2)
        self.ax.set_zlim(centers[2] - span / 2, centers[2] + span / 2)

    def _update_line(self, point_size, upto_index=None):
        if self.plot_data is None:
            return
        if upto_index is None:
            upto_index = len(self.plot_data)
        subset = self.plot_data[:upto_index]
        self.line.set_data(subset[:, 0], subset[:, 1])
        self.line.set_3d_properties(subset[:, 2])
        self.line.set_markersize(point_size)

    def toggle_play(self):
        if self.animating:
            self.animating = False
            self.play_button.config(text="Play")
            if self.anim_after_id:
                self.after_cancel(self.anim_after_id)
                self.anim_after_id = None
            return

        if self.plot_data is None or len(self.plot_data) == 0:
            messagebox.showinfo("No data", "Generate an attractor before playing.")
            return

        self.animating = True
        self.play_button.config(text="Pause")
        self._schedule_animation()

    def _schedule_animation(self):
        self.anim_after_id = self.after(30, self._animate_step)

    def _animate_step(self):
        if not self.animating:
            return
        try:
            step = max(1, self._parse_int(self.speed_var, "Step speed"))
            point_size = max(0.1, self._parse_float(self.point_size_var, "Point size"))
        except ValueError:
            step = 1
            point_size = 0.6

        self.anim_index = min(self.anim_index + step, len(self.plot_data))
        self._update_line(point_size, self.anim_index)
        self.canvas.draw_idle()

        if self.anim_index >= len(self.plot_data):
            self.animating = False
            self.play_button.config(text="Play")
            return
        self._schedule_animation()

    def reset_view(self):
        self.ax.view_init(elev=20, azim=-60)
        self.canvas.draw_idle()


if __name__ == "__main__":
    app = AttractorExplorer()
    app.mainloop()
