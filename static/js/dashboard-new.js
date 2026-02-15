/**
 * Unique Triage Dashboard - Light Theme with Neon Effects
 * Features: Gauge charts, Radar chart, Queue visualization, Animations
 */

// Backend API URL
const API_BASE_URL = 'https://pragyan-neuranexus.onrender.com';

// Global chart instances
let riskChart = null;
let vitalsRadar = null;
let ageChart = null;

// Color palette - Neon theme
const COLORS = {
    neonCyan: '#00d4ff',
    neonMagenta: '#ff00ff',
    neonPurple: '#8b5cf6',
    neonGreen: '#00ff88',
    neonOrange: '#ff6b35',
    neonPink: '#ff0080',
    riskHigh: '#ff4757',
    riskMedium: '#ffa502',
    riskLow: '#2ed573',
    chartColors: ['#00d4ff', '#ff00ff', '#8b5cf6', '#00ff88', '#ff6b35', '#ff0080']
};

// Fetch dashboard data
async function fetchDashboardData(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/dashboard-data` + (qs ? `?${qs}` : '');
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load dashboard data: ' + (await res.text()));
    return res.json();
}

// Update department capacity
async function updateDepartmentCapacity(department, capacity) {
    const res = await fetch(`${API_BASE_URL}/update-department-capacity`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ department, capacity })
    });
    const data = await res.json();
    if (!data.success) {
        throw new Error(data.error || 'Failed to update capacity');
    }
    return data;
}

// Get department capacity
async function getDepartmentCapacity() {
    const res = await fetch(`${API_BASE_URL}/get-department-capacity`);
    const data = await res.json();
    if (!data.success) {
        throw new Error(data.error || 'Failed to get capacity');
    }
    return data.department_capacity;
}

// Show capacity edit modal
async function showCapacityEditModal() {
    // Get current capacity values
    const capacityData = await getDepartmentCapacity();
    
    // Create modal HTML
    const modalHtml = `
        <div id="capacityModal" class="modal-overlay">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Edit Department Capacity</h3>
                    <button class="modal-close" onclick="closeCapacityModal()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="capacity-form">
                        ${Object.entries(capacityData).map(([dept, cap]) => `
                            <div class="capacity-row">
                                <label for="cap_${dept.replace(/\s+/g, '_')}">${dept}</label>
                                <input type="number" id="cap_${dept.replace(/\s+/g, '_')}" 
                                       value="${cap}" min="1" max="100" 
                                       data-department="${dept}">
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn-cancel" onclick="closeCapacityModal()">Cancel</button>
                    <button class="btn-save" onclick="saveCapacity()">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('capacityModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// Close capacity modal
function closeCapacityModal() {
    const modal = document.getElementById('capacityModal');
    if (modal) {
        modal.remove();
    }
}

// Save capacity changes
async function saveCapacity() {
    const inputs = document.querySelectorAll('#capacityModal input[data-department]');
    const updates = [];
    
    for (const input of inputs) {
        const department = input.dataset.department;
        const capacity = parseInt(input.value);
        
        if (capacity > 0) {
            updates.push({ department, capacity });
        }
    }
    
    try {
        // Update each department capacity
        for (const update of updates) {
            await updateDepartmentCapacity(update.department, update.capacity);
        }
        
        // Close modal
        closeCapacityModal();
        
        // Show success message with SweetAlert
        await Swal.fire({
            icon: 'success',
            title: 'Success!',
            text: 'Capacity updated successfully!',
            timer: 2000,
            showConfirmButton: false
        });
        
        // Refresh the dashboard
        const data = await fetchDashboardData();
        renderGaugeCharts(data.department_status);
        
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Error updating capacity: ' + error.message
        });
    }
}

// Render Doughnut Chart for Risk Distribution
function renderRiskChart(data) {
    const ctx = document.getElementById('riskChart').getContext('2d');
    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = [COLORS.riskLow, COLORS.riskMedium, COLORS.riskHigh];
    
    if (riskChart) riskChart.destroy();
    
    riskChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: values,
                backgroundColor: colors,
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: { size: 12, weight: '600' }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

// Render Gauge Charts for Department Capacity
function renderGaugeCharts(deptStatus) {
    const container = document.getElementById('gaugeContainer');
    container.innerHTML = '';
    
    const depts = Object.entries(deptStatus).sort((a, b) => b[1].utilization_percentage - a[1].utilization_percentage);
    
    depts.forEach(([dept, info], index) => {
        const utilization = info.utilization_percentage;
        let gaugeClass = 'good';
        let glowColor = COLORS.neonGreen;
        
        if (utilization >= 100) {
            gaugeClass = 'critical';
            glowColor = COLORS.riskHigh;
        } else if (utilization >= 70) {
            gaugeClass = 'warning';
            glowColor = COLORS.riskMedium;
        }
        
        const gaugeItem = document.createElement('div');
        gaugeItem.className = 'gauge-item';
        gaugeItem.style.animationDelay = `${index * 0.05}s`;
        gaugeItem.innerHTML = `
            <div class="gauge-label" title="${dept}">${dept}</div>
            <div class="gauge-value ${gaugeClass}" style="text-shadow: 0 0 15px ${glowColor}">${utilization}%</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${info.current_patients}/${info.capacity}</div>
        `;
        
        // Create mini progress bar
        const progressBar = document.createElement('div');
        progressBar.style.cssText = `
            height: 6px;
            background: rgba(0,0,0,0.1);
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
        `;
        
        const progress = document.createElement('div');
        progress.style.cssText = `
            height: 100%;
            width: ${Math.min(utilization, 100)}%;
            background: linear-gradient(90deg, ${glowColor}, ${glowColor}aa);
            border-radius: 3px;
            transition: width 0.5s ease;
            box-shadow: 0 0 10px ${glowColor};
        `;
        
        progressBar.appendChild(progress);
        gaugeItem.appendChild(progressBar);
        container.appendChild(gaugeItem);
    });
}

// Render Radar Chart for Patient Vitals
function renderVitalsRadar(patient) {
    const ctx = document.getElementById('vitalsRadar').getContext('2d');
    const badge = document.getElementById('patientBadge');
    const patientIdEl = document.getElementById('selectedPatientId');
    
    if (!patient) {
        if (vitalsRadar) {
            vitalsRadar.destroy();
            vitalsRadar = null;
        }
        badge.textContent = 'Select Patient';
        badge.style.background = 'rgba(139,92,246,0.1)';
        badge.style.color = 'var(--neon-purple)';
        patientIdEl.textContent = 'No patient selected';
        // Hide risk assessment card
        const riskAssessmentCard = document.getElementById('riskAssessmentCard');
        if (riskAssessmentCard) {
            riskAssessmentCard.style.display = 'none';
        }
        return;
    }
    
    const labels = ['Systolic BP', 'Diastolic BP', 'Heart Rate', 'Temp (°F)', 'O2 Sat (%)', 'Pain'];
    const values = [
        patient.blood_pressure_systolic || 0,
        patient.blood_pressure_diastolic || 0,
        patient.heart_rate || 0,
        patient.temperature || 0,
        patient.oxygen_saturation || 0,
        patient.pain_level || 0
    ];
    
    // Normalize values for radar (approximate ranges)
    const normalized = [
        (values[0] / 200) * 100,  // BP systolic max 200
        (values[1] / 120) * 100,  // BP diastolic max 120
        (values[2] / 150) * 100,  // HR max 150
        (values[3] / 110) * 100,  // Temp max 110
        (values[4] / 100) * 100,  // O2 max 100
        (values[5] / 10) * 100    // Pain max 10
    ];
    
    if (vitalsRadar) vitalsRadar.destroy();
    
    vitalsRadar = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Patient Vitals',
                data: normalized,
                backgroundColor: 'rgba(139, 92, 246, 0.2)',
                borderColor: COLORS.neonPurple,
                borderWidth: 2,
                pointBackgroundColor: COLORS.neonPurple,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { display: false },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    pointLabels: {
                        font: { size: 11, weight: '600' }
                    }
                }
            },
            plugins: {
                legend: { display: false }
            },
            animation: {
                duration: 800,
                easing: 'easeOutQuart'
            }
        }
    });
    
    // Update patient info
    badge.textContent = patient.risk_level ? patient.risk_level.toUpperCase() : 'Unknown';
    const riskColors = {
        'high': COLORS.riskHigh,
        'medium': COLORS.riskMedium,
        'low': COLORS.riskLow
    };
    const color = riskColors[patient.risk_level] || COLORS.neonPurple;
    badge.style.background = `${color}20`;
    badge.style.color = color;
    patientIdEl.textContent = `Patient #${patient.patient_id}`;
    
    // Render risk assessment details
    renderRiskAssessment(patient);
}

// Render Risk Assessment Details
function renderRiskAssessment(patient) {
    const riskAssessmentCard = document.getElementById('riskAssessmentCard');
    if (!riskAssessmentCard) return;
    
    // Show the card
    riskAssessmentCard.style.display = 'block';
    
    // Get elements
    const patientIdValue = document.getElementById('patientIdValue');
    const riskLevelBadge = document.getElementById('riskLevelBadge');
    const riskConfidence = document.getElementById('riskConfidence');
    const recommendedDept = document.getElementById('recommendedDept');
    const deptConfidence = document.getElementById('deptConfidence');
    const explainabilityList = document.getElementById('explainabilityList');
    
    // Update patient ID
    if (patientIdValue) {
        patientIdValue.textContent = patient.patient_id ? `#${patient.patient_id}` : '-';
    }
    
    // Update risk level
    if (riskLevelBadge) {
        const riskLevel = patient.risk_level || '-';
        riskLevelBadge.textContent = riskLevel.toUpperCase();
        riskLevelBadge.className = 'risk-level-badge ' + riskLevel.toLowerCase();
    }
    
    // Update risk confidence
    if (riskConfidence) {
        riskConfidence.textContent = patient.risk_confidence || '-';
    }
    
    // Update recommended department
    if (recommendedDept) {
        recommendedDept.textContent = patient.recommended_department || '-';
    }
    
    // Update department confidence
    if (deptConfidence) {
        deptConfidence.textContent = patient.dept_confidence || '-';
    }
    
    // Update explainability factors
    if (explainabilityList) {
        const explainability = patient.explainability || [];
        if (explainability.length === 0) {
            explainabilityList.innerHTML = '<p style="color: var(--text-muted); font-size: 0.85rem;">No assessment factors available</p>';
        } else {
            explainabilityList.innerHTML = explainability.map(factor => {
                const contribution = factor.contribution || 'low';
                const icon = getFactorIcon(factor.factor);
                return `
                    <div class="explainability-factor ${contribution}">
                        <span class="factor-icon">${icon}</span>
                        <div class="factor-content">
                            <div class="factor-name">${factor.factor || '-'}</div>
                            <div class="factor-description">${factor.description || ''}</div>
                        </div>
                        <span class="factor-contribution ${contribution}">${contribution}</span>
                    </div>
                `;
            }).join('');
        }
    }
}

// Get icon for factor type
function getFactorIcon(factorName) {
    if (!factorName) return '📌';
    const name = factorName.toLowerCase();
    if (name.includes('age')) return '👤';
    if (name.includes('blood pressure') || name.includes('bp')) return '💓';
    if (name.includes('heart') || name.includes('tachycardia') || name.includes('bradycardia')) return '❤️';
    if (name.includes('fever') || name.includes('temperature')) return '🌡️';
    if (name.includes('oxygen') || name.includes('o2')) return '🫁';
    if (name.includes('pain')) return '😫';
    if (name.includes('risk') || name.includes('overall')) return '⚠️';
    return '📌';
}

// Render KPI-style cards for Age Groups - showing high-risk percentage (compact, no scroll issue)
function renderAgeChart(ageGroups) {
    const container = document.getElementById('ageChartContainer');
    if (!container) return;
    
    const groups = Object.entries(ageGroups || {}).map(([name, data]) => ({
        name,
        percent: data.high_risk_percentage || 0,
        count: data.count || 0
    }));
    
    if (groups.length === 0) {
        container.innerHTML = '<p style="text-align:center;color:var(--text-muted);">No age group data</p>';
        return;
    }
    
    container.innerHTML = groups.map(group => {
        const percent = group.percent;
        const color = percent > 30 ? COLORS.riskHigh : percent > 15 ? COLORS.riskMedium : COLORS.riskLow;
        return `
            <div class="age-kpi-card">
                <div class="age-kpi-label">${group.name}</div>
                <div class="age-kpi-percentage" style="color: ${color}; text-shadow: 0 0 8px ${color}33;">${percent.toFixed(1)}%</div>
                <div class="age-kpi-count">${group.count} patients</div>
                <div class="age-kpi-bar">
                    <div class="age-kpi-fill" style="width: ${percent}%; background: linear-gradient(90deg, ${color}, ${color}66); box-shadow: 0 0 8px ${color}44;"></div>
                </div>
            </div>
        `;
    }).join('');
}

// Render Queue Visualization
function renderQueue(patientList, maxItems = 10) {
    const container = document.getElementById('queueContainer');
    const queueCount = document.getElementById('queueCount');
    
    if (!patientList || patientList.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📭</div>
                <p>No patients in queue</p>
            </div>
        `;
        queueCount.textContent = '0 patients';
        return;
    }
    
    // Sort by risk level (high first)
    const riskOrder = { 'high': 0, 'medium': 1, 'low': 2 };
    const sorted = [...patientList].sort((a, b) => {
        const riskA = riskOrder[a.risk_level] ?? 3;
        const riskB = riskOrder[b.risk_level] ?? 3;
        return riskA - riskB;
    }).slice(0, maxItems);
    
    queueCount.textContent = `${patientList.length} patients`;
    
    container.innerHTML = sorted.map((patient, idx) => {
        const riskClass = patient.risk_level || 'low';
        return `
            <div class="queue-item ${riskClass}-risk slide-in" style="animation-delay: ${idx * 0.05}s">
                <div class="queue-position">${idx + 1}</div>
                <div class="queue-patient-id">#${patient.patient_id}</div>
                <span class="queue-risk" style="background: ${riskClass === 'high' ? 'rgba(255,71,87,0.15)' : riskClass === 'medium' ? 'rgba(255,165,2,0.15)' : 'rgba(46,213,115,0.15)'}; color: ${riskClass === 'high' ? COLORS.riskHigh : riskClass === 'medium' ? COLORS.riskMedium : COLORS.riskLow}">${riskClass.toUpperCase()}</span>
            </div>
        `;
    }).join('');
}

// Render Fairness Insights
function renderInsights(data) {
    const container = document.getElementById('insightsGrid');
    if (!container) return;
    
    const insights = [];
    
    try {
        // Fairness metrics
        if (data && data.fairness_metrics) {
            if (data.fairness_metrics.age_statistical_parity_difference !== undefined) {
                const spd = data.fairness_metrics.age_statistical_parity_difference;
                const assessment = data.fairness_metrics.age_disparity_assessment;
                insights.push({
                    title: 'Age Parity',
                    value: `${spd}%`,
                    desc: assessment || 'No assessment available',
                    type: spd > 15 ? 'warning' : 'success'
                });
            }
            
            if (data.fairness_metrics.gender_disparate_impact_ratio !== undefined) {
                const di = data.fairness_metrics.gender_disparate_impact_ratio;
                const assessment = data.fairness_metrics.gender_disparity_assessment;
                insights.push({
                    title: 'Gender Fairness',
                    value: typeof di === 'number' ? di.toFixed(2) : di,
                    desc: assessment || 'No assessment available',
                    type: di < 0.8 ? 'warning' : 'success'
                });
            }
        }
        
        // Department status
        if (data && data.department_status) {
            const overcrowded = Object.entries(data.department_status).filter(([k, v]) => (v.utilization_percentage || 0) > 100);
            const busy = Object.entries(data.department_status).filter(([k, v]) => (v.utilization_percentage || 0) > 70 && (v.utilization_percentage || 0) <= 100);
            
            if (overcrowded.length > 0) {
                insights.push({
                    title: 'Overcrowded Depts',
                    value: overcrowded.length,
                    desc: overcrowded.map(x => x[0]).join(', '),
                    type: 'warning'
                });
            }
            
            if (busy.length > 0) {
                insights.push({
                    title: 'Busy Depts',
                    value: busy.length,
                    desc: 'Above 70% capacity',
                    type: 'success'
                });
            }
        }
        
        // Allocation summary
        if (data && data.allocation_summary) {
            const totalStaff = data.allocation_summary.total_recommended_staff;
            if (totalStaff !== undefined) {
                insights.push({
                    title: 'Staff Required',
                    value: totalStaff,
                    desc: 'Total recommended',
                    type: 'success'
                });
            }
        }
    } catch (err) {
        console.error('Error rendering insights:', err);
    }
    
    if (insights.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">✅</div>
                <p>All systems normal</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = insights.map(insight => `
        <div class="insight-item ${insight.type} fade-in">
            <div class="insight-title">${insight.title}</div>
            <div class="insight-value">${insight.value}</div>
            <div class="insight-desc">${insight.desc}</div>
        </div>
    `).join('');
}

// Update Statistics Cards
function updateStats(data) {
    const riskDist = data.risk_distribution || {};
    const total = Object.values(riskDist).reduce((a, b) => a + b, 0);
    
    // Animate counting
    animateValue('totalPatients', total);
    animateValue('highRiskCount', riskDist.high || 0);
    animateValue('mediumRiskCount', riskDist.medium || 0);
    animateValue('lowRiskCount', riskDist.low || 0);
    
    // Check for high-risk alert
    const highRisk = riskDist.high || 0;
    const alertDiv = document.getElementById('emergencyAlert');
    const alertMsg = document.getElementById('alertMessage');
    
    if (highRisk > 5) {
        alertDiv.style.display = 'flex';
        alertMsg.textContent = `${highRisk} high-risk patients require immediate attention!`;
    } else {
        alertDiv.style.display = 'none';
    }
}

// Animate number counting
function animateValue(elementId, end) {
    const element = document.getElementById(elementId);
    const start = 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (end - start) * easeOut);
        
        element.textContent = current;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Initialize Dashboard
async function init() {
    try {
        const data = await fetchDashboardData();
        
        // Render all components
        renderRiskChart(data.risk_distribution);
        renderGaugeCharts(data.department_status);
        renderAgeChart(data.demographic_fairness?.age_groups || {});
        renderInsights(data);
        renderQueue(data.patient_list);
        updateStats(data);
        
        // Initial vitals (first patient if available)
        if (data.patient_list && data.patient_list.length > 0) {
            const firstPatient = await fetchDashboardData({ patient_id: data.patient_list[0].patient_id });
            renderVitalsRadar(firstPatient.selected_patient);
        }
        
        // Populate filter dropdowns
        populateFilters(data);
        
        // Setup event listeners
        setupEventListeners();
        
    } catch (err) {
        console.error(err);
        document.body.insertAdjacentHTML('afterbegin', `
            <div style="background:#fee;padding:12px;border-radius:6px;margin:10px;">
                Dashboard load error: ${err.message}
            </div>
        `);
    }
}

// Populate filter dropdowns
function populateFilters(data) {
    const patientSelect = document.getElementById('patientSelect');
    const deptFilter = document.getElementById('deptFilter');
    
    // Patients
    patientSelect.innerHTML = '<option value="">(Select patient)</option>';
    if (data.patient_list) {
        data.patient_list.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.patient_id;
            opt.text = `#${p.patient_id} - ${p.age || ''}y - ${p.risk_level || ''} - ${p.department || ''}`;
            patientSelect.appendChild(opt);
        });
    }
    
    // Departments
    Object.keys(data.department_status || {}).forEach(d => {
        const opt = document.createElement('option');
        opt.value = d;
        opt.text = d;
        deptFilter.appendChild(opt);
    });
}

// Setup event listeners
function setupEventListeners() {
    const patientSelect = document.getElementById('patientSelect');
    const deptFilter = document.getElementById('deptFilter');
    const riskFilter = document.getElementById('riskFilter');
    const applyBtn = document.getElementById('applyFilters');
    const editCapacityBtn = document.getElementById('editCapacityBtn');
    
    async function applyFilters() {
        const pid = patientSelect.value;
        const dept = deptFilter.value;
        const risk = riskFilter.value;
        
        const params = {};
        if (pid) params.patient_id = pid;
        if (dept) params.department = dept;
        if (risk) params.risk_level = risk;
        
        try {
            const filteredData = await fetchDashboardData(params);
            
            // Update all visualizations
            renderRiskChart(filteredData.risk_distribution);
            renderGaugeCharts(filteredData.department_status);
            renderAgeChart(filteredData.demographic_fairness?.age_groups || {});
            renderInsights(filteredData);
            renderQueue(filteredData.patient_list);
            updateStats(filteredData);
            
            // Update patient vitals if selected
            if (pid && filteredData.selected_patient) {
                renderVitalsRadar(filteredData.selected_patient);
            } else if (!pid) {
                renderVitalsRadar(null);
            }
            
        } catch (err) {
            console.error('Filter error:', err);
        }
    }
    
    applyBtn.addEventListener('click', applyFilters);
    patientSelect.addEventListener('change', applyFilters);
    
    // Add event listener for edit capacity button
    if (editCapacityBtn) {
        editCapacityBtn.addEventListener('click', showCapacityEditModal);
    }
}

// Start the dashboard
window.addEventListener('DOMContentLoaded', init);
