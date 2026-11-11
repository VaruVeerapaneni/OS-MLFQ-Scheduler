# Round Robin Time Slicing with Multilevel Feedback (MLFQ)

**Operating Systems Course Project**  
**Group Number:** 7

[![Live Web Simulator](https://img.shields.io/badge/Live_Simulator-varuveerapaneni.github.io%2FRound--Robin--MLFQ-22c55e?style=for-the-badge&logo=googlechrome&logoColor=white)](https://varuveerapaneni.github.io/Round-Robin-MLFQ/)
[![GitHub Actions CI](https://img.shields.io/badge/CI_Simulation-Passed_100%25-38bdf8?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/VaruVeerapaneni/Round-Robin-MLFQ/actions)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Deployed-a855f7?style=for-the-badge&logo=github&logoColor=white)](https://varuveerapaneni.github.io/Round-Robin-MLFQ/)

> 🌐 **Live Web Application URL:** [https://varuveerapaneni.github.io/Round-Robin-MLFQ/](https://varuveerapaneni.github.io/Round-Robin-MLFQ/)  

---

## 👥 Group Members

| Reg. Number | Student Name | Role / Contribution |
|---|---|---|
| **AP24110010509** | **VEERAPANENI VARALAKSHMI** | PCB Design & Queue Scheduling Logic |
| **AP24110010538** | **GANDHAM SAI POOJITHA** | Workload Generator & Statistical Metrics Engine |
| **AP24110012001** | **KANDIMALLA KEERTHI SREE** | Tkinter Desktop Visualizer & Canvas Gantt Chart |
| **AP24110011723** | **ARADHYA SINGH** | Web Dashboard & Comparative Analysis Documentation |

---

## 📋 Problem Statement & Objective

> **Problem Statement 21:**  
> *"UNIX operating system uses Round robin Time slicing with multilevel feedback for process scheduling. Assume that the processes (PCB's) arrive at random. Assume the time slice is 3 units. Simulate Round robin time slicing with fixed and variable (Randomized) burst times. Run the processes for fixed amount of time and find the average waiting time, average turn-around time of the processes completed."*

### Key Requirements Fulfilled:
- **Round Robin Time Slicing:** Exact time quantum of **3 units** ($Q = 3$).
- **Process Control Blocks (PCBs):** Complete representation including PID, Arrival Time, Burst Time, Remaining Time, Priority Queue Level, State, Timestamps, and Interval Logs.
- **Flexible Process Count:** Starts with six example PCBs (P1–P6), but users can increase or decrease the process count; the simulator supports arbitrary positive process counts.
- **Random Arrival Times:** Every generated process receives a randomized arrival timestamp; both comparison modes reuse the same arrival times.
- **Dual Burst Modes:**
  1. **Fixed Burst Times:** All processes have identical CPU burst requirements (e.g., 6 units).
  2. **Variable (Randomized) Burst Times:** Processes have uniformly distributed CPU burst requirements (e.g., 2–14 units, generated independently for every process).
- **Fixed Total Simulation Time ($T_{sim}$):** Runs up to a fixed simulation time limit, evaluating completed processes and accounting for in-flight tasks.
- **Performance Evaluation:** Computes **Average Waiting Time (AWT)**, **Average Turnaround Time (ATT)**, Average Response Time (ART), CPU Utilization, and Throughput.
- **Multiple Interfaces:**
  - **Interactive Terminal CLI** with formatted tables and ASCII Gantt charts.
  - **Tkinter Desktop GUI** with dynamic Canvas Gantt chart and side-by-side metric visualizer.
  - **Modern Web Dashboard** with SVG Gantt charts and KPI summary cards.

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+ (Tested on Python 3.13)
- **Zero external packages required!** The entire simulator, including GUI and Web generator, uses standard library Python (`tkinter`, `json`, `random`, `math`, `unittest`, `http.server`).

### Quick Start Commands

#### 1. Launch Interactive CLI Menu
```bash
python run_simulation.py
```
Or directly:
```bash
python cli.py
```

#### 2. Run Head-to-Head Comparative CLI Mode (Automated)
```bash
python cli.py --compare --sim-time 60 --processes 6
```

#### 3. Launch Desktop GUI (Tkinter)
```bash
python run_simulation.py --gui
```
Or:
```bash
python gui.py
```

#### 4. Generate & View Interactive Web Dashboard
```bash
python run_simulation.py --web
```
Or:
```bash
python web_dashboard.py
```
*(Generates `simulation_results.html` and automatically opens it in your default web browser.)*

#### 5. Run Automated Unit Tests
```bash
python -m unittest test_mlfq.py
```

---

## 📁 Project Architecture

```
os_mlfq_simulator/
├── mlfq/
│   ├── __init__.py           # Package declarations
│   ├── pcb.py                # Process Control Block & ProcessState definitions
│   ├── scheduler.py          # MLFQ Scheduler with Round Robin (Q=3) & demotion
│   ├── generator.py          # Random arrival & matched workload generators
│   └── metrics.py            # AWT, ATT, CPU utilization & ASCII Gantt chart
├── cli.py                    # Terminal interface with formatted tables
├── gui.py                    # Interactive Desktop GUI (Tkinter Canvas)
├── web_dashboard.py          # Offline HTML5/SVG interactive dashboard generator
├── run_simulation.py         # Unified application runner
├── test_mlfq.py              # Comprehensive unit test suite
├── simulation_results.html   # Generated web report
├── README.md                 # User manual
└── PROJECT_REPORT.md         # Formal academic report
```

---

## 🔬 Algorithm Summary

1. **Queue Architecture:**
   - $Q_0$ (Highest Priority): Round Robin with Quantum = 3.
   - $Q_1$ (Medium Priority): Round Robin with Quantum = 3.
   - $Q_2$ (Lowest Priority): Round Robin with Quantum = 3.
2. **Process Arrival:**
   - Processes arrive at random times $t$ and immediately enter $Q_0$.
3. **Execution & Demotion:**
   - CPU always schedules from the highest-priority non-empty queue ($Q_0 \to Q_1 \to Q_2$).
   - A process executes for up to 3 units.
   - If it completes, it enters `TERMINATED` state and records completion time.
   - If it consumes the full 3 units without completing, it is preempted and **demoted** to $Q_{i+1}$.
4. **Simulation Termination:**
   - Simulation stops at $t = T_{\text{sim}}$.
   - Metrics are computed for all completed processes:

```text
Turnaround Time (TAT) = Completion Time - Arrival Time
Waiting Time (WT)    = Turnaround Time - Burst Time
Average Waiting Time = (Sum of WT) / Number of Completed Processes
Average Turnaround   = (Sum of TAT) / Number of Completed Processes
```

$$\text{TAT} = \text{Completion Time} - \text{Arrival Time}$$

$$\text{WT} = \text{TAT} - \text{Burst Time}$$

$$\text{AWT} = \frac{1}{N_{\text{completed}}} \sum_{i=1}^{N_{\text{completed}}} \text{WT}_i$$

$$\text{ATT} = \frac{1}{N_{\text{completed}}} \sum_{i=1}^{N_{\text{completed}}} \text{TAT}_i$$
