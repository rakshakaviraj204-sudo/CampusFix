// CampusFix Client-side Application Logic

// Utility: Debounce for search input
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility: HTML Escaping to prevent XSS
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Toast Notifications
function showToast(message, type = 'success') {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    const colors = {
        success: 'bg-emerald-600 text-white',
        error: 'bg-rose-600 text-white',
        info: 'bg-indigo-600 text-white'
    };

    const icons = {
        success: 'fa-circle-check',
        error: 'fa-circle-xmark',
        info: 'fa-circle-info'
    };

    toast.className = `${colors[type] || colors.info} px-4 py-3 rounded-xl shadow-lg flex items-center gap-3 text-sm font-semibold pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0`;
    toast.innerHTML = `
        <i class="fa-solid ${icons[type] || icons.info} text-base"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    });

    // Auto dismiss after 3.5 seconds
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Helper: Status Badges
function getStatusBadge(status) {
    const map = {
        'Submitted': { class: 'badge-submitted', icon: 'fa-paper-plane' },
        'Assigned': { class: 'badge-assigned', icon: 'fa-user-check' },
        'In Progress': { class: 'badge-in-progress', icon: 'fa-screwdriver-wrench' },
        'Resolved': { class: 'badge-resolved', icon: 'fa-circle-check' }
    };
    const s = map[status] || { class: 'bg-slate-100 text-slate-700', icon: 'fa-circle' };
    return `<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${s.class}">
        <i class="fa-solid ${s.icon} text-[10px]"></i> ${status}
    </span>`;
}

// Helper: Priority Badges
function getPriorityBadge(priority) {
    const map = {
        'Urgent': 'priority-urgent',
        'High': 'priority-high',
        'Medium': 'priority-medium',
        'Low': 'priority-low'
    };
    const c = map[priority] || 'priority-medium';
    return `<span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${c}">${priority}</span>`;
}

// Render Progress Stepper (4 steps)
function renderProgressBar(currentStatus) {
    const steps = ['Submitted', 'Assigned', 'In Progress', 'Resolved'];
    const currentIndex = steps.indexOf(currentStatus);

    return `
    <div class="mt-4 pt-3 border-t border-slate-100">
        <div class="flex items-center justify-between relative">
            <div class="absolute left-3 right-3 top-3 -translate-y-1/2 h-0.5 bg-slate-200 -z-0"></div>
            ${steps.map((step, idx) => {
                const isPassed = idx <= currentIndex;
                const isCurrent = idx === currentIndex;
                let circleClass = 'bg-slate-100 border-2 border-slate-300 text-slate-400';
                let labelClass = 'text-slate-400 font-medium';

                if (isCurrent) {
                    circleClass = 'bg-indigo-600 border-2 border-indigo-600 text-white shadow-xs ring-4 ring-indigo-100';
                    labelClass = 'text-indigo-700 font-bold';
                } else if (isPassed) {
                    circleClass = 'bg-emerald-500 border-2 border-emerald-500 text-white';
                    labelClass = 'text-emerald-700 font-semibold';
                }

                return `
                <div class="flex flex-col items-center z-10">
                    <div class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] ${circleClass}">
                        ${isPassed && !isCurrent ? '<i class="fa-solid fa-check"></i>' : (idx + 1)}
                    </div>
                    <span class="text-[11px] mt-1.5 ${labelClass}">${step}</span>
                </div>
                `;
            }).join('')}
        </div>
    </div>
    `;
}

// Fetch Statistics
async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        const elTotal = document.getElementById('stat-total');
        const elActive = document.getElementById('stat-active');
        const elResolved = document.getElementById('stat-resolved');
        const elUrgent = document.getElementById('stat-urgent');

        if (elTotal) elTotal.innerText = data.total;
        if (elActive) elActive.innerText = data.active;
        if (elResolved) elResolved.innerText = data.resolved;
        if (elUrgent) elUrgent.innerText = data.urgent;
    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

// Load Issues for Public Campus Board
async function loadIssues() {
    const listEl = document.getElementById('issues-list');
    if (!listEl) return;

    const search = document.getElementById('search-input')?.value || '';
    const dept = document.getElementById('department-filter')?.value || 'All';
    const status = document.getElementById('status-filter')?.value || 'All';

    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (dept && dept !== 'All') params.append('department', dept);
    if (status && status !== 'All') params.append('status', status);

    try {
        const res = await fetch(`/api/issues?${params.toString()}`);
        const issues = await res.json();

        const countEl = document.getElementById('issue-count');
        if (countEl) countEl.innerText = `${issues.length} Issues`;

        if (issues.length === 0) {
            listEl.innerHTML = `
                <div class="bg-white rounded-2xl p-12 text-center border border-slate-200">
                    <div class="w-16 h-16 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                        <i class="fa-solid fa-clipboard-check"></i>
                    </div>
                    <h3 class="text-base font-bold text-slate-800">No issues matching your filters</h3>
                    <p class="text-sm text-slate-500 mt-1">Try resetting the department or status filter, or submit a new report.</p>
                </div>
            `;
            return;
        }

        listEl.innerHTML = issues.map(issue => `
            <div class="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs hover:border-slate-300 transition">
                <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
                    <div class="flex flex-wrap items-center gap-2">
                        <span class="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">${escapeHtml(issue.ticket_code)}</span>
                        <span class="text-xs font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg flex items-center gap-1.5">
                            <i class="fa-regular fa-building text-[11px] text-slate-500"></i> ${escapeHtml(issue.department)}
                        </span>
                        ${getPriorityBadge(issue.priority)}
                    </div>
                    <div>
                        ${getStatusBadge(issue.status)}
                    </div>
                </div>

                <h3 class="text-base sm:text-lg font-bold text-slate-900 mb-1">${escapeHtml(issue.title)}</h3>
                
                <div class="flex items-center gap-2 text-xs font-medium text-slate-500 mb-3">
                    <i class="fa-solid fa-location-dot text-rose-500"></i>
                    <span>${escapeHtml(issue.location)}</span>
                    <span class="text-slate-300">&bull;</span>
                    <i class="fa-regular fa-user text-slate-400"></i>
                    <span>Reported by ${escapeHtml(issue.reporter_name)} (${escapeHtml(issue.reporter_role)})</span>
                </div>

                <p class="text-sm text-slate-600 line-clamp-2 mb-4 leading-relaxed">${escapeHtml(issue.description)}</p>

                <!-- Visual 4-Step Stepper -->
                ${renderProgressBar(issue.status)}

                <div class="mt-4 pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-3">
                    <div class="flex items-center gap-3">
                        <button onclick="upvoteIssue(${issue.id}, this)" class="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-indigo-50 hover:text-indigo-600 hover:border-indigo-200 transition cursor-pointer text-slate-700">
                            <i class="fa-solid fa-thumbs-up text-indigo-500"></i>
                            <span>Me Too</span>
                            <span class="ml-1 bg-white px-1.5 py-0.5 rounded-full text-[11px] border border-slate-200 font-bold upvote-count">${issue.upvotes}</span>
                        </button>

                        ${issue.assigned_to && issue.assigned_to !== 'Unassigned' ? `
                            <span class="text-xs text-slate-500 flex items-center gap-1.5">
                                <i class="fa-solid fa-wrench text-slate-400"></i> Assigned to: <strong class="text-slate-700 font-semibold">${escapeHtml(issue.assigned_to)}</strong>
                            </span>
                        ` : ''}
                    </div>

                    <button onclick="openDetailsModal(${issue.id})" class="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 px-3.5 py-1.5 rounded-xl transition cursor-pointer">
                        <i class="fa-solid fa-timeline"></i>
                        <span>Track Timeline</span>
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error("Error loading issues:", err);
        listEl.innerHTML = `<div class="p-8 text-center text-rose-500">Failed to load issues. Please check server.</div>`;
    }
}

// Load Issues for Department Console
async function loadDeptIssues() {
    const container = document.getElementById('dept-issues-container');
    if (!container) return;

    const dept = currentDept || '';
    const status = document.getElementById('dept-status-filter')?.value || 'All';

    const params = new URLSearchParams();
    if (dept) params.append('department', dept);
    if (status && status !== 'All') params.append('status', status);

    try {
        const res = await fetch(`/api/issues?${params.toString()}`);
        const issues = await res.json();

        if (issues.length === 0) {
            container.innerHTML = `
                <div class="bg-white rounded-2xl p-12 text-center border border-slate-200">
                    <div class="w-16 h-16 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto mb-4 text-2xl">
                        <i class="fa-solid fa-circle-check text-emerald-500"></i>
                    </div>
                    <h3 class="text-base font-bold text-slate-800">No pending issues for ${escapeHtml(dept)}</h3>
                    <p class="text-sm text-slate-500 mt-1">All tickets in this category have been attended to or filter conditions matched none.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = issues.map(issue => `
            <div class="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-xs">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">${escapeHtml(issue.ticket_code)}</span>
                        ${getPriorityBadge(issue.priority)}
                        <span class="text-xs text-slate-500 flex items-center gap-1">
                            <i class="fa-regular fa-clock"></i> ${escapeHtml(issue.created_at)}
                        </span>
                    </div>
                    <div>
                        ${getStatusBadge(issue.status)}
                    </div>
                </div>

                <h3 class="text-lg font-bold text-slate-900 mb-1">${escapeHtml(issue.title)}</h3>
                <div class="text-xs font-semibold text-slate-500 mb-3 flex items-center gap-2">
                    <i class="fa-solid fa-location-dot text-rose-500"></i>
                    <span>${escapeHtml(issue.location)}</span>
                    <span class="text-slate-300">&bull;</span>
                    <span>Reporter: ${escapeHtml(issue.reporter_name)} (${escapeHtml(issue.reporter_role)})</span>
                </div>

                <p class="text-sm text-slate-600 mb-4 bg-slate-50 p-3 rounded-xl border border-slate-100">${escapeHtml(issue.description)}</p>

                <!-- Current Assignment and Notes -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4 text-xs">
                    <div class="bg-indigo-50/60 p-3 rounded-xl border border-indigo-100">
                        <span class="font-bold text-indigo-900 block mb-0.5">Assigned Staff / Tech:</span>
                        <span class="text-indigo-800">${escapeHtml(issue.assigned_to || 'Unassigned')}</span>
                    </div>
                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                        <span class="font-bold text-slate-700 block mb-0.5">Latest Notes:</span>
                        <span class="text-slate-600">${escapeHtml(issue.resolution_notes || 'No work notes logged yet.')}</span>
                    </div>
                </div>

                <!-- Action Buttons -->
                <div class="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                    <button onclick="openDetailsModal(${issue.id})" class="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 cursor-pointer">
                        <i class="fa-solid fa-clock-rotate-left"></i> View Full Timeline History
                    </button>

                    <button onclick="openStatusModal(${issue.id}, '${escapeHtml(issue.status)}', '${escapeHtml(issue.assigned_to || '')}', '${escapeHtml(issue.resolution_notes || '')}', '${escapeHtml(issue.ticket_code)}')" 
                            class="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs px-4 py-2 rounded-xl shadow-xs transition flex items-center gap-2 cursor-pointer">
                        <i class="fa-solid fa-sliders"></i>
                        <span>Update Status & Notes</span>
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error("Error loading department issues:", err);
    }
}

// Upvote Issue
async function upvoteIssue(issueId, btn) {
    try {
        const res = await fetch(`/api/issues/${issueId}/upvote`, { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            const countSpan = btn.querySelector('.upvote-count');
            if (countSpan) countSpan.innerText = data.upvotes;
            showToast("Upvoted! Department will see high campus priority.", "success");
        }
    } catch (err) {
        console.error("Upvote failed:", err);
    }
}

// Reset Filters
function resetFilters() {
    const sInput = document.getElementById('search-input');
    const dFilter = document.getElementById('department-filter');
    const stFilter = document.getElementById('status-filter');
    if (sInput) sInput.value = '';
    if (dFilter) dFilter.value = 'All';
    if (stFilter) stFilter.value = 'All';
    loadIssues();
}

// --- AI Smart Issue Classification Logic ---
let currentAiSuggestions = null;

async function triggerAiClassification(isAuto = false) {
    const descEl = document.getElementById("form-description");
    const titleEl = document.getElementById("form-title");
    const loadingEl = document.getElementById("ai-loading");
    const suggestionBox = document.getElementById("ai-suggestion-box");
    const feedbackEl = document.getElementById("ai-applied-feedback");

    const description = descEl ? descEl.value.trim() : "";
    const title = titleEl ? titleEl.value.trim() : "";

    // Require at least 3 characters in either field to trigger
    if (description.length < 3 && title.length < 3) {
        if (!isAuto) {
            showToast("Please enter a few words first.", "info");
        }
        return;
    }

    if (loadingEl) {
        loadingEl.classList.remove("hidden");
        loadingEl.classList.add("flex");
    }
    if (feedbackEl) feedbackEl.classList.add("hidden");

    try {
        const res = await fetch("/api/classify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ description, title })
        });

        const data = await res.json();
        if (res.ok && data.success) {
            currentAiSuggestions = data;

            // Update UI elements
            const deptEl = document.getElementById("ai-suggested-dept");
            const priorityEl = document.getElementById("ai-suggested-priority");
            const locEl = document.getElementById("ai-suggested-location");
            const badgeEl = document.getElementById("ai-confidence-badge");
            const reasonEl = document.getElementById("ai-reasoning-content");

            if (deptEl) deptEl.innerHTML = `<i class="fa-solid fa-building text-indigo-500 text-xs"></i> <span>${escapeHtml(data.suggested_department)}</span>`;
            if (priorityEl) priorityEl.innerHTML = getPriorityBadge(data.suggested_priority);
            
            if (locEl) {
                if (data.suggested_location) {
                    locEl.innerHTML = `<i class="fa-solid fa-location-dot text-rose-500 text-xs"></i> <span>${escapeHtml(data.suggested_location)}</span>`;
                } else {
                    locEl.innerHTML = `<span class="text-slate-400 italic">None found</span>`;
                }
            }

            if (badgeEl) badgeEl.innerText = `${data.confidence}% Match`;
            if (reasonEl) reasonEl.innerText = data.reasoning;

            // Automatically sync the suggested priority to the form-priority dropdown
            const prioritySelect = document.getElementById("form-priority");
            if (prioritySelect && data.suggested_priority) {
                prioritySelect.value = data.suggested_priority;
                updatePrioritySelectStyle(data.suggested_priority);
                // Visual ring feedback that priority dynamically adjusted
                prioritySelect.classList.add("ring-2", "ring-indigo-500");
                setTimeout(() => {
                    prioritySelect.classList.remove("ring-2", "ring-indigo-500");
                }, 800);
            }

            // Automatically sync suggested department if not manually set by user
            const deptSelect = document.getElementById("form-department");
            if (deptSelect && data.suggested_department && (!deptSelect.value || deptSelect.dataset.aiAutoFilled === "true")) {
                deptSelect.value = data.suggested_department;
                deptSelect.dataset.aiAutoFilled = "true";
            }

            // Automatically sync suggested location if empty or AI-populated
            const locInput = document.getElementById("form-location");
            if (locInput && data.suggested_location && (!locInput.value || locInput.dataset.aiAutoFilled === "true")) {
                locInput.value = data.suggested_location;
                locInput.dataset.aiAutoFilled = "true";
            }

            if (suggestionBox) suggestionBox.classList.remove("hidden");
            if (!isAuto) {
                showToast(`AI prioritized as ${data.suggested_priority}! Form updated.`, "info");
            }
        }
    } catch (err) {
        console.error("AI Classification error:", err);
    } finally {
        if (loadingEl) {
            loadingEl.classList.add("hidden");
            loadingEl.classList.remove("flex");
        }
    }
}

function updatePrioritySelectStyle(val) {
    const el = document.getElementById("form-priority");
    if (!el) return;
    el.classList.remove("border-rose-400", "border-amber-400", "border-emerald-400", "bg-rose-50/40", "bg-amber-50/40", "bg-emerald-50/40");
    if (val === 'High' || val === 'Urgent') {
        el.classList.add("border-rose-400", "bg-rose-50/40");
    } else if (val === 'Low') {
        el.classList.add("border-emerald-400", "bg-emerald-50/40");
    } else if (val === 'Medium') {
        el.classList.add("border-amber-400", "bg-amber-50/40");
    }
}

function applyAllAiSuggestions() {
    if (!currentAiSuggestions) return;

    // Apply department
    if (currentAiSuggestions.suggested_department) {
        const deptSelect = document.getElementById("form-department");
        if (deptSelect) deptSelect.value = currentAiSuggestions.suggested_department;
    }

    // Apply priority
    if (currentAiSuggestions.suggested_priority) {
        const prioritySelect = document.getElementById("form-priority");
        if (prioritySelect) {
            prioritySelect.value = currentAiSuggestions.suggested_priority;
            updatePrioritySelectStyle(currentAiSuggestions.suggested_priority);
        }
    }

    // Apply location if detected
    if (currentAiSuggestions.suggested_location) {
        const locInput = document.getElementById("form-location");
        if (locInput) locInput.value = currentAiSuggestions.suggested_location;
    }

    const feedbackEl = document.getElementById("ai-applied-feedback");
    if (feedbackEl) feedbackEl.classList.remove("hidden");

    showToast("Suggestions applied! You can review or edit them.", "success");
}

function applyAiField(field) {
    if (!currentAiSuggestions) return;

    if (field === 'department') {
        const deptSelect = document.getElementById("form-department");
        if (deptSelect) {
            deptSelect.value = currentAiSuggestions.suggested_department;
            showToast(`Applied Department: ${currentAiSuggestions.suggested_department}`, "success");
        }
    } else if (field === 'priority') {
        const prioritySelect = document.getElementById("form-priority");
        if (prioritySelect) {
            prioritySelect.value = currentAiSuggestions.suggested_priority;
            updatePrioritySelectStyle(currentAiSuggestions.suggested_priority);
            showToast(`Applied Priority: ${currentAiSuggestions.suggested_priority}`, "success");
        }
    } else if (field === 'location') {
        if (currentAiSuggestions.suggested_location) {
            const locInput = document.getElementById("form-location");
            if (locInput) {
                locInput.value = currentAiSuggestions.suggested_location;
                showToast(`Applied Location: ${currentAiSuggestions.suggested_location}`, "success");
            }
        } else {
            showToast("No specific location was detected in description.", "info");
        }
    }
}

// Modal Helpers: Report Issue
function openReportModal() {
    const modal = document.getElementById("report-modal");
    if (modal) modal.classList.remove("hidden");

    // Attach debounced auto-detection listeners if not already attached
    initAiEventListeners();
}

function initAiEventListeners() {
    const descInput = document.getElementById("form-description");
    if (descInput && !descInput.dataset.aiBound) {
        descInput.dataset.aiBound = "true";
        descInput.addEventListener("input", debounce(() => {
            triggerAiClassification(true);
        }, 300));
        descInput.addEventListener("blur", () => {
            triggerAiClassification(true);
        });
        descInput.addEventListener("change", () => {
            triggerAiClassification(true);
        });
    }

    const titleInput = document.getElementById("form-title");
    if (titleInput && !titleInput.dataset.aiBound) {
        titleInput.dataset.aiBound = "true";
        titleInput.addEventListener("input", debounce(() => {
            triggerAiClassification(true);
        }, 350));
        titleInput.addEventListener("blur", () => {
            triggerAiClassification(true);
        });
    }

    const prioritySelect = document.getElementById("form-priority");
    if (prioritySelect && !prioritySelect.dataset.styleBound) {
        prioritySelect.dataset.styleBound = "true";
        prioritySelect.addEventListener("change", (e) => {
            updatePrioritySelectStyle(e.target.value);
        });
        updatePrioritySelectStyle(prioritySelect.value);
    }
}

function closeReportModal() {
    const modal = document.getElementById("report-modal");
    if (modal) modal.classList.add("hidden");

    // Reset AI state
    currentAiSuggestions = null;
    const box = document.getElementById("ai-suggestion-box");
    if (box) box.classList.add("hidden");
    const loading = document.getElementById("ai-loading");
    if (loading) loading.classList.add("hidden");
    const feedback = document.getElementById("ai-applied-feedback");
    if (feedback) feedback.classList.add("hidden");
}

// Submit Issue Form
async function submitIssue(e) {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Submitting...`;

    const payload = {
        title: document.getElementById('form-title').value,
        department: document.getElementById('form-department').value,
        priority: document.getElementById('form-priority').value,
        location: document.getElementById('form-location').value,
        reporter_name: document.getElementById('form-name').value,
        reporter_role: document.getElementById('form-role').value,
        description: document.getElementById('form-description').value
    };

    try {
        const res = await fetch('/api/issues', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.success) {
            closeReportModal();
            document.getElementById('report-form').reset();
            showToast(`Report submitted successfully! Ticket ${data.ticket_code}`, 'success');
            loadStats();
            loadIssues();
        } else {
            showToast(data.error || 'Failed to submit report', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while submitting issue', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-paper-plane"></i> <span>Submit Report</span>`;
    }
}

// Modal Helpers: Status Update
function openStatusModal(id, currentStatus, currentAssigned, currentNotes, ticketCode) {
    document.getElementById('status-issue-id').value = id;
    document.getElementById('update-status-select').value = currentStatus;
    document.getElementById('update-assigned-to').value = currentAssigned === 'Unassigned' ? '' : currentAssigned;
    document.getElementById('update-notes').value = currentNotes;
    document.getElementById('status-modal-subtitle').innerText = `Managing Ticket: ${ticketCode}`;

    const modal = document.getElementById('status-modal');
    if (modal) modal.classList.remove('hidden');
}

function closeStatusModal() {
    const modal = document.getElementById('status-modal');
    if (modal) modal.classList.add('hidden');
}

// Save Status Update
async function saveStatusUpdate(e) {
    e.preventDefault();
    const id = document.getElementById('status-issue-id').value;
    const btn = document.getElementById('save-status-btn');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Saving...`;

    const payload = {
        status: document.getElementById('update-status-select').value,
        assigned_to: document.getElementById('update-assigned-to').value,
        notes: document.getElementById('update-notes').value,
        updated_by: "Department Staff"
    };

    try {
        const res = await fetch(`/api/issues/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok && data.success) {
            closeStatusModal();
            showToast(`Ticket status updated to ${payload.status}!`, 'success');
            loadDeptIssues();
            loadStats();
        } else {
            showToast(data.error || 'Failed to update status', 'error');
        }
    } catch (err) {
        console.error(err);
        showToast('Network error while updating status', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> <span>Apply Status Update</span>`;
    }
}

// Details & Full Timeline Tracker Modal
async function openDetailsModal(issueId) {
    const modal = document.getElementById('details-modal');
    const content = document.getElementById('details-modal-content');
    if (!modal || !content) return;

    modal.classList.remove('hidden');
    content.innerHTML = `
        <div class="p-12 text-center text-slate-400">
            <i class="fa-solid fa-spinner fa-spin text-2xl text-indigo-500 mb-2"></i>
            <p>Fetching full ticket history...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/issues/${issueId}`);
        const issue = await res.json();

        if (!res.ok) {
            content.innerHTML = `<div class="p-6 text-center text-rose-500">${issue.error || 'Issue not found'}</div>`;
            return;
        }

        content.innerHTML = `
            <div class="mb-5">
                <div class="flex flex-wrap items-center gap-2 mb-2">
                    <span class="font-mono text-xs font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-lg border border-indigo-100">${escapeHtml(issue.ticket_code)}</span>
                    <span class="text-xs font-semibold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-lg">${escapeHtml(issue.department)}</span>
                    ${getPriorityBadge(issue.priority)}
                    ${getStatusBadge(issue.status)}
                </div>
                <h2 class="text-xl font-extrabold text-slate-900">${escapeHtml(issue.title)}</h2>
                <div class="text-xs text-slate-500 mt-1 flex items-center gap-2">
                    <i class="fa-solid fa-location-dot text-rose-500"></i>
                    <span>${escapeHtml(issue.location)}</span>
                    <span>&bull;</span>
                    <span>Reported by: <strong>${escapeHtml(issue.reporter_name)} (${escapeHtml(issue.reporter_role)})</strong></span>
                </div>
            </div>

            <!-- Issue Description Box -->
            <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-4 mb-6">
                <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Problem Description</p>
                <p class="text-sm text-slate-700 whitespace-pre-wrap">${escapeHtml(issue.description)}</p>
            </div>

            <!-- Assignment Info -->
            <div class="grid grid-cols-2 gap-3 mb-6">
                <div class="bg-indigo-50/70 p-3 rounded-xl border border-indigo-100 text-xs">
                    <span class="text-slate-500 font-medium block">Assigned Personnel</span>
                    <span class="text-slate-900 font-bold">${escapeHtml(issue.assigned_to || 'Unassigned')}</span>
                </div>
                <div class="bg-slate-50 p-3 rounded-xl border border-slate-200/80 text-xs">
                    <span class="text-slate-500 font-medium block">Community Impact Upvotes</span>
                    <span class="text-slate-900 font-bold"><i class="fa-solid fa-thumbs-up text-indigo-500 mr-1"></i> ${issue.upvotes} Students/Staff affected</span>
                </div>
            </div>

            <!-- Progression Stepper -->
            <div class="mb-6">
                <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Stage Progression</p>
                ${renderProgressBar(issue.status)}
            </div>

            <!-- Vertical Activity Timeline -->
            <div class="mt-8">
                <p class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Official Action Log & History</p>
                <div class="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                    ${(issue.timeline || []).map((log, index) => `
                        <div class="relative">
                            <div class="absolute -left-6 top-1 w-4 h-4 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center">
                                <div class="w-1.5 h-1.5 rounded-full bg-indigo-600"></div>
                            </div>
                            <div>
                                <div class="flex items-center gap-2">
                                    <span class="text-xs font-bold text-slate-800">${escapeHtml(log.status)}</span>
                                    <span class="text-[11px] text-slate-400">&bull; ${escapeHtml(log.created_at)}</span>
                                </div>
                                <p class="text-xs text-slate-600 mt-0.5">${escapeHtml(log.notes || 'Status updated.')}</p>
                                <span class="text-[10px] text-slate-400 font-medium">Logged by: ${escapeHtml(log.updated_by || 'System')}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    } catch (err) {
        console.error("Error fetching issue details:", err);
        content.innerHTML = `<div class="p-6 text-center text-rose-500">Failed to load issue details.</div>`;
    }
}

function closeDetailsModal() {
    const modal = document.getElementById('details-modal');
    if (modal) modal.classList.add('hidden');
}

// Close modals when clicking outside modal box
window.addEventListener('click', (e) => {
    const reportModal = document.getElementById('report-modal');
    const detailsModal = document.getElementById('details-modal');
    const statusModal = document.getElementById('status-modal');

    if (e.target === reportModal) closeReportModal();
    if (e.target === detailsModal) closeDetailsModal();
    if (e.target === statusModal) closeStatusModal();
});
