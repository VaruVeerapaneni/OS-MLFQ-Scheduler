"""
Process Workload Generator for UNIX MLFQ Simulation.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import random
from typing import List, Tuple, Optional
from .pcb import ProcessControlBlock


def generate_processes(
    count: int = 8,
    mode: str = "fixed",
    fixed_burst: int = 6,
    min_burst: int = 2,
    max_burst: int = 14,
    max_arrival_time: int = 20,
    seed: Optional[int] = None
) -> List[ProcessControlBlock]:
    """
    Generates a list of Process Control Blocks (PCBs) with random arrival times.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    processes: List[ProcessControlBlock] = []
    
    arrivals = [0] + [rng.randint(0, max_arrival_time) for _ in range(count - 1)]
    arrivals.sort()

    for i in range(count):
        pid = f"P{i+1}"
        arrival = arrivals[i]
        
        if mode == "fixed":
            burst = fixed_burst
        elif mode == "variable":
            burst = rng.randint(min_burst, max_burst)
        else:
            raise ValueError(f"Unknown burst mode '{mode}'. Choose 'fixed' or 'variable'.")

        processes.append(ProcessControlBlock(pid=pid, arrival_time=arrival, burst_time=burst))

    return processes


def generate_comparative_workload(
    count: int = 8,
    fixed_burst: int = 6,
    min_burst: int = 2,
    max_burst: int = 14,
    max_arrival_time: int = 20,
    seed: Optional[int] = 42
) -> Tuple[List[ProcessControlBlock], List[ProcessControlBlock]]:
    """
    Generates matched workloads with identical arrival times and PIDs:
    one with fixed burst times and one with variable burst times.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    arrivals = [0] + [rng.randint(0, max_arrival_time) for _ in range(count - 1)]
    arrivals.sort()

    fixed_procs = []
    var_procs = []

    for i in range(count):
        pid = f"P{i+1}"
        arrival = arrivals[i]
        v_burst = rng.randint(min_burst, max_burst)

        fixed_procs.append(ProcessControlBlock(pid=pid, arrival_time=arrival, burst_time=fixed_burst))
        var_procs.append(ProcessControlBlock(pid=pid, arrival_time=arrival, burst_time=v_burst))

    return fixed_procs, var_procs
