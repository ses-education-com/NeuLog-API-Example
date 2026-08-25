"""NeuLog API controller Sample.

Features
--------
* Launches the NeuLog_API executable.
* Prompts for the localhost API server port.
* Provides every command present in the supplied NeuLog API demo.
* Repeatedly requests experiment samples until stopped.
* Uses only Python's standard library.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.error import HTTPError, URLError
from urllib.request import build_opener, ProxyHandler

VERSION = "V2.01"

# Requests always target the local NeuLog API, so bypass any system/VPN proxy
# configuration outright instead of relying on proxy bypass-list matching.
_no_proxy_opener = build_opener(ProxyHandler({}))


class NeuLogController(tk.Tk):
    TIMEOUT_SECONDS = 3.0
    DEFAULT_PORT = 22001
    DEFAULT_API_DIR = Path(r"C:\NeuLogAPI2")
    API_EXE_NAME = "NeuLogAPI.exe"
    CONFIG_FILENAME = "API_Sample_settings.txt"
    SENSOR_NAMES = (
        "Temperature", "Light", "Voltage", "Current", "PH", "Oxygen", "PhotoGate", "Pulse", "Force", "Sound",
        "Humidity", "Pressure", "Motion", "Magtnetic", "Conductivity", "GSR", "CO2", "Barometer", "Rotary",
        "Acceleration", "Spirometer", "SoilMoisture", "Turbidity", "UVB", "EKG", "Colorimeter", "DropCounter",
        "FlowRate", "ForcePlate", "BloodPressure", "Salinity", "UVA", "SurfaceTemp", "WideRangeTemp",
        "InfraredThermometer", "Respiration", "HandDynamometer", "Calcium", "Chloride", "Ammonium", "Nitrate",
        "Anemometer", "GPS", "Gyroscope", "DewPoint", "Charge",
    )
    RESET_SENSOR_NAMES = tuple(
        name for name in SENSOR_NAMES
        if name in {
            "PH", "Force", "CO2", "Rotary", "Spirometer", "DropCounter",
            "ForcePlate", "HandDynamometer", "Charge",
        }
    )
    POSITIVE_DIRECTION_SENSOR_NAMES = tuple(
        name for name in SENSOR_NAMES if name in {"Force", "ForcePlate"}
    )

    def __init__(self) -> None:
        super().__init__()
        self.withdraw()
        self.title(f"NeuLog API Controller Sample {VERSION}")
        self.geometry("1120x820")
        self.minsize(900, 650)

        self.api_process: subprocess.Popen[str] | None = None
        self.api_path: Path | None = None

        self.port_var = tk.StringVar(value=str(self.DEFAULT_PORT))
        self.host_mode_var = tk.StringVar(value=self._load_host_mode())
        self.host_mode_var.trace_add("write", lambda *_: self._on_host_mode_change())
        self.command_var = tk.StringVar(value="Command:")
        self.url_var = tk.StringVar(value="URL:")
        self.result_var = tk.StringVar(value="Ready")
        self.status_var = tk.StringVar(value="Starting...")
        self.close_on_exit_var = tk.BooleanVar(value=self._load_close_on_exit())
        self.close_on_exit_var.trace_add("write", lambda *_: self._save_close_on_exit(self.close_on_exit_var.get()))
        selected_sensors = self._load_selected_sensors()
        self.sensor_vars: dict[str, tk.BooleanVar] = {
            name: tk.BooleanVar(value=name in selected_sensors) for name in self.SENSOR_NAMES
        }
        self._last_checked_sensor: str | None = None
        for name, var in self.sensor_vars.items():
            var.trace_add("write", lambda *_, n=name: self._on_sensor_toggle(n))
        self.direction_var = tk.StringVar(value=self._load_direction())
        self.direction_var.trace_add("write", lambda *_: self._on_direction_change())
        self._sensor_checkbuttons: list[tk.Checkbutton] = []
        self._sensor_columns = 0

        self._configure_styles()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.after(50, self._startup_sequence)

    # ------------------------------------------------------------------
    # Startup and API process
    # ------------------------------------------------------------------
    def _startup_sequence(self) -> None:
        self.deiconify()
        self.status_var.set("Ready. Use 'Check if API runs' or one of the Launch buttons to get started.")

    def _config_file(self) -> Path:
        return Path(__file__).resolve().parent / self.CONFIG_FILENAME

    def _load_config(self) -> dict[str, str]:
        config_file = self._config_file()
        if not config_file.is_file():
            return {}
        config: dict[str, str] = {}
        for line in config_file.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep:
                config[key.strip()] = value.strip()
        return config

    def _save_config_value(self, key: str, value: str) -> None:
        config = self._load_config()
        config[key] = value
        text = "\n".join(f"{k}={v}" for k, v in config.items())
        try:
            self._config_file().write_text(text, encoding="utf-8")
        except OSError:
            pass

    def _load_saved_api_path(self) -> Path | None:
        saved = self._load_config().get("api_path")
        if not saved:
            return None
        path = Path(saved)
        return path if path.is_file() else None

    def _save_api_path(self, api_path: Path) -> None:
        self._save_config_value("api_path", str(api_path))

    def _load_close_on_exit(self) -> bool:
        return self._load_config().get("close_on_exit") == "1"

    def _save_close_on_exit(self, value: bool) -> None:
        self._save_config_value("close_on_exit", "1" if value else "0")

    def _load_host_mode(self) -> str:
        mode = self._load_config().get("host_mode", "127.0.0.1")
        return mode if mode in {"localhost", "127.0.0.1"} else "127.0.0.1"

    def _save_host_mode(self, value: str) -> None:
        self._save_config_value("host_mode", value)

    def _load_selected_sensors(self) -> set[str]:
        saved = self._load_config().get("selected_sensors", "")
        return {name for name in saved.split(",") if name}

    def _save_selected_sensors(self) -> None:
        selected = [name for name in self.SENSOR_NAMES if self.sensor_vars[name].get()]
        self._save_config_value("selected_sensors", ",".join(selected))

    def _load_direction(self) -> str:
        return self._load_config().get("direction", "1")

    def _on_direction_change(self) -> None:
        self._save_config_value("direction", self.direction_var.get())
        self._update_positive_direction_value_entry()

    def _on_host_mode_change(self) -> None:
        self._save_host_mode(self.host_mode_var.get())

    def _on_sensor_toggle(self, changed_name: str | None = None) -> None:
        if changed_name is not None:
            if self.sensor_vars[changed_name].get():
                self._last_checked_sensor = changed_name
            elif self._last_checked_sensor == changed_name:
                self._last_checked_sensor = None
        self._save_selected_sensors()
        self._update_sensor_value_entry()
        self._update_reset_sensor_value_entry()
        self._update_positive_direction_value_entry()
        self._update_sensor_range_value_entry()

    def _update_sensor_value_entry(self) -> None:
        if not hasattr(self, "sensor_value_var"):
            return
        parts = [f"[{name}],[1]" for name in self.SENSOR_NAMES if self.sensor_vars[name].get()]
        self.sensor_value_var.set(",".join(parts))

    def _update_sensor_range_value_entry(self) -> None:
        if not hasattr(self, "sensor_range_value_var"):
            return
        name = self._last_checked_sensor
        if name is None or not self.sensor_vars[name].get():
            selected = [n for n in self.SENSOR_NAMES if self.sensor_vars[n].get()]
            name = selected[-1] if selected else None
        self.sensor_range_value_var.set(f"[{name}],[1],[2]" if name else "")

    def _update_reset_sensor_value_entry(self) -> None:
        if not hasattr(self, "reset_sensor_value_var"):
            return
        parts = [f"[{name}],[1]" for name in self.RESET_SENSOR_NAMES if self.sensor_vars[name].get()]
        self.reset_sensor_value_var.set(",".join(parts))

    def _update_positive_direction_value_entry(self) -> None:
        if not hasattr(self, "positive_direction_value_var"):
            return
        parts = [f"[{name}],[1]" for name in self.POSITIVE_DIRECTION_SENSOR_NAMES if self.sensor_vars[name].get()]
        direction = self.direction_var.get()
        if direction:
            parts.append(f"[{direction}]")
        self.positive_direction_value_var.set(",".join(parts))

    def _find_api_executable(self) -> Path | None:
        saved = self._load_saved_api_path()
        if saved is not None:
            return saved
        default_path = self.DEFAULT_API_DIR / self.API_EXE_NAME
        return default_path if default_path.is_file() else None

    def _locate_or_browse_api_executable(self) -> Path | None:
        api_path = self._find_api_executable()
        if api_path is not None:
            return api_path

        browse = messagebox.askyesno(
            "NeuLog API",
            f"{self.API_EXE_NAME} could not be found in {self.DEFAULT_API_DIR}.\n\n"
            "Would you like to browse for it?",
            parent=self,
        )
        if not browse:
            return None

        selected = filedialog.askopenfilename(
            title="Select NeuLogAPI.exe",
            filetypes=self._api_filetypes(),
            parent=self,
        )
        if not selected:
            return None

        api_path = Path(selected)
        self._save_api_path(api_path)
        return api_path

    def _api_filetypes(self) -> list[tuple[str, str]]:
        if sys.platform.startswith("win"):
            return [("Applications", "*.exe"), ("All files", "*.*")]
        if sys.platform == "darwin":
            return [("Applications and executables", "*"), ("All files", "*.*")]
        return [("Executables", "*"), ("All files", "*.*")]

    def _launch_api_button(self) -> None:
        api_path = self._locate_or_browse_api_executable()
        if api_path is not None:
            self._launch_api(api_path)

    def _launch_api_silent(self) -> None:
        api_path = self._locate_or_browse_api_executable()
        if api_path is not None:
            self._launch_api(api_path, extra_args=["--quiet"])

    def _launch_api(self, api_path: Path, extra_args: list[str] | None = None) -> None:
        try:
            if self.api_process is not None and self.api_process.poll() is None:
                messagebox.showinfo("NeuLog API", "NeuLog_API is already running from this program.", parent=self)
                return

            extra_args = extra_args or []
            cwd = api_path.parent
            if sys.platform == "darwin" and api_path.suffix.lower() == ".app":
                self.api_process = subprocess.Popen(["open", str(api_path), *extra_args], cwd=str(cwd), text=True)
            else:
                self.api_process = subprocess.Popen([str(api_path), *extra_args], cwd=str(cwd), text=True)
            self.api_path = api_path
            suffix = f" ({' '.join(extra_args)})" if extra_args else ""
            self.status_var.set(f"Launched NeuLog_API: {api_path}{suffix}")
        except OSError as exc:
            messagebox.showerror("Cannot launch NeuLog_API", str(exc), parent=self)
            self.status_var.set(f"Failed to launch NeuLog_API: {exc}")

    def _close_api(self) -> None:
        port = self.port_var.get().strip()

        def done(success: bool, data: str) -> None:
            if success and "ExitAPI_Received" in data:
                messagebox.showinfo("NeuLog API", "NeuLog API was closed successfuly", parent=self)
                self.status_var.set("NeuLog API was closed successfuly")
            else:
                messagebox.showerror(
                    "NeuLog API",
                    f"Could not close NeuLog API\n"
                    f"The NeuLog API is not communicating through port {port} or it is not running",
                    parent=self,
                )
                self.status_var.set("Could not close NeuLog API")

        self.send_command("ExitAPI", callback=done)

    def _start_usb(self) -> None:
        self.send_command("StartUSBSerialConnection")

    def _start_bluetooth(self) -> None:
        self.send_command("StartBluetoothConnection")

    def _check_usb_status(self) -> None:
        self.send_command("GetUSBSerialStatus")

    def _check_bluetooth_status(self) -> None:
        self.send_command("GetBluetoothStatus")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _configure_styles(self) -> None:
        self.configure(bg="white")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background="white")
        style.configure("TFrame", background="white")
        style.configure("TLabelframe", background="white")
        style.configure("TLabelframe.Label", background="white")
        style.configure("TLabel", background="white")
        style.configure("TCheckbutton", background="white")
        style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"), background="white")
        style.configure("Section.TLabelframe.Label", font=("TkDefaultFont", 10, "bold"), background="white")
        style.configure("Mono.TLabel", font=("TkFixedFont", 9), background="white")
        style.configure("Terminal.TFrame", background="black")

    def _build_ui(self) -> None:
        header = ttk.Frame(self, padding=12)
        header.pack(fill="x")
        ttk.Label(header, text="NeuLog API Controller Sample", style="Title.TLabel").pack(anchor="w")

        ttk.Label(header, text="1. Neulog API should run in the background").pack(anchor="w", pady=(10, 0))

        buttons_row = ttk.Frame(header)
        buttons_row.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons_row, text="Check if API runs", command=self._test_server).pack(side="left", padx=3)
        ttk.Button(buttons_row, text="Launch API", command=self._launch_api_button).pack(side="left", padx=3)
        ttk.Button(buttons_row, text="Launch API silent mode", command=self._launch_api_silent).pack(side="left", padx=3)
        ttk.Button(buttons_row, text="Close API", command=self._close_api).pack(side="left", padx=3)
        tk.Checkbutton(
            buttons_row,
            text="Close API when exit",
            variable=self.close_on_exit_var,
            bg="white",
            activebackground="white",
            highlightthickness=0,
        ).pack(side="left", padx=12)

        ttk.Label(
            header,
            text="2. The NeuLog API initial port number is 22001, if this port is not available then port number + 1 will be open.",
        ).pack(anchor="w", pady=(10, 0))

        connection = ttk.Frame(header)
        connection.pack(fill="x", pady=(10, 0))
        ttk.Label(connection, text="API port:").pack(side="left")
        ttk.Entry(connection, textvariable=self.port_var, width=10).pack(side="left", padx=(6, 12))

        host_row = ttk.Frame(header)
        host_row.pack(fill="x", pady=(6, 0))
        ttk.Label(host_row, text="API host:").pack(side="left")
        tk.Radiobutton(
            host_row,
            text="localhost",
            variable=self.host_mode_var,
            value="localhost",
            bg="white",
            activebackground="white",
            highlightthickness=0,
        ).pack(side="left", padx=(6, 0))
        tk.Radiobutton(
            host_row,
            text="127.0.0.1",
            variable=self.host_mode_var,
            value="127.0.0.1",
            bg="white",
            activebackground="white",
            highlightthickness=0,
        ).pack(side="left", padx=(6, 0))

        ttk.Label(header, text="3. Set NeuLog API to work with the connectivity module.").pack(anchor="w", pady=(10, 0))

        connectivity_row = ttk.Frame(header)
        connectivity_row.pack(fill="x", pady=(10, 0))
        ttk.Button(connectivity_row, text="USB", command=self._start_usb).pack(side="left", padx=3)
        ttk.Button(connectivity_row, text="Bluetooth", command=self._start_bluetooth).pack(side="left", padx=3)
        ttk.Button(connectivity_row, text="Check USB status", command=self._check_usb_status).pack(side="left", padx=3)
        ttk.Button(connectivity_row, text="Check BT status", command=self._check_bluetooth_status).pack(side="left", padx=3)

        ttk.Label(
                    header,
                    text="API Terminal:",
                ).pack(anchor="w", pady=(10, 0))

        output = ttk.Frame(header, style="Terminal.TFrame", padding=10)
        output.pack(fill="x", pady=(0, 8))
        self._add_terminal_line(output, self.command_var)
        self._add_terminal_line(output, self.url_var)
        self.result_entry = self._add_terminal_line(output, self.result_var)
        self.result_extra_frame = ttk.Frame(output, style="Terminal.TFrame")
        self.result_extra_frame.pack(fill="x")
        self.result_extra_vars: list[tk.StringVar] = []
        self.result_extra_entries: list[tk.Entry] = []

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        canvas = tk.Canvas(body, highlightthickness=0, bg="white")
        scrollbar = ttk.Scrollbar(body, orient="vertical", command=canvas.yview)
        self.commands_frame = ttk.Frame(canvas)
        self.commands_frame.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=self.commands_frame, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel(canvas)

        sensors_header = ttk.Frame(self.commands_frame, padding=(12, 0))
        sensors_header.pack(fill="x")

        ttk.Label(sensors_header, text="4. choose the sensors to work with").pack(anchor="w", pady=(10, 0))

        self.sensors_frame = ttk.Frame(sensors_header)
        self.sensors_frame.pack(fill="x", pady=(6, 0))
        for name in self.SENSOR_NAMES:
            cb = tk.Checkbutton(
                self.sensors_frame,
                text=name,
                variable=self.sensor_vars[name],
                bg="white",
                activebackground="white",
                highlightthickness=0,
                anchor="w",
                padx=1,
                pady=0,
                borderwidth=0,
            )
            self._sensor_checkbuttons.append(cb)
        self.sensors_frame.bind("<Configure>", self._relayout_sensors)

        ttk.Label(
            sensors_header,
            text="5. all sensors ID set to 1 in this sample, in your project you can connect up to 9 sensors of the same kind (ID 1..9)",
        ).pack(anchor="w", pady=(10, 0))

        self._add_all_commands()

        footer = ttk.Frame(self, padding=(12, 2, 12, 10))
        footer.pack(fill="x")
        ttk.Separator(footer).pack(fill="x", pady=(0, 6))
        ttk.Label(footer, textvariable=self.status_var).pack(anchor="w")

    def _add_terminal_line(self, parent: ttk.Widget, textvariable: tk.StringVar, pack: bool = True) -> tk.Entry:
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            state="readonly",
            readonlybackground="black",
            fg="white",
            font=("TkFixedFont", 9),
            relief="flat",
            highlightthickness=0,
            borderwidth=0,
        )
        if pack:
            entry.pack(fill="x", pady=1)
        return entry

    def _extract_sensor_lines(self, data: str) -> list[str]:
        try:
            parsed = json.loads(data)
        except (ValueError, TypeError):
            return []
        if not isinstance(parsed, dict):
            return []
        lines: list[str] = []
        for value in parsed.values():
            if isinstance(value, list) and value and all(isinstance(item, list) for item in value):
                for item in value:
                    if len(item) < 2:
                        continue
                    name, sensor_id, *samples = item
                    samples_text = ", ".join(str(sample) for sample in samples)
                    lines.append(f"{len(samples)} - {name} [{sensor_id}] - {samples_text}")
        return lines

    def _update_result_extra_lines(self, data: str) -> None:
        lines = self._extract_sensor_lines(data)
        for entry in self.result_extra_entries:
            entry.pack_forget()
        while len(self.result_extra_vars) < len(lines):
            var = tk.StringVar(value="")
            entry = self._add_terminal_line(self.result_extra_frame, var, pack=False)
            self.result_extra_vars.append(var)
            self.result_extra_entries.append(entry)
        for i, line in enumerate(lines):
            self.result_extra_vars[i].set(line)
            self.result_extra_entries[i].pack(fill="x", pady=1)

    def _bind_mousewheel(self, canvas: tk.Canvas) -> None:
        def scroll(event: tk.Event) -> None:
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = -1 if event.delta > 0 else 1
            canvas.yview_scroll(delta, "units")

        # Bound globally (not just while hovering the canvas) so the wheel also
        # scrolls the command list while the pointer is over sections 4/5 or any
        # other widget in the window.
        self.bind_all("<MouseWheel>", scroll)
        self.bind_all("<Button-4>", scroll)
        self.bind_all("<Button-5>", scroll)

    def _relayout_sensors(self, _event=None) -> None:
        frame_width = self.sensors_frame.winfo_width()
        if frame_width <= 1 or not self._sensor_checkbuttons:
            return

        widget_width = max(cb.winfo_reqwidth() for cb in self._sensor_checkbuttons) + 2
        columns = max(1, frame_width // widget_width)
        if columns == self._sensor_columns:
            return
        self._sensor_columns = columns

        for col in range(len(self._sensor_checkbuttons)):
            self.sensors_frame.columnconfigure(col, weight=0)
        for index, cb in enumerate(self._sensor_checkbuttons):
            row, col = divmod(index, columns)
            cb.grid(row=row, column=col, sticky="w", padx=1, pady=0)
        for col in range(columns):
            self.sensors_frame.columnconfigure(col, weight=1)

    def _add_all_commands(self) -> None:
        basic = ttk.LabelFrame(self.commands_frame, text="NeuLog API commands", style="Section.TLabelframe", padding=10)
        basic.pack(fill="x", padx=4, pady=4)

        self._simple_row(basic, "Get API server version", "GetServerVersion")
        self._simple_row(basic, "Get API server status", "GetSeverStatus")
        self.sensor_value_var = tk.StringVar(value="")
        self._input_row(basic, "Get sensor values", "GetSensorValue:", "", value_var=self.sensor_value_var)
        self._update_sensor_value_entry()
        self.reset_sensor_value_var = tk.StringVar(value="")
        self._input_row(basic, "Reset sensor", "ResetSensor:", "", value_var=self.reset_sensor_value_var)
        ttk.Label(
            basic,
            text=f"Reset function available in {', '.join(self.RESET_SENSOR_NAMES)} sensors",
        ).pack(anchor="w", pady=(0, 4))
        self._update_reset_sensor_value_entry()
        self.positive_direction_value_var = tk.StringVar(value="")
        self._input_row(
            basic, "Set positive direction", "SetPositiveDirection:", "", value_var=self.positive_direction_value_var
        )
        direction_frame = ttk.Frame(basic)
        direction_frame.pack(fill="x", pady=(2, 0))
        tk.Checkbutton(
            direction_frame,
            text="Push",
            variable=self.direction_var,
            onvalue="1",
            offvalue="2",
            bg="white",
            activebackground="white",
            highlightthickness=0,
        ).pack(side="left", padx=(0, 12))
        tk.Checkbutton(
            direction_frame,
            text="Pull",
            variable=self.direction_var,
            onvalue="2",
            offvalue="1",
            bg="white",
            activebackground="white",
            highlightthickness=0,
        ).pack(side="left")
        ttk.Label(
            basic,
            text="Direction function available in force and force plate sensors only",
        ).pack(anchor="w", pady=(0, 4))
        self._update_positive_direction_value_entry()
        self.sensor_range_value_var = tk.StringVar(value="")
        self._input_row(
            basic, "Set sensor range", "SetSensorRange:", "", value_var=self.sensor_range_value_var
        )
        self._update_sensor_range_value_entry()
        self._input_row(basic, "Set sensor ID", "SetSensorsID:", "[2]")
        self._input_row(basic, "Set RF ID", "SetRFID:", "[2]")
        self._simple_row(basic, "Exit and close API", "ExitAPI")

        custom = ttk.LabelFrame(self.commands_frame, text="Custom command", style="Section.TLabelframe", padding=10)
        custom.pack(fill="x", padx=4, pady=4)
        self.custom_var = tk.StringVar()
        ttk.Entry(custom, textvariable=self.custom_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(custom, text="Send", command=lambda: self.send_command(self.custom_var.get().strip())).pack(side="left")

    def _simple_row(self, parent: ttk.Widget, label: str, command: str) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=48).pack(side="left")
        ttk.Label(row, text=command, style="Mono.TLabel").pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Send", command=lambda c=command: self.send_command(c)).pack(side="right")

    def _input_row(
        self, parent: ttk.Widget, label: str, prefix: str, default: str, value_var: tk.StringVar | None = None
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=48).pack(side="left")
        value = value_var if value_var is not None else tk.StringVar(value=default)
        ttk.Label(row, text=prefix, style="Mono.TLabel").pack(side="left", padx=(6, 2))
        entry = ttk.Entry(row, textvariable=value)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Send", command=lambda p=prefix, v=value: self.send_command(p + v.get().strip())).pack(side="right")
        entry.bind("<Return>", lambda _e, p=prefix, v=value: self.send_command(p + v.get().strip()))

    # ------------------------------------------------------------------
    # API requests and automatic experiment
    # ------------------------------------------------------------------
    def _valid_port(self) -> int | None:
        text = self.port_var.get().strip()
        if not text.isdigit() or not 1 <= int(text) <= 65535:
            messagebox.showerror("Invalid port", "Enter a port number from 1 to 65535.", parent=self)
            return None
        return int(text)

    def _current_host(self) -> str | None:
        return "localhost" if self.host_mode_var.get() == "localhost" else "127.0.0.1"

    def _test_server(self) -> None:
        port = self.port_var.get().strip()

        def done(success: bool, data: str) -> None:
            if success:
                version = data
                try:
                    version = json.loads(data).get("GetServerVersion", data)
                except (ValueError, AttributeError):
                    pass
                messagebox.showinfo(
                    "NeuLog API",
                    f"NeuLog API is running ok\nserver version {version}",
                    parent=self,
                )
            else:
                messagebox.showerror(
                    "NeuLog API",
                    f"NeuLog API does not run or does not answer in port {port}\n"
                    "Try to run the API or try a different port address",
                    parent=self,
                )

        self.send_command("GetServerVersion", callback=done)

    def send_command(self, command: str, callback=None) -> None:
        command = command.strip()
        if not command:
            messagebox.showwarning("Empty command", "Enter a command first.", parent=self)
            return
        port = self._valid_port()
        if port is None:
            return
        host = self._current_host()
        if host is None:
            return

        url = f"http://{host}:{port}/NeuLogAPI?{command}"
        self.command_var.set(f"Command: {command}")
        self.url_var.set(f"URL: {url}")
        self.result_var.set("Pending...")
        self.result_entry.configure(fg="white")
        self._update_result_extra_lines("")
        self.status_var.set(f"Sending {command}...")

        threading.Thread(target=self._request_worker, args=(command, url, callback), daemon=True).start()

    def _request_worker(self, command: str, url: str, callback) -> None:
        success = False
        data = ""
        error = ""
        try:
            with _no_proxy_opener.open(url, timeout=self.TIMEOUT_SECONDS) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                data = response.read().decode(charset, errors="replace")
            success = True
        except HTTPError as exc:
            error = f"HTTP {exc.code}: {exc.reason}"
        except URLError as exc:
            error = f"Connection error: {exc.reason}"
        except TimeoutError:
            error = f"Timeout after {self.TIMEOUT_SECONDS:g} seconds"
        except Exception as exc:
            error = f"Error: {exc}"

        self.after(0, self._finish_request, command, success, data, error, callback)

    def _finish_request(self, command: str, success: bool, data: str, error: str, callback) -> None:
        if success:
            self.result_entry.configure(fg="white")
            self.result_var.set(f"Result: {data}")
            self._update_result_extra_lines(data)
            self.status_var.set(f"Completed: {command}")
        else:
            self.result_entry.configure(fg="white")
            self.result_var.set(f"Error! {error}")
            self._update_result_extra_lines("")
            self.status_var.set(f"Failed: {command}")

        if callback is not None:
            callback(success, data if success else error)

    def _on_close(self) -> None:
        if self.close_on_exit_var.get():
            self._close_api_blocking()
        self.destroy()

    def _close_api_blocking(self) -> None:
        port = self.port_var.get().strip()
        if not port.isdigit():
            return
        host = "localhost" if self.host_mode_var.get() == "localhost" else "127.0.0.1"
        url = f"http://{host}:{port}/NeuLogAPI?ExitAPI"
        try:
            _no_proxy_opener.open(url, timeout=self.TIMEOUT_SECONDS)
        except Exception:
            pass


def main() -> None:
    app = NeuLogController()
    app.mainloop()


if __name__ == "__main__":
    main()
