"""
Metrics and Reporting Module for UNIX MLFQ Simulation.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

from typing import Dict, Any, List


def format_process_table(processes: List[Any], title: str = "Process Execution Summary") -> str:
    """Formats process execution records into an aligned table."""
    headers = ["PID", "Arrival", "Burst", "Remaining", "Final Q", "State", "Finish", "TAT", "WT", "RT"]
    row_fmt = "{:<5} {:>7} {:>7} {:>9} {:>8} {:<11} {:>6} {:>6} {:>6} {:>6}"
    
    lines = [
        "=" * 75,
        f" {title}",
        "=" * 75,
        row_fmt.format(*headers),
        "-" * 75
    ]

    for p in sorted(processes, key=lambda x: int(x.pid.replace("P", "")) if x.pid.replace("P", "").isdigit() else x.pid):
        finish_str = str(p.completion_time) if p.completion_time is not None else "N/A"
        tat_str = str(p.turnaround_time) if p.turnaround_time is not None else "N/A"
        wt_str = str(p.waiting_time)
        rt_str = str(p.response_time) if p.response_time is not None else "N/A"

        lines.append(row_fmt.format(
            p.pid,
            p.arrival_time,
            p.burst_time,
            p.remaining_time,
            f"Q{p.current_queue}",
            p.state.value,
            finish_str,
            tat_str,
            wt_str,
            rt_str
        ))
    
    lines.append("=" * 75)
    return "\n".join(lines)


def render_ascii_gantt(gantt_segments: List[Any], max_width: int = 80) -> str:
    """Renders a visual ASCII Gantt chart of the CPU schedule."""
    if not gantt_segments:
        return "[Empty Gantt Chart]"

    total_time = gantt_segments[-1].end_time
    if total_time == 0:
        return "[Duration: 0]"

    bar_str = "|"
    time_str = "0"
    
    for seg in gantt_segments:
        seg_label = f" {seg.pid} "
        if seg.queue_level >= 0:
            seg_label = f" {seg.pid}(Q{seg.queue_level}) "
        
        block_len = max(len(seg_label), int(seg.duration * 2))
        padded_label = seg_label.center(block_len)
        bar_str += padded_label + "|"
        time_str += str(seg.end_time).rjust(len(padded_label) + 1)

    return f"Gantt Chart Timeline (Total Time: {total_time}):\n{bar_str}\n{time_str}"


def format_comparison_summary(fixed_summary: Dict[str, Any], var_summary: Dict[str, Any]) -> str:
    """Formats a side-by-side comparative table for Fixed vs Variable burst times."""
    lines = [
        "*" * 75,
        "   COMPARATIVE ANALYSIS: FIXED BURST vs VARIABLE (RANDOMIZED) BURST",
        "*" * 75,
        "{:<35} | {:<16} | {:<16}".format("Performance Metric", "Fixed Burst", "Variable Burst"),
        "-" * 75,
        "{:<35} | {:<16} | {:<16}".format("Total Processes Generated", fixed_summary['total_processes'], var_summary['total_processes']),
        "{:<35} | {:<16} | {:<16}".format("Completed Processes", fixed_summary['completed_count'], var_summary['completed_count']),
        "{:<35} | {:<16} | {:<16}".format("Incomplete / In-Flight", fixed_summary['incomplete_count'], var_summary['incomplete_count']),
        "{:<35} | {:<16} | {:<16}".format("Simulation Time Limit (units)", fixed_summary['max_simulation_time'], var_summary['max_simulation_time']),
        "{:<35} | {:<16} | {:<16}".format("Round Robin Time Slice (Q)", fixed_summary['time_slice'], var_summary['time_slice']),
        "{:<35} | {:<16} | {:<16}".format("Average Waiting Time (AWT)", f"{fixed_summary['avg_waiting_time']} units", f"{var_summary['avg_waiting_time']} units"),
        "{:<35} | {:<16} | {:<16}".format("Average Turnaround Time (ATT)", f"{fixed_summary['avg_turnaround_time']} units", f"{var_summary['avg_turnaround_time']} units"),
        "{:<35} | {:<16} | {:<16}".format("Average Response Time (ART)", f"{fixed_summary['avg_response_time']} units", f"{var_summary['avg_response_time']} units"),
        "{:<35} | {:<16} | {:<16}".format("CPU Utilization (%)", f"{fixed_summary['cpu_utilization']}%", f"{var_summary['cpu_utilization']}%"),
        "{:<35} | {:<16} | {:<16}".format("Total Busy Time (units)", fixed_summary['total_busy_time'], var_summary['total_busy_time']),
        "{:<35} | {:<16} | {:<16}".format("Total Idle Time (units)", fixed_summary['total_idle_time'], var_summary['total_idle_time']),
        "{:<35} | {:<16} | {:<16}".format("Throughput (processes/unit)", fixed_summary['throughput'], var_summary['throughput']),
        "*" * 75,
    ]
    return "\n".join(lines)


def calculate_metrics(summary: Dict[str, Any]) -> Dict[str, Any]:
    return summary


def compare_results(fixed: Dict[str, Any], var: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "fixed": fixed,
        "variable": var
    }
