"""
Interactive Tkinter Desktop GUI for UNIX MLFQ Scheduling Simulator.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
from typing import Any, List

from mlfq.scheduler import MLFQScheduler
from mlfq.generator import generate_comparative_workload


QUEUE_COLORS = {
    0: "#3b82f6",  # Blue (Q0 - Highest)
    1: "#10b981",  # Emerald (Q1 - Medium)
    2: "#f59e0b",  # Amber (Q2 - Lowest)
    -1: "#94a3b8"  # Slate (IDLE)
}

PID_PALETTE = [
    "#3b82f6", "#10b981", "#8b5cf6", "#ec4899", 
    "#f97316", "#06b6d4", "#eab308", "#6366f1",
    "#14b8a6", "#f43f5e", "#84cc16", "#a855f7"
]


class MLFQSimulatorGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UNIX Round Robin MLFQ Simulator - Group 7")
        self.geometry("1100x780")
        self.minsize(900, 650)

        # Style configuration
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        
        self.fixed_summary = None
        self.var_summary = None

        self._build_header()
        self._build_control_panel()
        self._build_notebook()
        self._build_statusbar()

        # Run initial default simulation
        self.run_simulation()

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#1e293b", padx=16, pady=12)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="UNIX Process Scheduling: Round Robin with Multilevel Feedback (MLFQ)",
            font=("Segoe UI", 15, "bold"),
            fg="#f8fafc",
            bg="#1e293b"
        )
        title_lbl.pack(anchor="w")

        info_lbl = tk.Label(
            header_frame,
            text="OS Group Project (Group 7) | Members: VEERAPANENI VARALAKSHMI (AP24110010509), GANDHAM SAI POOJITHA (AP24110010538), KANDIMALLA KEERTHI SREE (AP24110012001), ARADHYA SINGH (AP24110011723)",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg="#1e293b"
        )
        info_lbl.pack(anchor="w", pady=(2, 0))

    def _build_control_panel(self):
        control_frame = ttk.LabelFrame(self, text="Simulation Parameters", padding=10)
        control_frame.pack(fill=tk.X, padx=14, pady=8)

        # Inputs grid
        row1 = ttk.Frame(control_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Time Quantum (Q):").pack(side=tk.LEFT, padx=(0, 4))
        self.quantum_var = tk.IntVar(value=3)
        ttk.Spinbox(row1, from_=3, to=3, textvariable=self.quantum_var, width=5).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Max Sim Time (T):").pack(side=tk.LEFT, padx=(0, 4))
        self.sim_time_var = tk.IntVar(value=60)
        ttk.Spinbox(row1, from_=10, to=500, textvariable=self.sim_time_var, width=6).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Processes (N):").pack(side=tk.LEFT, padx=(0, 4))
        self.num_procs_var = tk.IntVar(value=6)
        ttk.Spinbox(row1, from_=6, to=6, textvariable=self.num_procs_var, width=5).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Fixed Burst:").pack(side=tk.LEFT, padx=(0, 4))
        self.fixed_burst_var = tk.IntVar(value=6)
        ttk.Spinbox(row1, from_=1, to=50, textvariable=self.fixed_burst_var, width=5).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Var Burst Min/Max:").pack(side=tk.LEFT, padx=(0, 4))
        self.min_burst_var = tk.IntVar(value=2)
        ttk.Spinbox(row1, from_=1, to=20, textvariable=self.min_burst_var, width=4).pack(side=tk.LEFT, padx=(0, 4))
        self.max_burst_var = tk.IntVar(value=14)
        ttk.Spinbox(row1, from_=2, to=50, textvariable=self.max_burst_var, width=4).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(row1, text="Seed:").pack(side=tk.LEFT, padx=(0, 4))
        self.seed_var = tk.IntVar(value=42)
        ttk.Spinbox(row1, from_=0, to=9999, textvariable=self.seed_var, width=6).pack(side=tk.LEFT, padx=(0, 16))

        # Action Buttons
        btn_run = tk.Button(
            row1,
            text="▶ Run Simulation",
            command=self.run_simulation,
            bg="#2563eb",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=3,
            cursor="hand2"
        )
        btn_run.pack(side=tk.LEFT, padx=(10, 6))

        btn_rand_seed = ttk.Button(row1, text="🎲 New Seed", command=self._randomize_seed)
        btn_rand_seed.pack(side=tk.LEFT, padx=(0, 6))

        btn_html = ttk.Button(row1, text="🌐 Open Web Report", command=self._open_web_dashboard)
        btn_html.pack(side=tk.LEFT, padx=(0, 6))

    def _randomize_seed(self):
        self.seed_var.set(random.randint(1, 9999))
        self.run_simulation()

    def _open_web_dashboard(self):
        try:
            import web_dashboard
            web_dashboard.generate_and_open()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open dashboard: {e}")

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        # Tab 1: Comparison & KPI Cards
        self.tab_compare = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_compare, text="  📊 Comparative Analysis  ")
        self._build_compare_tab()

        # Tab 2: Fixed Burst
        self.tab_fixed = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fixed, text="  ⏱ Fixed Burst Mode  ")
        self._build_fixed_tab()

        # Tab 3: Variable Burst
        self.tab_variable = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_variable, text="  🔀 Variable Burst Mode  ")
        self._build_variable_tab()

        # Tab 4: Execution Logs
        self.tab_logs = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_logs, text="  📜 Event Logs  ")
        self._build_logs_tab()

    def _build_compare_tab(self):
        # KPI Cards Frame
        self.kpi_frame = ttk.Frame(self.tab_compare, padding=10)
        self.kpi_frame.pack(fill=tk.X)

        # Canvas for comparative bar chart
        chart_group = ttk.LabelFrame(self.tab_compare, text="Metrics Comparison Visualizer", padding=10)
        chart_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.canvas_chart = tk.Canvas(chart_group, bg="#ffffff", highlightthickness=1, highlightbackground="#e2e8f0")
        self.canvas_chart.pack(fill=tk.BOTH, expand=True)

    def _build_fixed_tab(self):
        pane = ttk.PanedWindow(self.tab_fixed, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Gantt chart group
        gantt_grp = ttk.LabelFrame(pane, text="Gantt Chart (Round Robin Time Slicing, Q=3)", padding=6)
        pane.add(gantt_grp, weight=1)

        self.canvas_fixed_gantt = tk.Canvas(gantt_grp, bg="#ffffff", height=130, highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas_fixed_gantt.pack(fill=tk.BOTH, expand=True)

        # Process Table
        tbl_grp = ttk.LabelFrame(pane, text="Fixed Burst Process Execution Table", padding=6)
        pane.add(tbl_grp, weight=2)
        self.fixed_tree = self._create_process_tree(tbl_grp)

    def _build_variable_tab(self):
        pane = ttk.PanedWindow(self.tab_variable, orient=tk.VERTICAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        gantt_grp = ttk.LabelFrame(pane, text="Gantt Chart (Round Robin Time Slicing, Q=3)", padding=6)
        pane.add(gantt_grp, weight=1)

        self.canvas_var_gantt = tk.Canvas(gantt_grp, bg="#ffffff", height=130, highlightthickness=1, highlightbackground="#cbd5e1")
        self.canvas_var_gantt.pack(fill=tk.BOTH, expand=True)

        tbl_grp = ttk.LabelFrame(pane, text="Variable (Randomized) Burst Process Execution Table", padding=6)
        pane.add(tbl_grp, weight=2)
        self.var_tree = self._create_process_tree(tbl_grp)

    def _create_process_tree(self, parent):
        cols = ("PID", "Arrival", "Burst", "Remaining", "Queue", "State", "Finish", "TAT", "WT", "RT")
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=8)
        
        col_widths = {"PID": 60, "Arrival": 70, "Burst": 70, "Remaining": 85, "Queue": 70, "State": 90, "Finish": 70, "TAT": 70, "WT": 70, "RT": 70}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=col_widths.get(c, 70), anchor="center")

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def _build_logs_tab(self):
        frame = ttk.Frame(self.tab_logs, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 10), bg="#0f172a", fg="#38bdf8")
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w", font=("Segoe UI", 9), bg="#f1f5f9", fg="#475569", padx=8, pady=3)
        bar.pack(side=tk.BOTTOM, fill=tk.X)

    def run_simulation(self):
        try:
            q = self.quantum_var.get()
            t_max = self.sim_time_var.get()
            n_procs = self.num_procs_var.get()
            fixed_burst = self.fixed_burst_var.get()
            min_b = self.min_burst_var.get()
            max_b = self.max_burst_var.get()
            seed = self.seed_var.get()

            if min_b > max_b:
                messagebox.showerror("Error", "Min Burst cannot be greater than Max Burst.")
                return

            f_procs, v_procs = generate_comparative_workload(
                count=n_procs,
                fixed_burst=fixed_burst,
                min_burst=min_b,
                max_burst=max_b,
                max_arrival_time=20,
                seed=seed
            )

            # Run Fixed
            sched_fixed = MLFQScheduler(time_slice=q, num_queues=3, max_simulation_time=t_max)
            self.fixed_summary = sched_fixed.run(f_procs)

            # Run Variable
            sched_var = MLFQScheduler(time_slice=q, num_queues=3, max_simulation_time=t_max)
            self.var_summary = sched_var.run(v_procs)

            # Update UI views
            self._update_tables()
            self._draw_gantt_chart(self.canvas_fixed_gantt, self.fixed_summary["gantt_chart"], t_max)
            self._draw_gantt_chart(self.canvas_var_gantt, self.var_summary["gantt_chart"], t_max)
            self._update_kpi_cards()
            self._draw_comparison_chart()
            self._update_logs()

            self.status_var.set(
                f"Simulated {n_procs} processes over {t_max} time units (Quantum={q}). "
                f"Fixed: Completed {self.fixed_summary['completed_count']}, AWT={self.fixed_summary['avg_waiting_time']} | "
                f"Variable: Completed {self.var_summary['completed_count']}, AWT={self.var_summary['avg_waiting_time']}"
            )

        except Exception as e:
            messagebox.showerror("Simulation Error", str(e))

    def _update_tables(self):
        # Update Fixed Table
        for row in self.fixed_tree.get_children():
            self.fixed_tree.delete(row)
        for p in self.fixed_summary["all_processes"]:
            self.fixed_tree.insert("", tk.END, values=(
                p.pid, p.arrival_time, p.burst_time, p.remaining_time,
                f"Q{p.current_queue}", p.state.value,
                p.completion_time if p.completion_time is not None else "-",
                p.turnaround_time if p.turnaround_time is not None else "-",
                p.waiting_time,
                p.response_time if p.response_time is not None else "-"
            ))

        # Update Variable Table
        for row in self.var_tree.get_children():
            self.var_tree.delete(row)
        for p in self.var_summary["all_processes"]:
            self.var_tree.insert("", tk.END, values=(
                p.pid, p.arrival_time, p.burst_time, p.remaining_time,
                f"Q{p.current_queue}", p.state.value,
                p.completion_time if p.completion_time is not None else "-",
                p.turnaround_time if p.turnaround_time is not None else "-",
                p.waiting_time,
                p.response_time if p.response_time is not None else "-"
            ))

    def _draw_gantt_chart(self, canvas: tk.Canvas, segments: List[Any], max_time: int):
        canvas.delete("all")
        canvas.update_idletasks()

        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 100:
            w = 800
        if h < 80:
            h = 130

        pad_x = 30
        pad_top = 25
        bar_height = 45
        axis_y = pad_top + bar_height + 15

        plot_width = w - (2 * pad_x)
        total_time = max(max_time, segments[-1].end_time if segments else 1)
        scale = plot_width / total_time

        # Draw axis line
        canvas.create_line(pad_x, axis_y, pad_x + plot_width, axis_y, fill="#94a3b8", width=1.5)

        for seg in segments:
            x1 = pad_x + (seg.start_time * scale)
            x2 = pad_x + (seg.end_time * scale)
            
            if seg.pid == "IDLE":
                fill_color = "#e2e8f0"
                txt_color = "#64748b"
                label = "IDLE"
            else:
                pid_num = int(seg.pid.replace("P", "")) if seg.pid.replace("P", "").isdigit() else 1
                fill_color = PID_PALETTE[(pid_num - 1) % len(PID_PALETTE)]
                txt_color = "#ffffff"
                label = f"{seg.pid} (Q{seg.queue_level})"

            # Segment rectangle
            canvas.create_rectangle(x1, pad_top, x2, pad_top + bar_height, fill=fill_color, outline="#ffffff", width=1.5)

            # Label if segment wide enough
            if (x2 - x1) > 28:
                canvas.create_text((x1 + x2) / 2, pad_top + (bar_height / 2), text=label, fill=txt_color, font=("Segoe UI", 9, "bold"))
            elif (x2 - x1) > 14:
                canvas.create_text((x1 + x2) / 2, pad_top + (bar_height / 2), text=seg.pid, fill=txt_color, font=("Segoe UI", 8))

            # Tick mark and label on axis
            canvas.create_line(x1, axis_y - 4, x1, axis_y + 4, fill="#64748b")
            canvas.create_text(x1, axis_y + 12, text=str(seg.start_time), font=("Segoe UI", 8), fill="#475569")

        # Final end tick
        last_x = pad_x + (total_time * scale)
        canvas.create_line(last_x, axis_y - 4, last_x, axis_y + 4, fill="#64748b")
        canvas.create_text(last_x, axis_y + 12, text=str(total_time), font=("Segoe UI", 8), fill="#475569")

    def _update_kpi_cards(self):
        for widget in self.kpi_frame.winfo_children():
            widget.destroy()

        metrics = [
            ("Average Waiting Time (AWT)", f"{self.fixed_summary['avg_waiting_time']} units", f"{self.var_summary['avg_waiting_time']} units"),
            ("Average Turnaround Time (ATT)", f"{self.fixed_summary['avg_turnaround_time']} units", f"{self.var_summary['avg_turnaround_time']} units"),
            ("Completed Processes", f"{self.fixed_summary['completed_count']} / {self.fixed_summary['total_processes']}", f"{self.var_summary['completed_count']} / {self.var_summary['total_processes']}"),
            ("CPU Utilization", f"{self.fixed_summary['cpu_utilization']}%", f"{self.var_summary['cpu_utilization']}%"),
            ("Throughput", f"{self.fixed_summary['throughput']} p/u", f"{self.var_summary['throughput']} p/u"),
        ]

        for i, (title, f_val, v_val) in enumerate(metrics):
            card = tk.Frame(self.kpi_frame, bg="#f8fafc", bd=1, relief=tk.SOLID, padx=10, pady=8)
            card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4)

            tk.Label(card, text=title, font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#f8fafc").pack(anchor="w")
            
            row = tk.Frame(card, bg="#f8fafc")
            row.pack(fill=tk.X, pady=(4, 0))

            tk.Label(row, text="Fixed: ", font=("Segoe UI", 8), fg="#475569", bg="#f8fafc").pack(side=tk.LEFT)
            tk.Label(row, text=f_val, font=("Segoe UI", 10, "bold"), fg="#2563eb", bg="#f8fafc").pack(side=tk.LEFT)

            row2 = tk.Frame(card, bg="#f8fafc")
            row2.pack(fill=tk.X, pady=(2, 0))
            tk.Label(row2, text="Variable: ", font=("Segoe UI", 8), fg="#475569", bg="#f8fafc").pack(side=tk.LEFT)
            tk.Label(row2, text=v_val, font=("Segoe UI", 10, "bold"), fg="#059669", bg="#f8fafc").pack(side=tk.LEFT)

    def _draw_comparison_chart(self):
        c = self.canvas_chart
        c.delete("all")
        c.update_idletasks()

        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100:
            w = 700
        if h < 100:
            h = 280

        pad_left = 70
        pad_bottom = 50
        chart_w = w - pad_left - 40
        chart_h = h - pad_bottom - 40

        # Bar categories: AWT, ATT, ART, CPU Util (/10)
        categories = ["Waiting Time (AWT)", "Turnaround Time (ATT)", "Response Time (ART)", "CPU Util (%)"]
        f_vals = [
            self.fixed_summary["avg_waiting_time"],
            self.fixed_summary["avg_turnaround_time"],
            self.fixed_summary["avg_response_time"],
            self.fixed_summary["cpu_utilization"]
        ]
        v_vals = [
            self.var_summary["avg_waiting_time"],
            self.var_summary["avg_turnaround_time"],
            self.var_summary["avg_response_time"],
            self.var_summary["cpu_utilization"]
        ]

        max_val = max(max(f_vals), max(v_vals), 10) * 1.15

        # Draw Y axis
        c.create_line(pad_left, 30, pad_left, 30 + chart_h, fill="#94a3b8", width=1.5)
        # Draw X axis
        c.create_line(pad_left, 30 + chart_h, pad_left + chart_w, 30 + chart_h, fill="#94a3b8", width=1.5)

        # Y axis ticks
        for i in range(5):
            val = round(max_val * (i / 4), 1)
            y = 30 + chart_h - (chart_h * (i / 4))
            c.create_line(pad_left - 4, y, pad_left, y, fill="#94a3b8")
            c.create_text(pad_left - 8, y, text=str(val), font=("Segoe UI", 8), fill="#64748b", anchor="e")
            if i > 0:
                c.create_line(pad_left, y, pad_left + chart_w, y, fill="#f1f5f9", dash=(3, 3))

        # Bars
        group_width = chart_w / len(categories)
        bar_w = min(35, (group_width - 25) / 2)

        for i, cat in enumerate(categories):
            cx = pad_left + (i * group_width) + (group_width / 2)
            
            # Fixed Bar (Blue)
            f_h = (f_vals[i] / max_val) * chart_h
            bx1 = cx - bar_w - 2
            bx2 = cx - 2
            by1 = 30 + chart_h - f_h
            by2 = 30 + chart_h
            c.create_rectangle(bx1, by1, bx2, by2, fill="#3b82f6", outline="")
            c.create_text((bx1 + bx2) / 2, by1 - 8, text=str(f_vals[i]), font=("Segoe UI", 8, "bold"), fill="#1d4ed8")

            # Var Bar (Green)
            v_h = (v_vals[i] / max_val) * chart_h
            vx1 = cx + 2
            vx2 = cx + bar_w + 2
            vy1 = 30 + chart_h - v_h
            vy2 = 30 + chart_h
            c.create_rectangle(vx1, vy1, vx2, vy2, fill="#10b981", outline="")
            c.create_text((vx1 + vx2) / 2, vy1 - 8, text=str(v_vals[i]), font=("Segoe UI", 8, "bold"), fill="#047857")

            # Category Label
            c.create_text(cx, 30 + chart_h + 18, text=cat, font=("Segoe UI", 8, "bold"), fill="#334155")

        # Legend
        c.create_rectangle(w - 220, 10, w - 205, 22, fill="#3b82f6", outline="")
        c.create_text(w - 200, 16, text="Fixed Burst", font=("Segoe UI", 8, "bold"), fill="#334155", anchor="w")

        c.create_rectangle(w - 110, 10, w - 95, 22, fill="#10b981", outline="")
        c.create_text(w - 90, 16, text="Variable Burst", font=("Segoe UI", 8, "bold"), fill="#334155", anchor="w")

    def _update_logs(self):
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert(tk.END, "=== FIXED BURST SIMULATION EVENT LOG ===\n")
        for line in self.fixed_summary["event_log"]:
            self.log_text.insert(tk.END, line + "\n")
        self.log_text.insert(tk.END, "\n=== VARIABLE (RANDOMIZED) BURST SIMULATION EVENT LOG ===\n")
        for line in self.var_summary["event_log"]:
            self.log_text.insert(tk.END, line + "\n")


def launch_gui():
    app = MLFQSimulatorGUI()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
