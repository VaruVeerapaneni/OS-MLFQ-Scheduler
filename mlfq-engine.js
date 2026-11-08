// ==========================================================================
// UNIX MLFQ Engine & Visualization Module
// Problem #21: Round Robin Time Slicing (Q=3) with Multilevel Feedback
// ==========================================================================

class PRNG {
    constructor(seed) { 
        this.m = 0x80000000; 
        this.a = 1103515245; 
        this.c = 12345; 
        this.state = seed ? seed : Math.floor(Math.random() * (this.m - 1)); 
    }
    nextInt(min, max) { 
        this.state = (this.a * this.state + this.c) % this.m; 
        return min + Math.floor((this.state / this.m) * (max - min + 1)); 
    }
}

const PID_PALETTE = [
    "#6366f1", "#06b6d4", "#10b981", "#f59e0b", 
    "#ec4899", "#8b5cf6", "#14b8a6", "#f43f5e", 
    "#eab308", "#3b82f6", "#84cc16", "#a855f7"
];

function simulateMLFQ(workload, timeSlice = 3, maxTime = 60, numQueues = 3) {
    const procs = workload.map(p => ({
        pid: p.pid, arrival: p.arrival, burst: p.burst, remaining: p.burst,
        queue: 0, state: "NEW", startTime: null, completionTime: null,
        tat: null, wt: 0, rt: null, sliceSpent: 0
    }));

    const arrivals = [...procs].sort((a, b) => a.arrival - b.arrival);
    const queues = Array.from({ length: numQueues }, () => []);
    const gantt = [];
    const completed = [];
    const ticksHistory = [];

    let curTime = 0;
    let running = null;
    let sliceRemaining = 0;
    let busyTime = 0;
    let idleTime = 0;

    while (curTime < maxTime) {
        // 1. Process Arrivals
        while (arrivals.length > 0 && arrivals[0].arrival <= curTime) {
            const arriving = arrivals.shift();
            arriving.state = "READY";
            arriving.queue = 0;
            arriving.sliceSpent = 0;
            queues[0].push(arriving);
        }

        // 2. Higher-Priority Preemption Check
        if (running) {
            let higherReady = false;
            for (let q = 0; q < running.queue; q++) {
                if (queues[q].length > 0) { higherReady = true; break; }
            }
            if (higherReady) {
                running.state = "READY";
                queues[running.queue].unshift(running);
                running = null;
                sliceRemaining = 0;
            }
        }

        // 3. Dispatch from highest-priority non-empty queue
        if (!running) {
            for (let q = 0; q < numQueues; q++) {
                if (queues[q].length > 0) {
                    running = queues[q].shift();
                    sliceRemaining = timeSlice;
                    break;
                }
            }
        }

        // 4. Record Snapshot for step animation
        ticksHistory.push({
            t: curTime,
            runningPid: running ? `${running.pid} (Q${running.queue}, Rem:${running.remaining})` : "IDLE",
            sliceLeft: sliceRemaining,
            q0: queues[0].map(p => `${p.pid} (${p.remaining})`),
            q1: queues[1].map(p => `${p.pid} (${p.remaining})`),
            q2: queues[2].map(p => `${p.pid} (${p.remaining})`)
        });

        // 5. Execute 1 time unit
        if (running) {
            if (running.startTime === null) {
                running.startTime = curTime;
                running.rt = curTime - running.arrival;
            }

            if (gantt.length > 0 && gantt[gantt.length - 1].pid === running.pid && gantt[gantt.length - 1].queue === running.queue && gantt[gantt.length - 1].end === curTime) {
                gantt[gantt.length - 1].end = curTime + 1;
            } else {
                gantt.push({ pid: running.pid, queue: running.queue, start: curTime, end: curTime + 1 });
            }

            running.remaining--;
            running.sliceSpent++;
            busyTime++;
            sliceRemaining--;
            curTime++;

            if (running.remaining === 0) {
                running.completionTime = curTime;
                running.state = "TERMINATED";
                running.tat = curTime - running.arrival;
                running.wt = running.tat - running.burst;
                completed.push(running);
                running = null;
                sliceRemaining = 0;
            } else if (sliceRemaining === 0) {
                if (running.queue < numQueues - 1) running.queue++;
                running.sliceSpent = 0;
                running.state = "READY";
                queues[running.queue].push(running);
                running = null;
            }
        } else {
            if (gantt.length > 0 && gantt[gantt.length - 1].pid === "IDLE" && gantt[gantt.length - 1].end === curTime) {
                gantt[gantt.length - 1].end = curTime + 1;
            } else {
                gantt.push({ pid: "IDLE", queue: -1, start: curTime, end: curTime + 1 });
            }
            idleTime++;
            curTime++;

            if (arrivals.length === 0 && queues.every(q => q.length === 0)) {
                const rem = maxTime - curTime;
                if (rem > 0) {
                    idleTime += rem;
                    if (gantt.length > 0 && gantt[gantt.length - 1].pid === "IDLE") gantt[gantt.length - 1].end = maxTime;
                    else gantt.push({ pid: "IDLE", queue: -1, start: curTime, end: maxTime });
                    curTime = maxTime;
                }
                break;
            }
        }
    }

    procs.forEach(p => {
        if (p.remaining > 0 && curTime >= p.arrival) {
            p.wt = Math.max(0, (curTime - p.arrival) - (p.burst - p.remaining));
        }
    });

    const doneCount = completed.length;
    const awt = doneCount > 0 ? (completed.reduce((a, b) => a + b.wt, 0) / doneCount).toFixed(2) : "0.00";
    const att = doneCount > 0 ? (completed.reduce((a, b) => a + b.tat, 0) / doneCount).toFixed(2) : "0.00";
    const art = doneCount > 0 ? (completed.reduce((a, b) => a + (b.rt || 0), 0) / doneCount).toFixed(2) : "0.00";
    const cpu = ((busyTime / Math.max(1, curTime)) * 100).toFixed(1);
    const tp = (doneCount / Math.max(1, curTime)).toFixed(4);

    return { procs, completed, gantt, awt, att, art, cpu, tp, doneCount, total: procs.length, ticksHistory, queues };
}

function renderGanttSVG(segments, maxTime) {
    const totalTime = Math.max(maxTime, segments.length > 0 ? segments[segments.length - 1].end : 1);
    const viewWidth = 1100;
    const barY = 16, barH = 38, axisY = 66;
    const plotW = viewWidth - 40;
    const scale = plotW / totalTime;

    let svg = `<svg class="gantt-svg" viewBox="0 0 ${viewWidth} 90" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<line x1="20" y1="${axisY}" x2="${viewWidth - 20}" y2="${axisY}" stroke="rgba(255,255,255,0.18)" stroke-width="1.5" />`;

    segments.forEach(seg => {
        const x1 = 20 + (seg.start * scale);
        const x2 = 20 + (seg.end * scale);
        const w = Math.max(1, x2 - x1);

        let color = "rgba(100, 116, 139, 0.3)", textCol = "#94a3b8", label = "IDLE";
        if (seg.pid !== "IDLE") {
            const pNum = parseInt(seg.pid.replace(/[^0-9]/g, "")) || 1;
            color = PID_PALETTE[(pNum - 1) % PID_PALETTE.length];
            textCol = "#ffffff";
            label = `${seg.pid} (Q${seg.queue})`;
        }

        svg += `<rect x="${x1.toFixed(1)}" y="${barY}" width="${w.toFixed(1)}" height="${barH}" fill="${color}" stroke="#0f172a" stroke-width="1.5" rx="6"><title>${seg.pid} | Queue: Q${seg.queue} | Range: [${seg.start} - ${seg.end}] | Duration: ${seg.end - seg.start}u</title></rect>`;
        if (w > 36) svg += `<text x="${((x1 + x2)/2).toFixed(1)}" y="${barY + 23}" fill="${textCol}" font-size="11" font-weight="700" text-anchor="middle" pointer-events="none">${label}</text>`;
        else if (w > 18) svg += `<text x="${((x1 + x2)/2).toFixed(1)}" y="${barY + 23}" fill="${textCol}" font-size="9" text-anchor="middle" pointer-events="none">${seg.pid}</text>`;

        svg += `<line x1="${x1.toFixed(1)}" y1="${axisY - 3}" x2="${x1.toFixed(1)}" y2="${axisY + 3}" stroke="rgba(255,255,255,0.3)"/>`;
        svg += `<text x="${x1.toFixed(1)}" y="${axisY + 14}" font-size="9" fill="#94a3b8" text-anchor="middle" font-family="'JetBrains Mono', monospace">${seg.start}</text>`;
    });

    const lastX = 20 + (totalTime * scale);
    svg += `<line x1="${lastX.toFixed(1)}" y1="${axisY - 3}" x2="${lastX.toFixed(1)}" y2="${axisY + 3}" stroke="rgba(255,255,255,0.3)"/>`;
    svg += `<text x="${lastX.toFixed(1)}" y="${axisY + 14}" font-size="9" fill="#94a3b8" text-anchor="middle" font-family="'JetBrains Mono', monospace">${totalTime}</text>`;
    svg += `</svg>`;
    return svg;
}

function exportProcsCSV(procs, filename = "mlfq_simulation_metrics.csv") {
    let csv = "PID,Arrival,Burst,Remaining,Queue,State,Completion,TAT,WT,RT\n";
    procs.forEach(p => {
        csv += `${p.pid},${p.arrival},${p.burst},${p.remaining},Q${p.queue},${p.state},${p.completionTime !== null ? p.completionTime : "N/A"},${p.tat !== null ? p.tat : "N/A"},${p.wt},${p.rt !== null ? p.rt : "N/A"}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
}
