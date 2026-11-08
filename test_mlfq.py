"""
Unit Test Suite for UNIX Round Robin MLFQ Scheduler.
Group 7: Round Robin Time Slicing with Multilevel Feedback.
"""

import unittest
from mlfq.pcb import ProcessControlBlock, ProcessState
from mlfq.scheduler import MLFQScheduler
from mlfq.generator import generate_processes, generate_comparative_workload


class TestMLFQ(unittest.TestCase):

    def test_pcb_basic_operations(self):
        pcb = ProcessControlBlock(pid="P1", arrival_time=0, burst_time=7)
        self.assertEqual(pcb.remaining_time, 7)
        self.assertEqual(pcb.current_queue, 0)
        self.assertFalse(pcb.is_completed)

        executed = pcb.execute_slice(0, 3)
        self.assertEqual(executed, 3)
        self.assertEqual(pcb.remaining_time, 4)
        self.assertEqual(pcb.start_time, 0)
        self.assertEqual(pcb.response_time, 0)

        pcb.demote(current_time=3, max_queue=2)
        self.assertEqual(pcb.current_queue, 1)

    def test_scheduler_quantum_and_demotion(self):
        """
        Verify that a single process with burst=7 is sliced into:
        T=0..3 in Q0 (demoted to Q1),
        T=3..6 in Q1 (demoted to Q2),
        T=6..7 in Q2 (completed).
        """
        scheduler = MLFQScheduler(time_slice=3, num_queues=3, max_simulation_time=20)
        p = ProcessControlBlock(pid="P1", arrival_time=0, burst_time=7)
        summary = scheduler.run([p])

        self.assertEqual(summary["completed_count"], 1)
        completed_p = summary["completed_processes"][0]
        self.assertEqual(completed_p.completion_time, 7)
        self.assertEqual(completed_p.turnaround_time, 7)
        self.assertEqual(completed_p.waiting_time, 0)
        self.assertEqual(completed_p.current_queue, 2)

        gantt = summary["gantt_chart"]
        busy_segments = [s for s in gantt if s.pid != "IDLE"]
        self.assertEqual(len(busy_segments), 3)
        self.assertEqual(busy_segments[0].queue_level, 0)
        self.assertEqual(busy_segments[0].duration, 3)
        self.assertEqual(busy_segments[1].queue_level, 1)
        self.assertEqual(busy_segments[1].duration, 3)
        self.assertEqual(busy_segments[2].queue_level, 2)
        self.assertEqual(busy_segments[2].duration, 1)

    def test_two_processes_round_robin(self):
        """
        Two processes arrive at T=0, each with burst=6.
        Time slice = 3.
        T=0..3: P1 in Q0 (rem=3) -> demoted to Q1
        T=3..6: P2 in Q0 (rem=3) -> demoted to Q1
        T=6..9: P1 in Q1 (rem=0) -> finishes at 9!
        T=9..12: P2 in Q1 (rem=0) -> finishes at 12!
        """
        scheduler = MLFQScheduler(time_slice=3, num_queues=3, max_simulation_time=30)
        p1 = ProcessControlBlock("P1", arrival_time=0, burst_time=6)
        p2 = ProcessControlBlock("P2", arrival_time=0, burst_time=6)
        summary = scheduler.run([p1, p2])

        self.assertEqual(summary["completed_count"], 2)
        p_dict = {p.pid: p for p in summary["completed_processes"]}
        
        self.assertEqual(p_dict["P1"].completion_time, 9)
        self.assertEqual(p_dict["P1"].turnaround_time, 9)
        self.assertEqual(p_dict["P1"].waiting_time, 3)

        self.assertEqual(p_dict["P2"].completion_time, 12)
        self.assertEqual(p_dict["P2"].turnaround_time, 12)
        self.assertEqual(p_dict["P2"].waiting_time, 6)

        self.assertAlmostEqual(summary["avg_waiting_time"], 4.5)
        self.assertAlmostEqual(summary["avg_turnaround_time"], 10.5)

    def test_fixed_simulation_time_limit(self):
        scheduler = MLFQScheduler(time_slice=3, num_queues=3, max_simulation_time=10)
        p = ProcessControlBlock("P1", arrival_time=0, burst_time=20)
        summary = scheduler.run([p])

        self.assertEqual(summary["completed_count"], 0)
        self.assertEqual(summary["incomplete_count"], 1)
        self.assertEqual(summary["simulation_time"], 10)
        self.assertEqual(summary["incomplete_processes"][0].remaining_time, 10)

    def test_workload_generators(self):
        fixed_procs = generate_processes(count=5, mode="fixed", fixed_burst=6, seed=123)
        self.assertEqual(len(fixed_procs), 5)
        for p in fixed_procs:
            self.assertEqual(p.burst_time, 6)

        var_procs = generate_processes(count=5, mode="variable", min_burst=3, max_burst=10, seed=123)
        self.assertEqual(len(var_procs), 5)
        for p in var_procs:
            self.assertTrue(3 <= p.burst_time <= 10)

        f_set, v_set = generate_comparative_workload(count=6, fixed_burst=6, min_burst=2, max_burst=12, seed=99)
        for f, v in zip(f_set, v_set):
            self.assertEqual(f.arrival_time, v.arrival_time)
            self.assertEqual(f.pid, v.pid)
            self.assertEqual(f.burst_time, 6)


if __name__ == "__main__":
    unittest.main()
