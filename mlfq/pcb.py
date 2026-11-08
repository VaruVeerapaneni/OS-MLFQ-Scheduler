"""
Process Control Block (PCB) Module for UNIX MLFQ Scheduling Simulation.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

from enum import Enum
from typing import Optional, List, Tuple, Dict, Any


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    TERMINATED = "TERMINATED"


class ProcessControlBlock:
    """
    Represents the Process Control Block (PCB) of a simulated UNIX process.
    Contains all vital tracking information needed by the operating system scheduler.
    """

    def __init__(self, pid: str, arrival_time: int, burst_time: int, initial_queue: int = 0):
        self.pid: str = pid
        self.arrival_time: int = arrival_time
        self.burst_time: int = burst_time
        self.remaining_time: int = burst_time
        self.current_queue: int = initial_queue
        
        # Process State
        self.state: ProcessState = ProcessState.NEW
        
        # Timing Metrics
        self.start_time: Optional[int] = None       # First time process acquires CPU
        self.completion_time: Optional[int] = None  # Time when process completes all execution
        self.waiting_time: int = 0                  # Accumulated waiting time
        self.turnaround_time: Optional[int] = None  # completion_time - arrival_time
        self.response_time: Optional[int] = None    # start_time - arrival_time
        
        # Time slice consumption tracking
        self.time_spent_in_current_slice: int = 0
        
        # Detailed interval logs: (start_time, end_time, queue_level)
        self.execution_intervals: List[Tuple[int, int, int]] = []
        
        # History of transitions: (timestamp, old_queue, new_queue, reason)
        self.queue_transitions: List[Tuple[int, int, int, str]] = []

    @property
    def is_completed(self) -> bool:
        """Returns True if the process has executed all of its burst time."""
        return self.remaining_time <= 0

    def record_start(self, current_time: int) -> None:
        """Records initial CPU acquisition time for Response Time calculation."""
        if self.start_time is None:
            self.start_time = current_time
            self.response_time = current_time - self.arrival_time

    def execute_slice(self, current_time: int, duration: int) -> int:
        """Executes up to duration units, updating remaining time and intervals."""
        self.record_start(current_time)
        actual_duration = min(duration, self.remaining_time)
        self.remaining_time -= actual_duration
        self.time_spent_in_current_slice += actual_duration
        self.execution_intervals.append((current_time, current_time + actual_duration, self.current_queue))
        self.state = ProcessState.RUNNING
        return actual_duration

    def demote(self, current_time: int, max_queue: int, reason: str = "Quantum Expired") -> None:
        """Demotes the process to the next lower priority queue."""
        old_q = self.current_queue
        if self.current_queue < max_queue:
            self.current_queue += 1
        self.time_spent_in_current_slice = 0
        self.state = ProcessState.READY
        self.queue_transitions.append((current_time, old_q, self.current_queue, reason))

    def reset_slice(self) -> None:
        """Resets the quantum counter for current queue."""
        self.time_spent_in_current_slice = 0

    def mark_completed(self, current_time: int) -> None:
        """Marks process TERMINATED and computes Turnaround and Waiting times."""
        self.completion_time = current_time
        self.state = ProcessState.TERMINATED
        self.turnaround_time = self.completion_time - self.arrival_time
        self.waiting_time = self.turnaround_time - self.burst_time

    def compute_interim_metrics(self, current_time: int) -> None:
        """Computes partial metrics for in-flight processes when simulation time ends."""
        if not self.is_completed:
            if current_time >= self.arrival_time:
                time_in_system = current_time - self.arrival_time
                executed_time = self.burst_time - self.remaining_time
                self.waiting_time = max(0, time_in_system - executed_time)

    def clone(self) -> "ProcessControlBlock":
        """Creates an independent copy with fresh runtime state."""
        return ProcessControlBlock(
            pid=self.pid,
            arrival_time=self.arrival_time,
            burst_time=self.burst_time,
            initial_queue=0
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serializes PCB to dictionary for JSON or UI reporting."""
        return {
            "pid": self.pid,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "remaining_time": self.remaining_time,
            "current_queue": self.current_queue,
            "state": self.state.value,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
            "completed": self.is_completed,
            "intervals": self.execution_intervals
        }

    def __repr__(self) -> str:
        return (f"PCB(pid={self.pid}, arr={self.arrival_time}, burst={self.burst_time}, "
                f"rem={self.remaining_time}, Q={self.current_queue}, state={self.state.value})")
