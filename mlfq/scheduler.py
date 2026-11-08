"""
Multilevel Feedback Queue (MLFQ) Scheduler with Round Robin Time Slicing.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from .pcb import ProcessControlBlock, ProcessState


class GanttSegment:
    """Represents a segment of CPU execution for Gantt chart generation."""
    def __init__(self, start_time: int, end_time: int, pid: str, queue_level: int):
        self.start_time: int = start_time
        self.end_time: int = end_time
        self.pid: str = pid
        self.queue_level: int = queue_level

    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start_time,
            "end": self.end_time,
            "pid": self.pid,
            "queue": self.queue_level,
            "duration": self.duration
        }

    def __repr__(self) -> str:
        return f"[{self.start_time}-{self.end_time}: {self.pid} (Q{self.queue_level})]"


class MLFQScheduler:
    """
    Simulates UNIX Round Robin Time Slicing with Multilevel Feedback Queues.
    """

    def __init__(
        self,
        time_slice: int = 3,
        num_queues: int = 3,
        max_simulation_time: int = 100,
        enable_preemption: bool = True
    ):
        """
        :param time_slice: Round Robin time quantum (default: 3 units).
        :param num_queues: Total number of priority queues (Q0=highest, Q(n-1)=lowest).
        :param max_simulation_time: Fixed amount of simulation time to run.
        :param enable_preemption: Higher priority queue arrival preempts lower queue.
        """
        self.time_slice: int = time_slice
        self.num_queues: int = num_queues
        self.max_simulation_time: int = max_simulation_time
        self.enable_preemption: bool = enable_preemption

        self.queues: List[deque] = [deque() for _ in range(num_queues)]
        self.all_processes: List[ProcessControlBlock] = []
        self.completed_processes: List[ProcessControlBlock] = []
        self.incomplete_processes: List[ProcessControlBlock] = []
        
        self.gantt_chart: List[GanttSegment] = []
        self.event_log: List[str] = []
        
        self.total_idle_time: int = 0
        self.total_busy_time: int = 0
        self.current_time: int = 0

    def _log(self, message: str) -> None:
        self.event_log.append(f"[T={self.current_time:03d}] {message}")

    def run(self, processes: List[ProcessControlBlock]) -> Dict[str, Any]:
        """
        Runs the simulation for a fixed amount of time (max_simulation_time).
        """
        self.all_processes = [p.clone() for p in processes]
        pending_arrivals = deque(sorted(self.all_processes, key=lambda p: (p.arrival_time, p.pid)))
        
        self.current_time = 0
        current_running: Optional[ProcessControlBlock] = None
        current_slice_remaining: int = 0
        
        self._log(f"Starting simulation. Max time: {self.max_simulation_time}, Time slice: {self.time_slice}, Queues: {self.num_queues}")

        while self.current_time < self.max_simulation_time:
            # 1. New arrivals at current_time
            while pending_arrivals and pending_arrivals[0].arrival_time <= self.current_time:
                arriving_proc = pending_arrivals.popleft()
                arriving_proc.state = ProcessState.READY
                arriving_proc.current_queue = 0
                arriving_proc.reset_slice()
                self.queues[0].append(arriving_proc)
                self._log(f"Process {arriving_proc.pid} arrived (Burst: {arriving_proc.burst_time}) -> Enqueued into Q0")

            # 2. Check for preemption if higher priority queue has ready processes
            if self.enable_preemption and current_running is not None:
                has_higher_priority = any(len(self.queues[q]) > 0 for q in range(current_running.current_queue))
                if has_higher_priority:
                    self._log(f"Process {current_running.pid} (Q{current_running.current_queue}) preempted by higher-priority queue")
                    current_running.state = ProcessState.READY
                    self.queues[current_running.current_queue].appendleft(current_running)
                    current_running = None
                    current_slice_remaining = 0

            # 3. If CPU is idle, dispatch from highest-priority non-empty queue
            if current_running is None:
                for q_idx in range(self.num_queues):
                    if self.queues[q_idx]:
                        current_running = self.queues[q_idx].popleft()
                        current_slice_remaining = self.time_slice
                        self._log(f"Dispatched {current_running.pid} from Q{q_idx} (Remaining burst: {current_running.remaining_time})")
                        break

            # 4. Execute 1 time unit
            if current_running is not None:
                # Append to Gantt chart
                if self.gantt_chart and self.gantt_chart[-1].pid == current_running.pid and self.gantt_chart[-1].queue_level == current_running.current_queue and self.gantt_chart[-1].end_time == self.current_time:
                    self.gantt_chart[-1].end_time = self.current_time + 1
                else:
                    self.gantt_chart.append(GanttSegment(self.current_time, self.current_time + 1, current_running.pid, current_running.current_queue))

                current_running.execute_slice(self.current_time, 1)
                self.total_busy_time += 1
                current_slice_remaining -= 1
                self.current_time += 1

                # Check process completion
                if current_running.is_completed:
                    current_running.mark_completed(self.current_time)
                    self.completed_processes.append(current_running)
                    self._log(f"Process {current_running.pid} COMPLETED at T={self.current_time} (TAT: {current_running.turnaround_time}, WT: {current_running.waiting_time})")
                    current_running = None
                    current_slice_remaining = 0
                elif current_slice_remaining == 0:
                    # Quantum expired -> Demote to next queue
                    old_q = current_running.current_queue
                    current_running.demote(self.current_time, self.num_queues - 1, reason=f"Slice {self.time_slice} Expired")
                    new_q = current_running.current_queue
                    self.queues[new_q].append(current_running)
                    self._log(f"Process {current_running.pid} time slice ({self.time_slice}) expired -> Demoted Q{old_q} to Q{new_q} (Rem: {current_running.remaining_time})")
                    current_running = None
            else:
                # CPU Idle
                if self.gantt_chart and self.gantt_chart[-1].pid == "IDLE" and self.gantt_chart[-1].end_time == self.current_time:
                    self.gantt_chart[-1].end_time = self.current_time + 1
                else:
                    self.gantt_chart.append(GanttSegment(self.current_time, self.current_time + 1, "IDLE", -1))
                
                self.total_idle_time += 1
                self.current_time += 1

                # If all done and no arrivals pending
                if not pending_arrivals and all(len(q) == 0 for q in self.queues):
                    self._log("All queues empty and no pending arrivals.")
                    rem_idle = self.max_simulation_time - self.current_time
                    if rem_idle > 0:
                        self.total_idle_time += rem_idle
                        if self.gantt_chart and self.gantt_chart[-1].pid == "IDLE":
                            self.gantt_chart[-1].end_time = self.max_simulation_time
                        else:
                            self.gantt_chart.append(GanttSegment(self.current_time, self.max_simulation_time, "IDLE", -1))
                        self.current_time = self.max_simulation_time
                    break

        if current_running is not None and not current_running.is_completed:
            self.queues[current_running.current_queue].appendleft(current_running)

        completed_pids = {p.pid for p in self.completed_processes}
        for p in self.all_processes:
            if p.pid not in completed_pids:
                p.compute_interim_metrics(self.max_simulation_time)
                self.incomplete_processes.append(p)

        self._log(f"Simulation concluded at T={self.current_time}. Completed: {len(self.completed_processes)}, Incomplete: {len(self.incomplete_processes)}")
        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Calculates statistical performance summary."""
        completed_count = len(self.completed_processes)
        
        if completed_count > 0:
            avg_waiting_time = sum(p.waiting_time for p in self.completed_processes) / completed_count
            avg_turnaround_time = sum(p.turnaround_time for p in self.completed_processes) / completed_count
            avg_response_time = sum(p.response_time for p in self.completed_processes if p.response_time is not None) / completed_count
        else:
            avg_waiting_time = 0.0
            avg_turnaround_time = 0.0
            avg_response_time = 0.0

        sim_duration = max(1, self.current_time)
        cpu_utilization = (self.total_busy_time / sim_duration) * 100.0
        throughput = completed_count / sim_duration

        return {
            "simulation_time": self.current_time,
            "max_simulation_time": self.max_simulation_time,
            "time_slice": self.time_slice,
            "num_queues": self.num_queues,
            "total_processes": len(self.all_processes),
            "completed_count": completed_count,
            "incomplete_count": len(self.incomplete_processes),
            "avg_waiting_time": round(avg_waiting_time, 2),
            "avg_turnaround_time": round(avg_turnaround_time, 2),
            "avg_response_time": round(avg_response_time, 2),
            "cpu_utilization": round(cpu_utilization, 2),
            "total_busy_time": self.total_busy_time,
            "total_idle_time": self.total_idle_time,
            "throughput": round(throughput, 4),
            "completed_processes": self.completed_processes,
            "incomplete_processes": self.incomplete_processes,
            "all_processes": self.all_processes,
            "gantt_chart": self.gantt_chart,
            "event_log": self.event_log
        }
