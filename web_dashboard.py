"""
Web Dashboard Generator for UNIX MLFQ Scheduling Simulation.
Generates an interactive, standalone offline HTML/JS/CSS dashboard.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import sys
import os
import json
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from mlfq.pcb import ProcessControlBlock
from mlfq.scheduler import MLFQScheduler
from mlfq.generator import generate_comparative_workload

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UNIX MLFQ Scheduler Simulation - Group 7</title>
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --slate-900: #0f172a;
            --slate-800: #1e293b;
            --slate-700: #334155;
            --slate-100: #f1f5f9;
            --slate-50: #f8fafc;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        body { background: #f8fafc; color: #1e293b; line-height: 1.5; padding-bottom: 40px; }
        header { background: var(--slate-900); color: white; padding: 24px 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        .header-title { font-size: 24px; font-weight: 700; }
        .header-subtitle { color: #94a3b8; font-size: 14px; margin-top: 4px; }
        .group-badge { display: inline-block; background: #3b82f6; color: white; padding: 3px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-left: 10px; }
        .container { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
        
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .kpi-card { background: white; border-radius: 12px; padding: 18px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .kpi-label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #64748b; font-weight: 600; }
        .kpi-vals { display: flex; justify-content: space-between; align-items: baseline; margin-top: 10px; }
        .kpi-val-box { }
        .kpi-val-title { font-size: 11px; color: #94a3b8; }
        .kpi-val { font-size: 20px; font-weight: 700; }
        .val-fixed { color: var(--primary); }
        .val-var { color: var(--success); }

        .card { background: white; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 24px; overflow: hidden; }
        .card-header { padding: 16px 20px; border-bottom: 1px solid #e2e8f0; font-weight: 700; font-size: 16px; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
        .card-body { padding: 20px; }

        .gantt-svg { width: 100%; height: 90px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }

        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th { background: #f1f5f9; color: #475569; padding: 10px 14px; font-weight: 600; border-bottom: 1px solid #cbd5e1; }
        td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
        tr:hover { background: #f8fafc; }
        .status-badge { padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; }
        .status-terminated { background: #dcfce7; color: #15803d; }
        .status-ready { background: #fef3c7; color: #b45309; }
        .status-running { background: #dbeafe; color: #1d4ed8; }

        .comparison-table td:nth-child(2) { font-weight: 600; color: var(--primary); }
        .comparison-table td:nth-child(3) { font-weight: 600; color: var(--success); }

        .members-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
        .member-card { background: #f1f5f9; border-radius: 8px; padding: 12px 16px; border-left: 4px solid var(--primary); }
        .member-id { font-size: 12px; font-weight: 700; color: var(--primary); }
        .member-name { font-size: 14px; font-weight: 600; color: var(--slate-800); }

        .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
        .tab-btn { padding: 8px 16px; border-radius: 8px; border: none; background: #e2e8f0; color: #475569; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .tab-btn.active { background: var(--primary); color: white; }
    </style>
</head>
<body>

<header>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div class="header-title">UNIX Round Robin Time Slicing with Multilevel Feedback (MLFQ) <span class="group-badge">Group 7</span></div>
            <div class="header-subtitle">Operating Systems Project &bull; Time Slice = 3 units &bull; Fixed vs. Variable (Randomized) Burst Simulation</div>
        </div>
    </div>
</header>

<div class="container">
    <!-- Group Members Card -->
    <div class="card">
        <div class="card-header">👥 Project Group 7 Details</div>
        <div class="card-body">
            <div class="members-grid">
                <div class="member-card">
                    <div class="member-id">AP24110010509</div>
                    <div class="member-name">VEERAPANENI VARALAKSHMI</div>
                </div>
                <div class="member-card">
                    <div class="member-id">AP24110010538</div>
                    <div class="member-name">GANDHAM SAI POOJITHA</div>
                </div>
                <div class="member-card">
                    <div class="member-id">AP24110012001</div>
                    <div class="member-name">KANDIMALLA KEERTHI SREE</div>
                </div>
                <div class="member-card">
                    <div class="member-id">AP24110011723</div>
                    <div class="member-name">ARADHYA SINGH</div>
                </div>
            </div>
        </div>
    </div>

    <!-- KPI Grid -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">Average Waiting Time (AWT)</div>
            <div class="kpi-vals">
                <div class="kpi-val-box"><div class="kpi-val-title">Fixed</div><div class="kpi-val val-fixed">{{FIXED_AWT}}</div></div>
                <div class="kpi-val-box"><div class="kpi-val-title">Variable</div><div class="kpi-val val-var">{{VAR_AWT}}</div></div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Average Turnaround Time (ATT)</div>
            <div class="kpi-vals">
                <div class="kpi-val-box"><div class="kpi-val-title">Fixed</div><div class="kpi-val val-fixed">{{FIXED_ATT}}</div></div>
                <div class="kpi-val-box"><div class="kpi-val-title">Variable</div><div class="kpi-val val-var">{{VAR_ATT}}</div></div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Completed Processes</div>
            <div class="kpi-vals">
                <div class="kpi-val-box"><div class="kpi-val-title">Fixed</div><div class="kpi-val val-fixed">{{FIXED_COMPLETED}} / {{TOTAL_PROCS}}</div></div>
                <div class="kpi-val-box"><div class="kpi-val-title">Variable</div><div class="kpi-val val-var">{{VAR_COMPLETED}} / {{TOTAL_PROCS}}</div></div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">CPU Utilization</div>
            <div class="kpi-vals">
                <div class="kpi-val-box"><div class="kpi-val-title">Fixed</div><div class="kpi-val val-fixed">{{FIXED_CPU}}%</div></div>
                <div class="kpi-val-box"><div class="kpi-val-title">Variable</div><div class="kpi-val val-var">{{VAR_CPU}}%</div></div>
            </div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">Throughput (Proc/Unit)</div>
            <div class="kpi-vals">
                <div class="kpi-val-box"><div class="kpi-val-title">Fixed</div><div class="kpi-val val-fixed">{{FIXED_THROUGHPUT}}</div></div>
                <div class="kpi-val-box"><div class="kpi-val-title">Variable</div><div class="kpi-val val-var">{{VAR_THROUGHPUT}}</div></div>
            </div>
        </div>
    </div>

    <!-- Comparative Summary Table -->
    <div class="card">
        <div class="card-header">📊 Side-by-Side Comparative Summary</div>
        <div class="card-body">
            <table class="comparison-table">
                <thead>
                    <tr><th>Performance Metric</th><th>Fixed Burst Mode</th><th>Variable (Randomized) Burst Mode</th></tr>
                </thead>
                <tbody>
                    <tr><td>Total Processes Generated</td><td>{{TOTAL_PROCS}}</td><td>{{TOTAL_PROCS}}</td></tr>
                    <tr><td>Completed Processes</td><td>{{FIXED_COMPLETED}}</td><td>{{VAR_COMPLETED}}</td></tr>
                    <tr><td>Incomplete / In-Flight</td><td>{{FIXED_INCOMPLETE}}</td><td>{{VAR_INCOMPLETE}}</td></tr>
                    <tr><td>Round Robin Time Quantum</td><td>3 units</td><td>3 units</td></tr>
                    <tr><td>Simulation Time Limit</td><td>{{SIM_TIME}} units</td><td>{{SIM_TIME}} units</td></tr>
                    <tr><td>Average Waiting Time (AWT)</td><td>{{FIXED_AWT}} units</td><td>{{VAR_AWT}} units</td></tr>
                    <tr><td>Average Turnaround Time (ATT)</td><td>{{FIXED_ATT}} units</td><td>{{VAR_ATT}} units</td></tr>
                    <tr><td>Average Response Time (ART)</td><td>{{FIXED_ART}} units</td><td>{{VAR_ART}} units</td></tr>
                    <tr><td>CPU Utilization</td><td>{{FIXED_CPU}}%</td><td>{{VAR_CPU}}%</td></tr>
                    <tr><td>Throughput</td><td>{{FIXED_THROUGHPUT}}</td><td>{{VAR_THROUGHPUT}}</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Fixed Burst Section -->
    <div class="card">
        <div class="card-header">⏱ Fixed Burst Simulation (Burst = {{FIXED_BURST_VAL}} units, Quantum = 3)</div>
        <div class="card-body">
            <div style="margin-bottom:12px; font-weight:600; color:#475569;">Gantt Chart Timeline:</div>
            {{FIXED_GANTT_SVG}}
            <div style="margin-top:20px;">
                {{FIXED_TABLE_HTML}}
            </div>
        </div>
    </div>

    <!-- Variable Burst Section -->
    <div class="card">
        <div class="card-header">🔀 Variable (Randomized) Burst Simulation (Quantum = 3)</div>
        <div class="card-body">
            <div style="margin-bottom:12px; font-weight:600; color:#475569;">Gantt Chart Timeline:</div>
            {{VAR_GANTT_SVG}}
            <div style="margin-top:20px;">
                {{VAR_TABLE_HTML}}
            </div>
        </div>
    </div>
</div>

</body>
</html>
"""

PID_COLORS = [
    "#3b82f6", "#10b981", "#8b5cf6", "#ec4899", 
    "#f97316", "#06b6d4", "#eab308", "#6366f1",
    "#14b8a6", "#f43f5e", "#84cc16", "#a855f7"
]

def render_svg_gantt(segments: list, max_time: int) -> str:
    total_time = max(max_time, segments[-1].end_time if segments else 1)
    view_width = 1100
    bar_y = 15
    bar_h = 40
    axis_y = 65

    svg_parts = [f'<svg class="gantt-svg" viewBox="0 0 {view_width} 90" xmlns="http://www.w3.org/2000/svg">']
    # axis line
    svg_parts.append(f'<line x1="20" y1="{axis_y}" x2="{view_width - 20}" y2="{axis_y}" stroke="#94a3b8" stroke-width="1.5" />')

    plot_w = view_width - 40
    scale = plot_w / total_time

    for seg in segments:
        x1 = 20 + (seg.start_time * scale)
        x2 = 20 + (seg.end_time * scale)
        w = max(1.0, x2 - x1)

        if seg.pid == "IDLE":
            color = "#e2e8f0"
            text_color = "#64748b"
            label = "IDLE"
        else:
            p_num = int(seg.pid.replace("P", "")) if seg.pid.replace("P", "").isdigit() else 1
            color = PID_COLORS[(p_num - 1) % len(PID_COLORS)]
            text_color = "#ffffff"
            label = f"{seg.pid} (Q{seg.queue_level})"

        svg_parts.append(f'<rect x="{x1:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{color}" stroke="#ffffff" stroke-width="1" rx="4"/>')
        if w > 36:
            svg_parts.append(f'<text x="{(x1 + x2)/2:.1f}" y="{bar_y + 24}" fill="{text_color}" font-size="11" font-weight="bold" text-anchor="middle">{label}</text>')
        elif w > 18:
            svg_parts.append(f'<text x="{(x1 + x2)/2:.1f}" y="{bar_y + 24}" fill="{text_color}" font-size="9" text-anchor="middle">{seg.pid}</text>')

        # tick mark
        svg_parts.append(f'<line x1="{x1:.1f}" y1="{axis_y - 3}" x2="{x1:.1f}" y2="{axis_y + 3}" stroke="#64748b" />')
        svg_parts.append(f'<text x="{x1:.1f}" y="{axis_y + 14}" font-size="9" fill="#475569" text-anchor="middle">{seg.start_time}</text>')

    last_x = 20 + (total_time * scale)
    svg_parts.append(f'<line x1="{last_x:.1f}" y1="{axis_y - 3}" x2="{last_x:.1f}" y2="{axis_y + 3}" stroke="#64748b" />')
    svg_parts.append(f'<text x="{last_x:.1f}" y="{axis_y + 14}" font-size="9" fill="#475569" text-anchor="middle">{total_time}</text>')
    svg_parts.append('</svg>')
    return "".join(svg_parts)


def render_html_table(processes: list) -> str:
    rows = []
    for p in sorted(processes, key=lambda x: int(x.pid.replace("P", "")) if x.pid.replace("P", "").isdigit() else x.pid):
        status_cls = "status-terminated" if p.is_completed else "status-ready"
        finish = p.completion_time if p.completion_time is not None else "-"
        tat = p.turnaround_time if p.turnaround_time is not None else "-"
        rt = p.response_time if p.response_time is not None else "-"
        rows.append(f"""
        <tr>
            <td><strong>{p.pid}</strong></td>
            <td>{p.arrival_time}</td>
            <td>{p.burst_time}</td>
            <td>{p.remaining_time}</td>
            <td><span class="group-badge" style="background:#64748b;">Q{p.current_queue}</span></td>
            <td><span class="status-badge {status_cls}">{p.state.value}</span></td>
            <td>{finish}</td>
            <td><strong>{tat}</strong></td>
            <td><strong>{p.waiting_time}</strong></td>
            <td>{rt}</td>
        </tr>
        """)

    return f"""
    <table>
        <thead>
            <tr>
                <th>PID</th><th>Arrival</th><th>Burst</th><th>Remaining</th>
                <th>Final Queue</th><th>State</th><th>Completion</th>
                <th>Turnaround (TAT)</th><th>Waiting (WT)</th><th>Response (RT)</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows)}
        </tbody>
    </table>
    """


def generate_html_report(
    num_procs: int = 8,
    sim_time: int = 60,
    time_slice: int = 3,
    fixed_burst: int = 6,
    min_burst: int = 2,
    max_burst: int = 14,
    seed: int = 42
) -> Path:
    f_procs, v_procs = generate_comparative_workload(
        count=num_procs,
        fixed_burst=fixed_burst,
        min_burst=min_burst,
        max_burst=max_burst,
        max_arrival_time=20,
        seed=seed
    )

    sched_fixed = MLFQScheduler(time_slice=time_slice, num_queues=3, max_simulation_time=sim_time)
    f_summary = sched_fixed.run(f_procs)

    sched_var = MLFQScheduler(time_slice=time_slice, num_queues=3, max_simulation_time=sim_time)
    v_summary = sched_var.run(v_procs)

    out_html = HTML_TEMPLATE
    replacements = {
        "{{FIXED_AWT}}": str(f_summary["avg_waiting_time"]),
        "{{VAR_AWT}}": str(v_summary["avg_waiting_time"]),
        "{{FIXED_ATT}}": str(f_summary["avg_turnaround_time"]),
        "{{VAR_ATT}}": str(v_summary["avg_turnaround_time"]),
        "{{FIXED_ART}}": str(f_summary["avg_response_time"]),
        "{{VAR_ART}}": str(v_summary["avg_response_time"]),
        "{{TOTAL_PROCS}}": str(num_procs),
        "{{FIXED_COMPLETED}}": str(f_summary["completed_count"]),
        "{{VAR_COMPLETED}}": str(v_summary["completed_count"]),
        "{{FIXED_INCOMPLETE}}": str(f_summary["incomplete_count"]),
        "{{VAR_INCOMPLETE}}": str(v_summary["incomplete_count"]),
        "{{FIXED_CPU}}": str(f_summary["cpu_utilization"]),
        "{{VAR_CPU}}": str(v_summary["cpu_utilization"]),
        "{{FIXED_THROUGHPUT}}": str(f_summary["throughput"]),
        "{{VAR_THROUGHPUT}}": str(v_summary["throughput"]),
        "{{SIM_TIME}}": str(sim_time),
        "{{FIXED_BURST_VAL}}": str(fixed_burst),
        "{{FIXED_GANTT_SVG}}": render_svg_gantt(f_summary["gantt_chart"], sim_time),
        "{{VAR_GANTT_SVG}}": render_svg_gantt(v_summary["gantt_chart"], sim_time),
        "{{FIXED_TABLE_HTML}}": render_html_table(f_summary["all_processes"]),
        "{{VAR_TABLE_HTML}}": render_html_table(v_summary["all_processes"]),
    }

    for k, v in replacements.items():
        out_html = out_html.replace(k, v)

    out_file = Path(__file__).parent / "simulation_results.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(out_html)

    return out_file


def generate_and_open():
    out_path = generate_html_report()
    print(f"Report generated at: {out_path}")
    webbrowser.open(out_path.as_uri())


if __name__ == "__main__":
    if "--serve" in sys.argv:
        p = generate_html_report()
        os.chdir(p.parent)
        print("Serving dashboard at http://localhost:8080 ...")
        server = HTTPServer(("localhost", 8080), SimpleHTTPRequestHandler)
        webbrowser.open("http://localhost:8080/simulation_results.html")
        server.serve_forever()
    else:
        generate_and_open()
