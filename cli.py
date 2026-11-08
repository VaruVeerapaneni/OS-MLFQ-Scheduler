"""
Command-Line Interface (CLI) for UNIX MLFQ Scheduling Simulation.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import sys
import argparse
from mlfq.pcb import ProcessControlBlock
from mlfq.scheduler import MLFQScheduler
from mlfq.generator import generate_comparative_workload, generate_processes
from mlfq.metrics import (
    format_process_table,
    render_ascii_gantt,
    format_comparison_summary,
)


def print_banner():
    banner = """
===========================================================================
  UNIX PROCESS SCHEDULING SIMULATION
  Round Robin Time Slicing with Multilevel Feedback Queues (MLFQ)
---------------------------------------------------------------------------
  Course Project: Group 7
  Team Members:
    * AP24110010538 - GANDHAM SAI POOJITHA
    * AP24110010509 - VEERAPANENI VARALAKSHMI
    * AP24110012001 - KANDIMALLA KEERTHI SREE
    * AP24110011723 - ARADHYA SINGH
===========================================================================
"""
    print(banner)


def run_comparative_simulation(
    num_procs: int = 8,
    sim_time: int = 60,
    time_slice: int = 3,
    fixed_burst: int = 6,
    min_burst: int = 2,
    max_burst: int = 14,
    seed: int = 42,
    show_logs: bool = False
):
    print(f"\n[*] Generating matched workloads (Processes: {num_procs}, Time Slice: {time_slice}, Max Time: {sim_time}, Seed: {seed})...")
    fixed_procs, var_procs = generate_comparative_workload(
        count=num_procs,
        fixed_burst=fixed_burst,
        min_burst=min_burst,
        max_burst=max_burst,
        max_arrival_time=20,
        seed=seed
    )

    # 1. Run Fixed Burst Simulation
    print("\n" + "=" * 75)
    print(" >>> 1. RUNNING FIXED BURST SIMULATION (Burst = {} for all processes)".format(fixed_burst))
    print("=" * 75)
    sched_fixed = MLFQScheduler(time_slice=time_slice, num_queues=3, max_simulation_time=sim_time)
    fixed_summary = sched_fixed.run(fixed_procs)

    if show_logs:
        print("\n--- Fixed Burst Execution Log ---")
        for log_line in fixed_summary["event_log"]:
            print(log_line)

    print("\n" + render_ascii_gantt(fixed_summary["gantt_chart"]))
    print("\n" + format_process_table(fixed_summary["all_processes"], title=f"Fixed Burst Results (Burst = {fixed_burst})"))
    print(f"Summary: Completed = {fixed_summary['completed_count']}/{num_procs} | AWT = {fixed_summary['avg_waiting_time']} | ATT = {fixed_summary['avg_turnaround_time']} | CPU Util = {fixed_summary['cpu_utilization']}%")

    # 2. Run Variable Burst Simulation
    print("\n" + "=" * 75)
    print(f" >>> 2. RUNNING VARIABLE (RANDOMIZED) BURST SIMULATION (Burst in [{min_burst}, {max_burst}])")
    print("=" * 75)
    sched_var = MLFQScheduler(time_slice=time_slice, num_queues=3, max_simulation_time=sim_time)
    var_summary = sched_var.run(var_procs)

    if show_logs:
        print("\n--- Variable Burst Execution Log ---")
        for log_line in var_summary["event_log"]:
            print(log_line)

    print("\n" + render_ascii_gantt(var_summary["gantt_chart"]))
    print("\n" + format_process_table(var_summary["all_processes"], title="Variable (Randomized) Burst Results"))
    print(f"Summary: Completed = {var_summary['completed_count']}/{num_procs} | AWT = {var_summary['avg_waiting_time']} | ATT = {var_summary['avg_turnaround_time']} | CPU Util = {var_summary['cpu_utilization']}%")

    # 3. Print Side-by-Side Comparison
    print("\n" + format_comparison_summary(fixed_summary, var_summary))
    
    # 4. Academic Insights
    print("\n" + "-" * 75)
    print(" ACADEMIC OBSERVATIONS & ANALYSIS:")
    print("  1. Round Robin Time Slicing (Q=3): Ensures interactive responsiveness.")
    print("     Short jobs finish quickly in Q0 without degrading to lower priority queues.")
    print("  2. Multilevel Feedback Demotion: CPU-bound processes consume their 3-unit quantum")
    print("     and automatically drop to Q1 then Q2, preventing starvation of short/I-O tasks.")
    print("  3. Fixed vs. Variable Comparison: In variable burst workloads, variance in execution")
    print("     times highlights MLFQ's strength in penalizing heavy tasks while keeping short tasks fast.")
    print("-" * 75 + "\n")

    return fixed_summary, var_summary


def interactive_menu():
    print_banner()
    while True:
        print("Select an option:")
        print(" [1] Run Comparative Simulation (Fixed vs Variable Burst)")
        print(" [2] Run Simulation with Custom Parameters")
        print(" [3] Run with Verbose Step-by-Step Execution Logs")
        print(" [4] Launch Desktop GUI")
        print(" [5] Generate and View HTML Web Dashboard")
        print(" [0] Exit")
        choice = input("\nEnter choice (0-5) [default 1]: ").strip()
        if not choice:
            choice = "1"

        if choice == "1":
            run_comparative_simulation()
        elif choice == "2":
            try:
                n = int(input("Number of processes [8]: ").strip() or "8")
                q = int(input("Round Robin Time slice [3]: ").strip() or "3")
                t = int(input("Fixed simulation time [60]: ").strip() or "60")
                fb = int(input("Fixed burst time [6]: ").strip() or "6")
                min_b = int(input("Variable min burst [2]: ").strip() or "2")
                max_b = int(input("Variable max burst [14]: ").strip() or "14")
                s = int(input("Random seed [42]: ").strip() or "42")
                run_comparative_simulation(num_procs=n, sim_time=t, time_slice=q, fixed_burst=fb, min_burst=min_b, max_burst=max_b, seed=s)
            except ValueError as e:
                print(f"[!] Invalid input: {e}")
        elif choice == "3":
            run_comparative_simulation(show_logs=True)
        elif choice == "4":
            print("[*] Launching Tkinter GUI...")
            try:
                import gui
                gui.launch_gui()
            except Exception as e:
                print(f"[!] Error launching GUI: {e}")
        elif choice == "5":
            print("[*] Generating HTML Web Dashboard...")
            try:
                import web_dashboard
                web_dashboard.generate_and_open()
            except Exception as e:
                print(f"[!] Error generating dashboard: {e}")
        elif choice == "0":
            print("Exiting. Thank you!")
            break
        else:
            print("[!] Invalid option. Try again.")


def main():
    parser = argparse.ArgumentParser(description="UNIX MLFQ Process Scheduling Simulation (Group 7)")
    parser.add_argument("--compare", action="store_true", help="Run comparative simulation between fixed and variable burst times")
    parser.add_argument("--processes", type=int, default=8, help="Number of processes (default: 8)")
    parser.add_argument("--sim-time", type=int, default=60, help="Fixed simulation time limit (default: 60)")
    parser.add_argument("--quantum", type=int, default=3, help="Round Robin time slice (default: 3)")
    parser.add_argument("--fixed-burst", type=int, default=6, help="Fixed burst time (default: 6)")
    parser.add_argument("--min-burst", type=int, default=2, help="Variable min burst time (default: 2)")
    parser.add_argument("--max-burst", type=int, default=14, help="Variable max burst time (default: 14)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--logs", action="store_true", help="Display verbose event execution logs")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive text menu")

    args = parser.parse_args()

    if len(sys.argv) == 1 or args.interactive:
        interactive_menu()
    else:
        print_banner()
        run_comparative_simulation(
            num_procs=args.processes,
            sim_time=args.sim_time,
            time_slice=args.quantum,
            fixed_burst=args.fixed_burst,
            min_burst=args.min_burst,
            max_burst=args.max_burst,
            seed=args.seed,
            show_logs=args.logs
        )


if __name__ == "__main__":
    main()
