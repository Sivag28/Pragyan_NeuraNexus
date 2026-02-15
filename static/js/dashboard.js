// Backend API URL
const API_BASE_URL = 'https://pragyan-neuranexus.onrender.com';

async function fetchDashboardData(params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = `${API_BASE_URL}/dashboard-data` + (qs ? `?${qs}` : '');
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load dashboard data: ' + (await res.text()));
    return res.json();
}

function renderPie(ctx, labels, values, colors) {
    return new Chart(ctx, {
        type: 'pie',
        data: { labels, datasets: [{ data: values, backgroundColor: colors }] },
        options: { responsive: true }
    });
}

function renderBar(ctx, labels, values, label) {
    return new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label, data: values, backgroundColor: 'rgba(102,126,234,0.8)' }] },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
}

function formatInsights(data) {
    const el = document.getElementById('insights');
    const lines = [];

    // Fairness metrics
    if (data.fairness_metrics) {
        if (data.fairness_metrics.age_statistical_parity_difference !== undefined) {
            lines.push(`<p><strong>Age SPD:</strong> ${data.fairness_metrics.age_statistical_parity_difference}% (${data.fairness_metrics.age_disparity_assessment})</p>`);
        }
        if (data.fairness_metrics.gender_disparate_impact_ratio !== undefined) {
            lines.push(`<p><strong>Gender DI Ratio:</strong> ${data.fairness_metrics.gender_disparate_impact_ratio} (${data.fairness_metrics.gender_disparity_assessment})</p>`);
        }
    }

    // Department top issues
    if (data.department_status) {
        const overcrowded = Object.entries(data.department_status).filter(([k,v]) => (v.utilization_percentage || 0) > 100);
        if (overcrowded.length) {
            lines.push(`<p style="color:#c33"><strong>Overcrowded:</strong> ${overcrowded.map(x=>x[0]).join(', ')}</p>`);
        } else {
            lines.push('<p><strong>No critical overcrowding detected</strong></p>');
        }
    }

    // Resource recommendations summary
    if (data.allocation_summary) {
        lines.push(`<p><strong>Total recommended staff:</strong> ${data.allocation_summary.total_recommended_staff}</p>`);
    }

    el.innerHTML = lines.join('\n');
}

async function init() {
    try {
        const data = await fetchDashboardData();

        // Risk chart
        const riskLabels = Object.keys(data.risk_distribution || {});
        const riskValues = riskLabels.map(l => data.risk_distribution[l]);
        const riskColors = ['#48c6ef', '#f093fb', '#fa709a'];
        renderPie(document.getElementById('riskChart').getContext('2d'), riskLabels, riskValues, riskColors);

        // Department utilization chart (top 10)
        const deptEntries = Object.entries(data.department_status || {}).sort((a,b)=> b[1].utilization_percentage - a[1].utilization_percentage).slice(0,10);
        const deptLabels = deptEntries.map(e=>e[0]);
        const deptValues = deptEntries.map(e=>e[1].utilization_percentage);
        renderBar(document.getElementById('deptChart').getContext('2d'), deptLabels, deptValues, 'Utilization %');

        // Age high-risk percentage
        const ageGroups = data.demographic_fairness?.age_groups || {};
        const ageLabels = Object.keys(ageGroups);
        const ageValues = ageLabels.map(k => ageGroups[k].high_risk_percentage || 0);
        renderBar(document.getElementById('ageChart').getContext('2d'), ageLabels, ageValues, 'High-risk %');

        formatInsights(data);

        // Populate patient select and department filter
        const patientSelect = document.getElementById('patientSelect');
        const deptFilter = document.getElementById('deptFilter');
        const riskFilter = document.getElementById('riskFilter');
        patientSelect.innerHTML = '<option value="">(Select patient)</option>';
        if (data.patient_list) {
            data.patient_list.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.patient_id;
                opt.text = `${p.patient_id} — ${p.age || ''}y — ${p.risk_level || ''} — ${p.department || ''}`;
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

        // When a patient is selected or filters applied, fetch targeted data
        async function applySelection() {
            const pid = patientSelect.value;
            const dept = deptFilter.value;
            const risk = riskFilter.value;
            const sel = {};
            if (pid) sel.patient_id = pid;
            if (dept) sel.department = dept;
            if (risk) sel.risk_level = risk;
            const selData = await fetchDashboardData(sel);
            // update insights and patient vitals
            formatInsights(selData);
            renderPatientVitals(selData.selected_patient);
        }

        document.getElementById('applyFilters').addEventListener('click', applySelection);
        patientSelect.addEventListener('change', applySelection);

        // initial empty patient vitals
        renderPatientVitals(data.selected_patient);
    } catch (err) {
        console.error(err);
        document.body.insertAdjacentHTML('afterbegin', `<div style="background:#fee;padding:12px;border-radius:6px;margin:10px;">Dashboard load error: ${err.message}</div>`);
    }
}

window.addEventListener('DOMContentLoaded', init);

function renderPatientVitals(patient) {
    const ctx = document.getElementById('patientVitalsChart').getContext('2d');
    if (!patient) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return;
    }
    const labels = ['Systolic', 'Diastolic', 'Heart Rate', 'Temperature', 'O2 Saturation', 'Pain Level'];
    const values = [patient.blood_pressure_systolic || 0, patient.blood_pressure_diastolic || 0, patient.heart_rate || 0, patient.temperature || 0, patient.oxygen_saturation || 0, patient.pain_level || 0];
    // Destroy previous chart if present
    if (window._patientVitalsChart) window._patientVitalsChart.destroy();
    window._patientVitalsChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets: [{ label: `Patient ${patient.patient_id} Vitals`, data: values, backgroundColor: 'rgba(59,130,246,0.8)' }] },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
}
