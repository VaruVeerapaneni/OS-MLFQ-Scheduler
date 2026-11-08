// Pseudo-Random Number Generator for reproducible testing
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

let globalCustomProcs = [];
let animInterval = null;
let animCurrentTick = 0;
let isAnimating = false;
let latestFixedRes = null;
let latestVarRes = null;

function simulateMLFQEngine(workload, timeSlice, maxTime, numQueues = 3) {
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
        // Arrivals
        while (arrivals.length > 0 && arrivals[0].arrival <= curTime) {
            const arriving = arrivals.shift();
            arriving.state = "READY";
            arriving.queue = 0;
            arriving.sliceSpent = 0;
            queues[0].push(arriving);
        }

        // Preemption
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

        // Dispatch
        if (!running) {
            for (let q = 0; q < numQueues; q++) {
                if (queues[q].length > 0) {
                    running = queues[q].shift();
                    sliceRemaining = timeSlice;
                    break;
                }
            }
        }

        // Record Snapshot for step animation
        ticksHistory.push({
            t: curTime,
            runningPid: running ? `${running.pid} (Q${running.queue}, Rem:${running.remaining})` : "IDLE",
            sliceLeft: sliceRemaining,
            q0: queues[0].map(p => `${p.pid} (${p.remaining})`),
            q1: queues[1].map(p => `${p.pid} (${p.remaining})`),
            q2: queues[2].map(p => `${p.pid} (${p.remaining})`)
        });

        // Execution
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

function renderGantt(segments, maxTime) {
    const totalTime = Math.max(maxTime, segments.length > 0 ? segments[segments.length - 1].end : 1);
    const viewWidth = 1100;
    const barY = 16, barH = 38, axisY = 66;
    const plotW = viewWidth - 40;
    const scale = plotW / totalTime;

    let svg = `<svg class="gantt-svg" viewBox="0 0 ${viewWidth} 90" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<line x1="20" y1="${axisY}" x2="${viewWidth - 20}" y2="${axisY}" stroke="rgba(255,255,255,0.15)" stroke-width="1.5" />`;

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

        svg += `<rect x="${x1.toFixed(1)}" y="${barY}" width="${w.toFixed(1)}" height="${barH}" fill="${color}" stroke="#0f172a" stroke-width="1.5" rx="6"/>`;
        if (w > 36) svg += `<text x="${((x1 + x2)/2).toFixed(1)}" y="${barY + 23}" fill="${textCol}" font-size="11" font-weight="700" text-anchor="middle">${label}</text>`;
        else if (w > 18) svg += `<text x="${((x1 + x2)/2).toFixed(1)}" y="${barY + 23}" fill="${textCol}" font-size="9" text-anchor="middle">${seg.pid}</text>`;

        svg += `<line x1="${x1.toFixed(1)}" y1="${axisY - 3}" x2="${x1.toFixed(1)}" y2="${axisY + 3}" stroke="rgba(255,255,255,0.3)"/>`;
        svg += `<text x="${x1.toFixed(1)}" y="${axisY + 14}" font-size="9" fill="#94a3b8" text-anchor="middle" font-family="'JetBrains Mono', monospace">${seg.start}</text>`;
    });

    const lastX = 20 + (totalTime * scale);
    svg += `<line x1="${lastX.toFixed(1)}" y1="${axisY - 3}" x2="${lastX.toFixed(1)}" y2="${axisY + 3}" stroke="rgba(255,255,255,0.3)"/>`;
    svg += `<text x="${lastX.toFixed(1)}" y="${axisY + 14}" font-size="9" fill="#94a3b8" text-anchor="middle" font-family="'JetBrains Mono', monospace">${totalTime}</text>`;
    svg += `</svg>`;
    return svg;
}

function renderTable(tableId, procs) {
    const tableEl = document.getElementById(tableId);
    if (!tableEl) return;
    const tbody = tableEl.querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    procs.forEach(p => {
        const isDone = p.remaining === 0;
        const badgeCls = isDone ? "status-term" : "status-ready";
        const row = `<tr>
            <td style="color:#f8fafc; font-weight:700;">${p.pid}</td>
            <td>${p.arrival}</td>
            <td>${p.burst}</td>
            <td>${p.remaining}</td>
            <td><span class="badge-status status-run">Q${p.queue}</span></td>
            <td><span class="badge-status ${badgeCls}">${isDone ? 'TERMINATED' : 'READY'}</span></td>
            <td>${p.completionTime !== null ? p.completionTime : '-'}</td>
            <td style="color:var(--cyan); font-weight:700;">${p.tat !== null ? p.tat : '-'}</td>
            <td style="color:var(--emerald); font-weight:700;">${p.wt}</td>
            <td>${p.rt !== null ? p.rt : '-'}</td>
        </tr>`;
        tbody.innerHTML += row;
    });
}

function runInstantSimulator() {
    stopAnimation();

    const q = parseInt(document.getElementById("inpQuantum")?.value) || 3;
    const simTime = parseInt(document.getElementById("inpSimTime")?.value) || 60;
    const n = parseInt(document.getElementById("inpProcs")?.value) || 8;
    const fixedBurst = parseInt(document.getElementById("inpFixedBurst")?.value) || 6;
    const minBurst = parseInt(document.getElementById("inpMinBurst")?.value) || 2;
    const maxBurst = parseInt(document.getElementById("inpMaxBurst")?.value) || 14;
    const seed = parseInt(document.getElementById("inpSeed")?.value) || 42;

    const lblB = document.getElementById("lblFixedB");
    if (lblB) lblB.innerText = fixedBurst;

    const prng = new PRNG(seed);
    const arrivals = [0];
    for (let i = 1; i < n; i++) arrivals.push(prng.nextInt(0, 20));
    arrivals.sort((a, b) => a - b);

    const fixedWorkload = [];
    const varWorkload = [];
    for (let i = 0; i < n; i++) {
        const pid = `P${i + 1}`;
        const arr = arrivals[i];
        fixedWorkload.push({ pid, arrival: arr, burst: fixedBurst });
        varWorkload.push({ pid, arrival: arr, burst: prng.nextInt(minBurst, maxBurst) });
    }

    if (globalCustomProcs.length > 0) {
        globalCustomProcs.forEach(cp => {
            fixedWorkload.push({ ...cp });
            varWorkload.push({ ...cp });
        });
    }

    latestFixedRes = simulateMLFQEngine(fixedWorkload, q, simTime, 3);
    latestVarRes = simulateMLFQEngine(varWorkload, q, simTime, 3);

    // Update KPI Tiles
    const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    setTxt("valFixedAWT", `${latestFixedRes.awt}u`);
    setTxt("valVarAWT", `${latestVarRes.awt}u`);
    setTxt("valFixedATT", `${latestFixedRes.att}u`);
    setTxt("valVarATT", `${latestVarRes.att}u`);
    setTxt("valFixedDone", `${latestFixedRes.doneCount} / ${latestFixedRes.total}`);
    setTxt("valVarDone", `${latestVarRes.doneCount} / ${latestVarRes.total}`);
    setTxt("valFixedCPU", `${latestFixedRes.cpu}%`);
    setTxt("valVarCPU", `${latestVarRes.cpu}%`);
    setTxt("valFixedTP", latestFixedRes.tp);
    setTxt("valVarTP", latestVarRes.tp);

    // Render Gantt Charts
    const gFixBox = document.getElementById("ganttFixedBox");
    if (gFixBox) gFixBox.innerHTML = renderGantt(latestFixedRes.gantt, simTime);
    const gVarBox = document.getElementById("ganttVarBox");
    if (gVarBox) gVarBox.innerHTML = renderGantt(latestVarRes.gantt, simTime);

    // Render Tables
    renderTable("tblFixed", latestFixedRes.procs);
    renderTable("tblVar", latestVarRes.procs);

    // Render Queue Tracks
    renderLiveQueues(latestVarRes.procs);

    // Render Comparison Matrix
    renderComparisonMatrix(latestFixedRes, latestVarRes, simTime, q);

    // Render Math derivations
    renderMathInspector(latestVarRes);

    setTxt("clockDisplay", simTime);
    setTxt("cpuActiveProc", "Execution Concluded (T=" + simTime + ")");
    setTxt("quantumLeftDisplay", "0");
}

function renderLiveQueues(procs) {
    const q0 = document.getElementById("slotQ0");
    const q1 = document.getElementById("slotQ1");
    const q2 = document.getElementById("slotQ2");
    if (!q0 || !q1 || !q2) return;

    q0.innerHTML = ""; q1.innerHTML = ""; q2.innerHTML = "";

    const activeQ0 = procs.filter(p => p.remaining > 0 && p.queue === 0);
    const activeQ1 = procs.filter(p => p.remaining > 0 && p.queue === 1);
    const activeQ2 = procs.filter(p => p.remaining > 0 && p.queue === 2);

    if (activeQ0.length === 0) q0.innerHTML = '<span class="queue-empty-msg">Empty</span>';
    else activeQ0.forEach(p => q0.innerHTML += `<div class="pcb-chip">${p.pid} <span class="pcb-chip-rem">${p.remaining}u</span></div>`);

    if (activeQ1.length === 0) q1.innerHTML = '<span class="queue-empty-msg">Empty</span>';
    else activeQ1.forEach(p => q1.innerHTML += `<div class="pcb-chip">${p.pid} <span class="pcb-chip-rem">${p.remaining}u</span></div>`);

    if (activeQ2.length === 0) q2.innerHTML = '<span class="queue-empty-msg">Empty</span>';
    else activeQ2.forEach(p => q2.innerHTML += `<div class="pcb-chip">${p.pid} <span class="pcb-chip-rem">${p.remaining}u</span></div>`);
}

function renderComparisonMatrix(f, v, simTime, q) {
    const tbody = document.getElementById("tblCompareBody");
    if (!tbody) return;
    tbody.innerHTML = `
        <tr><td>Completed Workload</td><td><strong>${f.doneCount} / ${f.total}</strong></td><td><strong>${v.doneCount} / ${v.total}</strong></td><td>Fixed burst enables uniform completion; Variable isolates short jobs first.</td></tr>
        <tr><td>Average Waiting Time (AWT)</td><td><strong style="color:var(--cyan);">${f.awt} units</strong></td><td><strong style="color:var(--emerald);">${v.awt} units</strong></td><td>Short jobs in Variable mode complete with near-zero queue wait in Q0.</td></tr>
        <tr><td>Average Turnaround Time (ATT)</td><td><strong style="color:var(--cyan);">${f.att} units</strong></td><td><strong style="color:var(--emerald);">${v.att} units</strong></td><td>MLFQ yields lower turnaround time for interactive workloads.</td></tr>
        <tr><td>Average Response Time (ART)</td><td>${f.art} units</td><td>${v.art} units</td><td>Response time to first touch CPU remains rapid across all new arrivals.</td></tr>
        <tr><td>CPU Core Utilization</td><td><strong style="color:var(--cyan);">${f.cpu}%</strong></td><td><strong style="color:var(--emerald);">${v.cpu}%</strong></td><td>Higher utilization under continuous variable CPU bursts.</td></tr>
        <tr><td>Throughput Rate</td><td>${f.tp} proc/unit</td><td>${v.tp} proc/unit</td><td>Completed processes per unit of simulation horizon.</td></tr>
        <tr><td>Time Quantum per Queue Slice</td><td>${q} units</td><td>${q} units</td><td>Strict Round Robin time slicing bound enforced across queues.</td></tr>
    `;
}

function renderMathInspector(res) {
    const box = document.getElementById("processMathInspector");
    if (!box) return;
    const completedSample = res.completed.slice(0, 4);
    if (completedSample.length === 0) {
        box.innerHTML = "No completed processes in current horizon. Increase simulation time limit to observe completions.";
        return;
    }

    const lines = [
        "Step-by-Step Numerical Calculations for Completed Workload:",
        ""
    ];
    completedSample.forEach(p => {
        lines.push(`▶ [${p.pid}] Arrival=${p.arrival}, Burst=${p.burst}, Completion=${p.completionTime}`);
        lines.push(`   TAT = Completion (${p.completionTime}) - Arrival (${p.arrival}) = ${p.tat} units`);
        lines.push(`   WT  = TAT (${p.tat}) - Burst (${p.burst}) = ${p.wt} units`);
        lines.push("");
    });
    lines.push(`AWT Calculation: (${res.completed.map(p => p.wt).join(' + ')}) / ${res.completed.length} = ${res.awt} units`);
    lines.push(`ATT Calculation: (${res.completed.map(p => p.tat).join(' + ')}) / ${res.completed.length} = ${res.att} units`);

    box.innerText = lines.join("\\n");
}

function togglePlayAnimation() {
    if (isAnimating) {
        stopAnimation();
    } else {
        startAnimation();
    }
}

function startAnimation() {
    runInstantSimulator();
    if (!latestVarRes || !latestVarRes.ticksHistory.length) return;

    isAnimating = true;
    const btn = document.getElementById("btnPlayPause");
    if (btn) btn.innerHTML = `<svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg> Pause`;
    animCurrentTick = 0;

    const speed = parseInt(document.getElementById("animSpeed")?.value) || 300;
    animInterval = setInterval(() => {
        if (animCurrentTick >= latestVarRes.ticksHistory.length) {
            stopAnimation();
            return;
        }
        applyTick(animCurrentTick);
        animCurrentTick++;
    }, speed);
}

function stopAnimation() {
    isAnimating = false;
    if (animInterval) clearInterval(animInterval);
    const btn = document.getElementById("btnPlayPause");
    if (btn) btn.innerHTML = `<svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/></svg> Play Step Animation`;
}

function stepForwardOneTick() {
    if (!latestVarRes) runInstantSimulator();
    if (latestVarRes && animCurrentTick < latestVarRes.ticksHistory.length) {
        applyTick(animCurrentTick);
        animCurrentTick++;
    }
}

function applyTick(tickIdx) {
    const snap = latestVarRes.ticksHistory[tickIdx];
    const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    setTxt("clockDisplay", snap.t);
    setTxt("cpuActiveProc", snap.runningPid);
    setTxt("quantumLeftDisplay", snap.sliceLeft);

    const q0 = document.getElementById("slotQ0");
    const q1 = document.getElementById("slotQ1");
    const q2 = document.getElementById("slotQ2");

    if (q0) q0.innerHTML = snap.q0.length ? snap.q0.map(s => `<div class="pcb-chip">${s}</div>`).join('') : '<span class="queue-empty-msg">Empty</span>';
    if (q1) q1.innerHTML = snap.q1.length ? snap.q1.map(s => `<div class="pcb-chip">${s}</div>`).join('') : '<span class="queue-empty-msg">Empty</span>';
    if (q2) q2.innerHTML = snap.q2.length ? snap.q2.map(s => `<div class="pcb-chip">${s}</div>`).join('') : '<span class="queue-empty-msg">Empty</span>';
}

function applyPreset() {
    const val = document.getElementById("presetSelect")?.value;
    const setV = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };
    if (val === "standard") {
        setV("inpQuantum", 3);
        setV("inpSimTime", 60);
        setV("inpProcs", 8);
        setV("inpFixedBurst", 6);
        setV("inpMinBurst", 2);
        setV("inpMaxBurst", 14);
    } else if (val === "interactive_short") {
        setV("inpQuantum", 3);
        setV("inpSimTime", 50);
        setV("inpProcs", 6);
        setV("inpFixedBurst", 3);
        setV("inpMinBurst", 1);
        setV("inpMaxBurst", 4);
    } else if (val === "heavy_cpu") {
        setV("inpQuantum", 3);
        setV("inpSimTime", 80);
        setV("inpProcs", 6);
        setV("inpFixedBurst", 15);
        setV("inpMinBurst", 10);
        setV("inpMaxBurst", 25);
    } else if (val === "preemption") {
        setV("inpQuantum", 3);
        setV("inpSimTime", 45);
        setV("inpProcs", 5);
        setV("inpFixedBurst", 7);
        setV("inpMinBurst", 2);
        setV("inpMaxBurst", 12);
    }
    runInstantSimulator();
}

function randomizeSeed() {
    const seedInput = document.getElementById("inpSeed");
    if (seedInput) {
        seedInput.value = Math.floor(Math.random() * 9999) + 1;
    }
    runInstantSimulator();
}

function switchMainTab(tabId) {
    document.querySelectorAll(".tab-content").forEach(el => el.style.display = "none");
    document.querySelectorAll(".tab-btn").forEach(el => el.classList.remove("active"));
    const activePanel = document.getElementById(tabId);
    if (activePanel) activePanel.style.display = "block";
    if (window.event && window.event.currentTarget) {
        window.event.currentTarget.classList.add("active");
    }
}

function openAddProcessModal() { 
    const el = document.getElementById("addProcModal"); 
    if (el) el.style.display = "flex"; 
}

function closeAddProcessModal() { 
    const el = document.getElementById("addProcModal"); 
    if (el) el.style.display = "none"; 
}

function submitCustomProcess() {
    const pid = document.getElementById("custPid")?.value.trim() || "P_USER";
    const arr = parseInt(document.getElementById("custArr")?.value) || 0;
    const burst = parseInt(document.getElementById("custBurst")?.value) || 6;
    globalCustomProcs.push({ pid, arrival: arr, burst });
    closeAddProcessModal();
    runInstantSimulator();
}

// Auto-run on page load
window.addEventListener("DOMContentLoaded", () => {
    runInstantSimulator();
});
