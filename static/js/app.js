/* ═══════════════════════════════════════════════════════════════════════════
   Student Study Planner — Frontend JavaScript
   API calls, schedule interactions, chart rendering, availability grid
   ═══════════════════════════════════════════════════════════════════════════ */

// ── Utility ──────────────────────────────────────────────────────────────

async function apiCall(url, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

function showToast(msg, type = 'success') {
    const el = document.createElement('div');
    el.className = `flash-message flash-${type}`;
    el.innerHTML = `${msg} <button class="flash-close" onclick="this.parentElement.remove()">✕</button>`;
    const main = document.querySelector('.main-content');
    if (main) main.prepend(el);
    setTimeout(() => el.remove(), 4000);
}

// ── Subject CRUD ─────────────────────────────────────────────────────────

async function deleteSubject(id) {
    if (!confirm('Delete this subject and all its tasks?')) return;
    const data = await apiCall(`/api/subjects/${id}`, 'DELETE');
    if (data.status === 'deleted') {
        const row = document.getElementById(`subject-row-${id}`);
        if (row) {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            setTimeout(() => row.remove(), 300);
        }
        showToast('Subject deleted.');
    }
}

// ── Task CRUD ────────────────────────────────────────────────────────────

async function toggleTask(id) {
    const data = await apiCall(`/api/tasks/${id}/complete`, 'PUT');
    if (data.status === 'toggled') {
        const row = document.getElementById(`task-row-${id}`);
        const btn = document.getElementById(`btn-check-${id}`);
        if (data.completed) {
            row.classList.add('item-completed');
            btn.classList.add('checked');
            btn.textContent = '✓';
            row.querySelector('.item-name').classList.add('line-through');
        } else {
            row.classList.remove('item-completed');
            btn.classList.remove('checked');
            btn.textContent = '';
            row.querySelector('.item-name').classList.remove('line-through');
        }
    }
}

async function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    const data = await apiCall(`/api/tasks/${id}`, 'DELETE');
    if (data.status === 'deleted') {
        const row = document.getElementById(`task-row-${id}`);
        if (row) {
            row.style.transition = 'all 0.3s ease';
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            setTimeout(() => row.remove(), 300);
        }
        showToast('Task deleted.');
    }
}

// ── Availability Grid ────────────────────────────────────────────────────

let isDragging = false;
let dragMode = null; // 'add' or 'remove'

function toggleAvailability(cell) {
    cell.classList.toggle('available');
}

// Drag-to-select on the availability grid
document.addEventListener('mousedown', (e) => {
    if (e.target.classList.contains('availability-cell')) {
        isDragging = true;
        dragMode = e.target.classList.contains('available') ? 'remove' : 'add';
        toggleAvailability(e.target);
        e.preventDefault();
    }
});

document.addEventListener('mouseover', (e) => {
    if (isDragging && e.target.classList.contains('availability-cell')) {
        if (dragMode === 'add') e.target.classList.add('available');
        else e.target.classList.remove('available');
    }
});

document.addEventListener('mouseup', () => { isDragging = false; });

async function saveAvailability() {
    const cells = document.querySelectorAll('.availability-cell.available');
    // Group contiguous hours per day
    const dayHours = {};
    cells.forEach(cell => {
        const day = parseInt(cell.dataset.day);
        const hour = parseInt(cell.dataset.hour);
        if (!dayHours[day]) dayHours[day] = [];
        dayHours[day].push(hour);
    });

    const slots = [];
    for (const [day, hours] of Object.entries(dayHours)) {
        hours.sort((a, b) => a - b);
        let start = hours[0];
        let prev = hours[0];
        for (let i = 1; i <= hours.length; i++) {
            if (i < hours.length && hours[i] === prev + 1) {
                prev = hours[i];
            } else {
                slots.push({ day: parseInt(day), start, end: prev + 1 });
                if (i < hours.length) {
                    start = hours[i];
                    prev = hours[i];
                }
            }
        }
    }

    const data = await apiCall('/availability', 'POST', { slots });
    if (data.status === 'saved') {
        showToast('Availability saved!');
    }
}

function clearAvailability() {
    document.querySelectorAll('.availability-cell.available').forEach(cell => {
        cell.classList.remove('available');
    });
}

// ── Schedule Generation ──────────────────────────────────────────────────

async function generateSchedule() {
    const btn = document.getElementById('btn-generate');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Generating...';
    }

    try {
        const data = await apiCall('/api/generate-schedule', 'POST');
        if (data.error) {
            showToast(data.error, 'error');
        } else {
            showToast(`Schedule generated! ${data.count} study blocks created.`);
            setTimeout(() => location.reload(), 800);
        }
    } catch (err) {
        showToast('Failed to generate schedule.', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Generate Schedule';
        }
    }
}

// ── Simple Canvas Bar Chart ──────────────────────────────────────────────

function drawBarChart(canvasId, labels, values, label) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const w = rect.width;
    const h = rect.height;
    const padding = { top: 20, right: 20, bottom: 50, left: 45 };
    const chartW = w - padding.left - padding.right;
    const chartH = h - padding.top - padding.bottom;

    const maxVal = Math.max(...values, 1);
    const barWidth = Math.min(40, (chartW / labels.length) * 0.6);
    const gap = chartW / labels.length;

    const colors = [
        '#6C63FF', '#3b82f6', '#10b981', '#f59e0b',
        '#ec4899', '#8b5cf6', '#06d6a0', '#ef4444'
    ];

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(w - padding.right, y);
        ctx.stroke();

        // Y-axis labels
        ctx.fillStyle = '#6b6b85';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'right';
        const val = (maxVal - (maxVal / 4) * i).toFixed(1);
        ctx.fillText(val, padding.left - 8, y + 4);
    }

    // Bars
    labels.forEach((lbl, i) => {
        const barH = (values[i] / maxVal) * chartH;
        const x = padding.left + gap * i + (gap - barWidth) / 2;
        const y = padding.top + chartH - barH;

        // Bar gradient
        const grad = ctx.createLinearGradient(x, y, x, y + barH);
        const col = colors[i % colors.length];
        grad.addColorStop(0, col);
        grad.addColorStop(1, col + '66');
        ctx.fillStyle = grad;

        // Rounded top
        const r = Math.min(6, barWidth / 2);
        ctx.beginPath();
        ctx.moveTo(x, y + r);
        ctx.arcTo(x, y, x + r, y, r);
        ctx.arcTo(x + barWidth, y, x + barWidth, y + r, r);
        ctx.lineTo(x + barWidth, y + barH);
        ctx.lineTo(x, y + barH);
        ctx.closePath();
        ctx.fill();

        // Value on top
        ctx.fillStyle = '#f0f0f5';
        ctx.font = '600 11px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(values[i].toFixed(1), x + barWidth / 2, y - 6);

        // X-axis label
        ctx.fillStyle = '#9d9db5';
        ctx.font = '11px Inter, sans-serif';
        ctx.textAlign = 'center';
        const labelY = padding.top + chartH + 20;

        // Truncate long labels
        const short = lbl.length > 8 ? lbl.slice(0, 7) + '…' : lbl;
        ctx.fillText(short, x + barWidth / 2, labelY);
    });
}

// ── Auto-dismiss flash messages ──────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.flash-message').forEach(el => {
        setTimeout(() => {
            el.style.transition = 'all 0.3s ease';
            el.style.opacity = '0';
            el.style.transform = 'translateY(-10px)';
            setTimeout(() => el.remove(), 300);
        }, 5000);
    });
});
