/* 
 * AI Patient Triage System - Main JavaScript
 * Handles form submission, API calls, tabs, simulation, wearable import, and fairness analysis
 */

const API_BASE_URL = 'https://pragyan-neuranexus.onrender.com';

// Global state
let currentTab = 'triage';

// ==================== Tab Switching ====================
function switchTab(tabName) {
    currentTab = tabName;
    // Update nav tabs by `data-tab` attribute
    document.querySelectorAll('.nav-tab').forEach(tab => {
        const name = tab.dataset.tab || '';
        tab.classList.toggle('active', name === tabName);
    });

    // Show/hide tab-content sections
    document.querySelectorAll('.tab-content').forEach(content => {
        const shouldShow = content.id === (tabName + 'Tab');
        content.classList.toggle('active', shouldShow);
        content.style.display = shouldShow ? 'block' : 'none';
    });

    // Show/hide main-grid inside triageTab specifically
    const mainGrid = document.querySelector('.main-grid');
    if (mainGrid) {
        mainGrid.style.display = (tabName === 'triage') ? 'grid' : 'none';
    }

    // Load fairness data if switching to fairness tab
    if (tabName === 'fairness') {
        loadFairnessData();
    }
    
    // Load recent patients if switching to EHR tab
    if (tabName === 'ehr') {
        loadRecentPatients();
    }
}

// ==================== Load Recent Patients ====================
async function loadRecentPatients() {
    const recentListContainer = document.getElementById('recentPatientsList');
    const patientRecordContainer = document.getElementById('patientRecord');
    
    if (!recentListContainer) return;
    
    // Show loading
    recentListContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Loading recent patients...</p>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/get-recent-patients`);
        const data = await response.json();
        
        if (data.success && data.patients && data.patients.length > 0) {
            displayRecentPatients(data.patients);
            
            // Also display the first patient in the record section
            if (patientRecordContainer) {
                viewPatientRecord(data.patients[0].patient_id);
            }
        } else {
            recentListContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No recent patients found</p>';
        }
    } catch (error) {
        recentListContainer.innerHTML = '<p style="color: var(--risk-high);">Error loading recent patients: ' + error.message + '</p>';
    }
}

function displayRecentPatients(patients) {
    const recentListContainer = document.getElementById('recentPatientsList');
    
    const html = patients.map(patient => `
        <div class="patient-result-item" onclick="viewPatientRecord('${patient.patient_id}')" style="cursor: pointer; padding: 12px; border: 1px solid var(--border-color); border-radius: var(--radius-md); margin-bottom: 8px; background: var(--bg-primary);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>${patient.patient_id}</strong>
                    <span style="margin-left: 10px; color: var(--text-secondary);">${patient.age} years, ${patient.gender || 'N/A'}</span>
                </div>
                <span class="queue-risk-badge ${patient.risk_level.toLowerCase()}">${patient.risk_level}</span>
            </div>
            <div style="margin-top: 6px; font-size: 0.9em; color: var(--text-secondary);">
                <span>Department: ${patient.recommended_department}</span>
            </div>
        </div>
    `).join('');
    
    recentListContainer.innerHTML = html;
}

// ==================== Form Submission ====================
document.addEventListener('DOMContentLoaded', function() {
    const triageForm = document.getElementById('triageForm');
    if (triageForm) {
        triageForm.addEventListener('submit', handleFormSubmit);
    }
});

async function handleFormSubmit(e) {
    e.preventDefault();
    
    // Show loading
    showLoading(true);
    hideError();
    
    // Collect form data
    const formData = {
        age: parseInt(document.getElementById('age').value),
        gender: document.getElementById('gender').value,
        blood_pressure_systolic: parseInt(document.getElementById('blood_pressure_systolic').value),
        blood_pressure_diastolic: parseInt(document.getElementById('blood_pressure_diastolic').value),
        heart_rate: parseInt(document.getElementById('heart_rate').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        oxygen_saturation: parseInt(document.getElementById('oxygen_saturation').value),
        pain_level: parseInt(document.getElementById('pain_level').value),
        symptoms: document.getElementById('symptoms').value,
        pre_existing_conditions: document.getElementById('pre_conditions').value,
        patient_id: 'P_' + Date.now()
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayResults(data);
        } else {
            showError(data.error || 'An error occurred while processing the patient');
        }
    } catch (error) {
        showError('Failed to connect to the server. Please try again.');
        console.error('Error:', error);
    } finally {
        showLoading(false);
    }
}

function displayResults(data) {
    const resultSection = document.getElementById('resultSection');
    const riskScore = document.getElementById('riskScore');
    const confidenceScore = document.getElementById('confidenceScore');
    const resultIcon = document.getElementById('resultIcon');
    const resultTitle = document.getElementById('resultTitle');
    const resultMeta = document.getElementById('resultMeta');
    const recommendedDept = document.getElementById('recommendedDept');
    const deptConfidence = document.getElementById('deptConfidence');
    const explainabilityFactors = document.getElementById('explainabilityFactors');
    
    // Set risk level and styling
    const riskLevel = data.risk_level.toLowerCase();
    resultSection.className = 'result-card show ' + riskLevel;
    
    // Update stats
    riskScore.textContent = data.risk_level.toUpperCase();
    confidenceScore.textContent = data.risk_confidence;
    
    // Update result header
    const icons = {
        'high': '🚨',
        'medium': '⚠️',
        'low': '✅'
    };
    resultIcon.textContent = icons[riskLevel] || '⚠️';
    resultTitle.textContent = data.risk_level.toUpperCase() + ' RISK';
    resultMeta.textContent = 'Confidence: ' + data.risk_confidence;
    
    // Update details
    recommendedDept.textContent = data.recommended_department;
    deptConfidence.textContent = data.dept_confidence;
    
    // Display explainability factors
    if (data.explainability && data.explainability.length > 0) {
        explainabilityFactors.innerHTML = data.explainability.map(factor => `
            <div class="factor-card ${factor.contribution}">
                <div class="factor-header">
                    <span class="factor-name">${factor.factor}</span>
                    <span class="factor-badge ${factor.contribution}">${factor.contribution}</span>
                </div>
                <div class="factor-description">${factor.description}</div>
            </div>
        `).join('');
    } else {
        explainabilityFactors.innerHTML = '<p>No contributing factors identified.</p>';
    }
}

// Display results specifically in the Wearable tab UI
function displayWearableResults(data) {
    const riskScore = document.getElementById('wearableRiskScore');
    const confidenceScore = document.getElementById('wearableConfidenceScore');
    const resultIcon = document.getElementById('wearableResultIcon');
    const resultTitle = document.getElementById('wearableResultTitle');
    const resultMeta = document.getElementById('wearableResultMeta');
    const recommendedDept = document.getElementById('wearableRecommendedDept');
    const deptConfidence = document.getElementById('wearableDeptConfidence');
    const explainabilityFactors = document.getElementById('wearableExplainabilityFactors');

    const w_age = document.getElementById('w_age');
    const w_gender = document.getElementById('w_gender');
    const w_bp = document.getElementById('w_bp');
    const w_hr = document.getElementById('w_hr');
    const w_temp = document.getElementById('w_temp');
    const w_spo2 = document.getElementById('w_spo2');
    const w_pain = document.getElementById('w_pain');
    const w_symptoms = document.getElementById('w_symptoms');

    if (!riskScore) return displayResults(data); // fallback

    const riskLevel = (data.risk_level || '').toLowerCase();
    riskScore.textContent = (data.risk_level || '--').toUpperCase();
    confidenceScore.textContent = data.risk_confidence || '--';

    const icons = { 'high': '🚨', 'medium': '⚠️', 'low': '✅' };
    resultIcon.textContent = icons[riskLevel] || '⚠️';
    resultTitle.textContent = (data.risk_level || 'RISK').toUpperCase() + ' RISK';
    resultMeta.textContent = 'Confidence: ' + (data.risk_confidence || '--');

    recommendedDept.textContent = data.recommended_department || '--';
    deptConfidence.textContent = data.dept_confidence || '--';

    // Apply risk class to wearable result card for consistent styling
    const wearableResultCard = document.getElementById('wearableResultSection');
    if (wearableResultCard) {
        wearableResultCard.className = 'result-card show ' + (riskLevel || '');
        wearableResultCard.style.display = 'block';
    }

    if (data.explainability && data.explainability.length > 0) {
        explainabilityFactors.innerHTML = data.explainability.map(factor => `
            <div class="factor-card ${factor.contribution}">
                <div class="factor-header">
                    <span class="factor-name">${factor.factor}</span>
                    <span class="factor-badge ${factor.contribution}">${factor.contribution}</span>
                </div>
                <div class="factor-description">${factor.description}</div>
            </div>
        `).join('');
    } else {
        explainabilityFactors.innerHTML = '<p>No contributing factors identified.</p>';
    }

    // Ensure explainability section is visible
    const exSection = document.getElementById('wearableExplainabilityFactors');
    if (exSection) exSection.parentElement.style.display = 'block';

    // Populate patient details if provided
    const p = data.patient_data || {};
    if (w_age) w_age.textContent = p.age !== undefined ? p.age : '--';
    if (w_gender) w_gender.textContent = p.gender || '--';
    if (w_bp) w_bp.textContent = (p.blood_pressure_systolic || p.systolic_bp || '--') + '/' + (p.blood_pressure_diastolic || p.diastolic_bp || '--');
    if (w_hr) w_hr.textContent = p.heart_rate !== undefined ? p.heart_rate : (p.heartRate || '--');
    if (w_temp) w_temp.textContent = p.temperature !== undefined ? p.temperature : (p.body_temperature || '--');
    if (w_spo2) w_spo2.textContent = p.oxygen_saturation !== undefined ? p.oxygen_saturation : (p.spo2 || '--');
    if (w_pain) w_pain.textContent = p.pain_level !== undefined ? p.pain_level : '--';
    if (w_symptoms) w_symptoms.textContent = p.symptoms || '--';
}

// ==================== Loading & Error States ====================
function showLoading(show) {
    const loading = document.getElementById('loading');
    const submitBtn = document.querySelector('.btn-submit');
    
    if (loading) {
        loading.classList.toggle('show', show);
    }
    if (submitBtn) {
        submitBtn.disabled = show;
        submitBtn.textContent = show ? 'Processing...' : '🔍 Assess Risk';
    }
}

function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

function hideError() {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.classList.remove('show');
    }
}

// ==================== Logout ====================
async function handleLogout() {
    try {
        // Call server-side logout endpoint to clear Flask session
        const response = await fetch(`${API_BASE_URL}/logout`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        // Clear any stored client-side session data
        localStorage.clear();
        sessionStorage.clear();
        
        // Redirect to login page
        window.location.href = `${API_BASE_URL}/login`;
    } catch (error) {
        console.error('Logout error:', error);
        // Still try to clear local storage and redirect even if server call fails
        localStorage.clear();
        sessionStorage.clear();
        window.location.href = `${API_BASE_URL}/login`;
    }
}

// ==================== Sample Data ====================
// Array of sample patient data for testing - cycles through on each click
const samplePatients = [
    {
        age: 45,
        gender: 'male',
        blood_pressure_systolic: 145,
        blood_pressure_diastolic: 95,
        heart_rate: 95,
        temperature: 99.5,
        oxygen_saturation: 94,
        pain_level: 6,
        symptoms: 'Chest pain with shortness of breath',
        pre_conditions: 'hypertension'
    },
    {
        age: 32,
        gender: 'female',
        blood_pressure_systolic: 110,
        blood_pressure_diastolic: 70,
        heart_rate: 72,
        temperature: 98.6,
        oxygen_saturation: 98,
        pain_level: 2,
        symptoms: 'Mild headache and fatigue',
        pre_conditions: ''
    },
    {
        age: 68,
        gender: 'male',
        blood_pressure_systolic: 165,
        blood_pressure_diastolic: 100,
        heart_rate: 110,
        temperature: 101.2,
        oxygen_saturation: 88,
        pain_level: 8,
        symptoms: 'Severe chest pain radiating to arm, shortness of breath',
        pre_conditions: 'heart_disease,diabetes'
    },
    {
        age: 25,
        gender: 'female',
        blood_pressure_systolic: 105,
        blood_pressure_diastolic: 65,
        heart_rate: 80,
        temperature: 100.4,
        oxygen_saturation: 97,
        pain_level: 4,
        symptoms: 'Sore throat, cough, mild fever',
        pre_conditions: 'asthma'
    },
    {
        age: 55,
        gender: 'female',
        blood_pressure_systolic: 130,
        blood_pressure_diastolic: 85,
        heart_rate: 78,
        temperature: 98.2,
        oxygen_saturation: 96,
        pain_level: 3,
        symptoms: 'Lower back pain, stiffness in morning',
        pre_conditions: 'arthritis'
    },
    {
        age: 42,
        gender: 'male',
        blood_pressure_systolic: 155,
        blood_pressure_diastolic: 98,
        heart_rate: 90,
        temperature: 99.1,
        oxygen_saturation: 93,
        pain_level: 7,
        symptoms: 'Severe abdominal pain, nausea, dizziness',
        pre_conditions: 'hypertension'
    },
    {
        age: 29,
        gender: 'female',
        blood_pressure_systolic: 115,
        blood_pressure_diastolic: 75,
        heart_rate: 68,
        temperature: 97.8,
        oxygen_saturation: 99,
        pain_level: 1,
        symptoms: 'Minor cuts and bruises from fall',
        pre_conditions: ''
    },
    {
        age: 72,
        gender: 'male',
        blood_pressure_systolic: 140,
        blood_pressure_diastolic: 88,
        heart_rate: 65,
        temperature: 98.4,
        oxygen_saturation: 91,
        pain_level: 5,
        symptoms: 'Shortness of breath with minimal exertion, confusion',
        pre_conditions: 'copd,heart_disease'
    }
];

// Counter to track current sample index
let currentSampleIndex = -1;

function loadSampleData() {
    // Cycle to next sample (or start at 0 if this is first click)
    currentSampleIndex = (currentSampleIndex + 1) % samplePatients.length;
    
    const sample = samplePatients[currentSampleIndex];
    
    // Load the sample data into the form
    document.getElementById('age').value = sample.age;
    document.getElementById('gender').value = sample.gender;
    document.getElementById('blood_pressure_systolic').value = sample.blood_pressure_systolic;
    document.getElementById('blood_pressure_diastolic').value = sample.blood_pressure_diastolic;
    document.getElementById('heart_rate').value = sample.heart_rate;
    document.getElementById('temperature').value = sample.temperature;
    document.getElementById('oxygen_saturation').value = sample.oxygen_saturation;
    document.getElementById('pain_level').value = sample.pain_level;
    document.getElementById('symptoms').value = sample.symptoms;
    document.getElementById('pre_conditions').value = sample.pre_conditions;
}

// ==================== Voice Input ====================
function startVoiceInput() {
    // Check if browser supports Web Speech API
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = function() {
            showError('Listening... Speak your symptoms.');
            setTimeout(() => hideError(), 2000);
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('symptoms').value = transcript;
            hideError();
        };
        
        recognition.onerror = function(event) {
            showError('Voice recognition error: ' + event.error);
        };
        
        recognition.onend = function() {
            console.log('Voice recognition ended');
        };
        
        recognition.start();
    } else {
        showError('Voice input is not supported in this browser.');
    }
}

// ==================== Simulation ====================
async function runSimulation() {
    const numPatients = parseInt(document.getElementById('numPatients').value) || 10;
    const category = document.getElementById('simulationCategory').value;
    const queueElement = document.getElementById('patientQueue');
    
    // Show loading in queue
    queueElement.innerHTML = '<div class="loading show"><div class="spinner"></div><p>Running simulation...</p></div>';
    
    try {
        // First, initialize triage session
        const initResponse = await fetch(`${API_BASE_URL}/init-triage-session`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!initResponse.ok) throw new Error('Failed to initialize session');
        
        // Generate random patients
        const patients = generateRandomPatients(numPatients);
        
        // Send batch to triage
        const response = await fetch(`${API_BASE_URL}/triage-batch-stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patients: patients })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displaySimulationResults(data.results, category);
        } else {
            queueElement.innerHTML = '<p style="color: var(--risk-high);">Error: ' + (data.error || 'Simulation failed') + '</p>';
        }
    } catch (error) {
        queueElement.innerHTML = '<p style="color: var(--risk-high);">Error: ' + error.message + '</p>';
    }
}

function generateRandomPatients(count) {
    const patients = [];
    const symptoms = [
        'chest_pain', 'shortness_of_breath', 'headache', 'abdominal_pain',
        'cough', 'fatigue', 'sore_throat', 'dizziness', 'back_pain'
    ];
    const genders = ['male', 'female'];
    const conditions = ['', 'diabetes', 'hypertension', 'heart_disease', 'asthma'];
    
    for (let i = 0; i < count; i++) {
        const age = Math.floor(Math.random() * 60) + 20;
        patients.push({
            patient_id: 'P_SIM_' + (i + 1),
            age: age,
            gender: genders[Math.floor(Math.random() * genders.length)],
            blood_pressure_systolic: Math.floor(Math.random() * 60) + 100,
            blood_pressure_diastolic: Math.floor(Math.random() * 30) + 60,
            heart_rate: Math.floor(Math.random() * 60) + 60,
            temperature: Math.floor(Math.random() * 4) + 97,
            oxygen_saturation: Math.floor(Math.random() * 10) + 90,
            pain_level: Math.floor(Math.random() * 10) + 1,
            symptoms: symptoms[Math.floor(Math.random() * symptoms.length)],
            pre_existing_conditions: conditions[Math.floor(Math.random() * conditions.length)]
        });
    }
    
    return patients;
}

function displaySimulationResults(results, filter) {
    const queueElement = document.getElementById('patientQueue');
    
    // Filter results if needed
    let filteredResults = results;
    if (filter !== 'all') {
        filteredResults = results.filter(p => {
            if (filter === 'high' || filter === 'medium' || filter === 'low') {
                return p.risk_level === filter;
            }
            return p.assigned_department === filter;
        });
    }
    
    if (filteredResults.length === 0) {
        queueElement.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No patients match the selected filter.</p>';
        return;
    }
    
    queueElement.innerHTML = filteredResults.map(patient => `
        <div class="queue-item priority-${patient.risk_level}">
            <div>
                <span class="queue-patient-id">${patient.patient_id}</span>
                <span class="queue-dept"> → ${patient.assigned_department}</span>
            </div>
            <span class="queue-risk-badge ${patient.risk_level}">${patient.risk_level.toUpperCase()}</span>
        </div>
    `).join('');
}

// ==================== Wearable Import ====================
async function importWearableData() {
    const wearableJson = document.getElementById('wearableJson').value;
    
    if (!wearableJson.trim()) {
        showError('Please enter JSON data');
        return;
    }
    
    try {
        const wearableData = JSON.parse(wearableJson);
        
        const response = await fetch(`${API_BASE_URL}/wearable-import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                wearable_data: wearableData,
                gender: wearableData.gender || '',
                pre_existing_conditions: wearableData.pre_existing_conditions || ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Keep user on the Wearable tab and display results there
            try { switchTab('wearable'); } catch (e) { /* ignore if not defined */ }
            displayWearableResults({
                patient_data: data.patient_data || {},
                risk_level: data.risk_level,
                risk_confidence: data.risk_confidence || '85%',
                recommended_department: data.recommended_department,
                dept_confidence: data.dept_confidence || '80%',
                explainability: data.explainability || [
                    { factor: 'Wearable Import', contribution: 'low', description: 'Data imported from wearable device' }
                ]
            });
            showError('');
        } else {
            showError(data.error || 'Failed to import wearable data');
        }
    } catch (error) {
        showError('Invalid JSON format');
    }
}

// ==================== Wearable Sample Data ====================
// Array of sample wearable data for testing - cycles through on each click
const wearableSamples = [
    {
        "age": 52,
        "gender": "male",
        "heart_rate": 78,
        "systolic_bp": 135,
        "diastolic_bp": 85,
        "body_temperature": 98.4,
        "spo2": 97,
        "pain_level": 3,
        "symptoms": "routine_checkup",
        "patient_id": "W_001",
        "description": "Routine checkup - healthy vitals"
    },
    {
        "age": 45,
        "gender": "female",
        "heart_rate": 95,
        "systolic_bp": 145,
        "diastolic_bp": 92,
        "body_temperature": 99.2,
        "spo2": 94,
        "pain_level": 5,
        "symptoms": "chest_discomfort",
        "patient_id": "W_002",
        "description": "Elevated heart rate and blood pressure"
    },
    {
        "age": 68,
        "gender": "male",
        "heart_rate": 110,
        "systolic_bp": 165,
        "diastolic_bp": 98,
        "body_temperature": 101.5,
        "spo2": 88,
        "pain_level": 8,
        "symptoms": "shortness_of_breath,chest_pain",
        "patient_id": "W_003",
        "description": "High risk - cardiac emergency symptoms"
    },
    {
        "age": 32,
        "gender": "female",
        "heart_rate": 72,
        "systolic_bp": 110,
        "diastolic_bp": 70,
        "body_temperature": 98.6,
        "spo2": 99,
        "pain_level": 1,
        "symptoms": "minor_headache",
        "patient_id": "W_004",
        "description": "Healthy young adult - minor symptoms"
    },
    {
        "age": 55,
        "gender": "male",
        "heart_rate": 88,
        "systolic_bp": 140,
        "diastolic_bp": 90,
        "body_temperature": 99.0,
        "spo2": 95,
        "pain_level": 4,
        "symptoms": "fatigue,mild_cough",
        "patient_id": "W_005",
        "description": "Middle aged - mild respiratory symptoms"
    },
    {
        "age": 72,
        "gender": "female",
        "heart_rate": 65,
        "systolic_bp": 128,
        "diastolic_bp": 82,
        "body_temperature": 97.8,
        "spo2": 92,
        "pain_level": 3,
        "symptoms": "dizziness,fatigue",
        "patient_id": "W_006",
        "description": "Senior citizen - slightly low oxygen"
    },
    {
        "age": 28,
        "gender": "male",
        "heart_rate": 82,
        "systolic_bp": 118,
        "diastolic_bp": 76,
        "body_temperature": 98.2,
        "spo2": 98,
        "pain_level": 2,
        "symptoms": "sore_throat",
        "patient_id": "W_007",
        "description": "Young adult - throat infection"
    },
    {
        "age": 63,
        "gender": "female",
        "heart_rate": 78,
        "systolic_bp": 155,
        "diastolic_bp": 95,
        "body_temperature": 98.8,
        "spo2": 96,
        "pain_level": 6,
        "symptoms": "back_pain,chest_discomfort",
        "patient_id": "W_008",
        "description": "Hypertension with chronic pain"
    },
    {
        "age": 41,
        "gender": "male",
        "heart_rate": 68,
        "systolic_bp": 125,
        "diastolic_bp": 80,
        "body_temperature": 97.6,
        "spo2": 99,
        "pain_level": 0,
        "symptoms": "no_symptoms",
        "patient_id": "W_009",
        "description": "Perfect health - no symptoms"
    },
    {
        "age": 58,
        "gender": "female",
        "heart_rate": 102,
        "systolic_bp": 138,
        "diastolic_bp": 88,
        "body_temperature": 100.2,
        "spo2": 93,
        "pain_level": 7,
        "symptoms": "abdominal_pain,nausea",
        "patient_id": "W_010",
        "description": "GI issues - elevated vitals"
    }
];

// Counter to track current wearable sample index
let currentWearableSampleIndex = -1;

function loadSampleWearableData() {
    // Cycle to next sample (or start at 0 if this is first click)
    currentWearableSampleIndex = (currentWearableSampleIndex + 1) % wearableSamples.length;
    
    const sample = wearableSamples[currentWearableSampleIndex];
    
    // Remove description and patient_id from the JSON (not needed for API)
    const { description, patient_id, ...dataForApi } = sample;
    
    document.getElementById('wearableJson').value = JSON.stringify(dataForApi, null, 2);
    
    // Show sample info if there's a description element
    const infoElement = document.getElementById('wearableSampleInfo');
    if (infoElement) {
        infoElement.textContent = `Sample ${currentWearableSampleIndex + 1} of ${wearableSamples.length}: ${description}`;
    }
}

function loadPreviousWearableSample() {
    currentWearableSampleIndex = (currentWearableSampleIndex - 1 + wearableSamples.length) % wearableSamples.length;
    
    const sample = wearableSamples[currentWearableSampleIndex];
    
    // Remove description and patient_id from the JSON (not needed for API)
    const { description, patient_id, ...dataForApi } = sample;
    
    document.getElementById('wearableJson').value = JSON.stringify(dataForApi, null, 2);
    
    // Show sample info
    const infoElement = document.getElementById('wearableSampleInfo');
    if (infoElement) {
        infoElement.textContent = `Sample ${currentWearableSampleIndex + 1} of ${wearableSamples.length}: ${description}`;
    }
}

function loadNextWearableSample() {
    loadSampleWearableData();
}

// ==================== Fairness Analysis ====================
async function loadFairnessData() {
    const fairnessContainer = document.getElementById('fairnessData');
    if (!fairnessContainer) return;
    
    fairnessContainer.innerHTML = '<div class="loading show"><div class="spinner"></div><p>Loading fairness analysis...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/fairness-analysis`);
        const data = await response.json();
        
        if (data.success) {
            displayFairnessData(data);
        } else {
            fairnessContainer.innerHTML = '<p style="color: var(--risk-high);">Error: ' + (data.error || 'Failed to load fairness data') + '</p>';
        }
    } catch (error) {
        fairnessContainer.innerHTML = '<p style="color: var(--risk-high);">Error: ' + error.message + '</p>';
    }
}

function displayFairnessData(data) {
    const container = document.getElementById('fairnessData');
    if (!container) return;
    
    const ageGroups = data.demographic_fairness.age_groups;
    
    let html = '<div class="fairness-container">';
    
    for (const [groupName, groupData] of Object.entries(ageGroups)) {
        const highPct = groupData.high_risk_percentage;
        const totalCount = groupData.count;
        const riskDist = groupData.risk_distribution;
        
        const highCount = riskDist.high || 0;
        const mediumCount = riskDist.medium || 0;
        const lowCount = riskDist.low || 0;
        const total = highCount + mediumCount + lowCount;
        
        const highWidth = total > 0 ? (highCount / total * 100) : 0;
        const mediumWidth = total > 0 ? (mediumCount / total * 100) : 0;
        const lowWidth = total > 0 ? (lowCount / total * 100) : 0;
        
        const riskBadgeClass = highPct > 30 ? 'high' : (highPct > 15 ? 'medium' : 'low');
        
        html += `
            <div class="age-group-card">
                <div class="age-group-header">
                    <span class="age-group-title">${groupName}</span>
                    <div class="age-group-stats">
                        <span class="patient-count">${totalCount} patients</span>
                        <span class="high-risk-badge ${riskBadgeClass}">${highPct}% high risk</span>
                    </div>
                </div>
                <div class="stacked-bar-container">
                    <div class="stacked-segment high" style="width: ${highWidth}%">${highWidth > 10 ? highCount : ''}</div>
                    <div class="stacked-segment medium" style="width: ${mediumWidth}%">${mediumWidth > 10 ? mediumCount : ''}</div>
                    <div class="stacked-segment low" style="width: ${lowWidth}%">${lowWidth > 10 ? lowCount : ''}</div>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    
    // Add fairness metrics if available
    if (data.fairness_metrics) {
        const metrics = data.fairness_metrics;
        html += '<div style="margin-top: 20px; padding: 16px; background: var(--bg-primary); border-radius: var(--radius-md);">';
        html += '<h4 style="margin-bottom: 10px;">Fairness Metrics</h4>';
        
        if (metrics.age_statistical_parity_difference !== undefined) {
            html += `<p><strong>Age SPD:</strong> ${metrics.age_statistical_parity_difference} (${metrics.age_disparity_assessment})</p>`;
        }
        if (metrics.gender_disparate_impact_ratio !== undefined) {
            html += `<p><strong>Gender DI:</strong> ${metrics.gender_disparate_impact_ratio} (${metrics.gender_disparity_assessment})</p>`;
        }
        
        html += '</div>';
    }
    
    container.innerHTML = html;
}

// ==================== Patient Search ====================
async function searchPatient() {
    const searchQuery = document.getElementById('ehrPatientSearch').value.trim();
    const resultsContainer = document.getElementById('patientSearchResults');
    
    if (!searchQuery) {
        resultsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Please enter a Patient ID or Name to search</p>';
        return;
    }
    
    // Show loading
    resultsContainer.innerHTML = '<div class="loading show"><div class="spinner"></div><p>Searching patients...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/search-patient`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: searchQuery })
        });
        
        const data = await response.json();
        
        if (data.success && data.patients && data.patients.length > 0) {
            displayPatientSearchResults(data.patients);
        } else {
            resultsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No patients found matching "' + searchQuery + '"</p>';
        }
    } catch (error) {
        resultsContainer.innerHTML = '<p style="color: var(--risk-high);">Error searching patients: ' + error.message + '</p>';
    }
}

function displayPatientSearchResults(patients) {
    const resultsContainer = document.getElementById('patientSearchResults');
    
    // Display full detailed records for each patient
    const html = patients.map(patient => {
        const riskLevel = patient.risk_level ? patient.risk_level.toLowerCase() : 'medium';
        const riskBadgeClass = riskLevel === 'high' ? 'high' : (riskLevel === 'medium' ? 'medium' : 'low');
        
        return `
        <div class="patient-record-full" style="padding: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-md); margin-bottom: 16px; background: var(--bg-primary);">
            <div class="patient-record-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
                <div>
                    <h3 style="margin: 0; font-size: 1.4em;">${patient.patient_id}</h3>
                    <p style="margin: 5px 0 0 0; color: var(--text-secondary);">${patient.age} years old, ${patient.gender || 'N/A'}</p>
                </div>
                <span class="queue-risk-badge ${riskBadgeClass}" style="font-size: 1.1em; padding: 6px 14px;">${patient.risk_level || 'N/A'} RISK</span>
            </div>
            
            <div class="patient-record-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                <div class="record-section">
                    <h4 style="margin-bottom: 8px; font-size: 1em;">Vital Signs</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 0.9em;">
                        <div><span style="color: var(--text-secondary);">BP:</span> <strong>${patient.blood_pressure_systolic || 0}/${patient.blood_pressure_diastolic || 0} mmHg</strong></div>
                        <div><span style="color: var(--text-secondary);">HR:</span> <strong>${patient.heart_rate || 0} bpm</strong></div>
                        <div><span style="color: var(--text-secondary);">Temp:</span> <strong>${patient.temperature || 0}°F</strong></div>
                        <div><span style="color: var(--text-secondary);">SpO2:</span> <strong>${patient.oxygen_saturation || 0}%</strong></div>
                        <div><span style="color: var(--text-secondary);">Pain:</span> <strong>${patient.pain_level || 0}/10</strong></div>
                    </div>
                </div>
                
                <div class="record-section">
                    <h4 style="margin-bottom: 8px; font-size: 1em;">Assessment</h4>
                    <div style="display: grid; gap: 6px; font-size: 0.9em;">
                        <div><span style="color: var(--text-secondary);">Department:</span> <strong>${patient.recommended_department || 'N/A'}</strong></div>
                        <div><span style="color: var(--text-secondary);">Symptoms:</span> <strong>${patient.symptoms || 'N/A'}</strong></div>
                        <div><span style="color: var(--text-secondary);">Conditions:</span> <strong>${patient.pre_existing_conditions || 'None'}</strong></div>
                    </div>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    resultsContainer.innerHTML = html;
}

async function viewPatientRecord(patientId) {
    const recordContainer = document.getElementById('patientRecord');
    
    if (!patientId) {
        recordContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">Select a patient to view their complete health record</p>';
        return;
    }
    
    // Show loading
    recordContainer.innerHTML = '<div class="loading show"><div class="spinner"></div><p>Loading patient record...</p></div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/get-patient-record`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ patient_id: patientId })
        });
        
        const data = await response.json();
        
        if (data.success && data.patient) {
            displayPatientRecord(data.patient);
        } else {
            recordContainer.innerHTML = '<p style="text-align: center; color: var(--risk-high);">Patient record not found</p>';
        }
    } catch (error) {
        recordContainer.innerHTML = '<p style="color: var(--risk-high);">Error loading patient record: ' + error.message + '</p>';
    }
}

function displayPatientRecord(patient) {
    const recordContainer = document.getElementById('patientRecord');
    
    const riskLevel = patient.risk_level ? patient.risk_level.toLowerCase() : 'medium';
    const riskBadgeClass = riskLevel === 'high' ? 'high' : (riskLevel === 'medium' ? 'medium' : 'low');
    
    const html = `
        <div class="patient-record-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid var(--border-color);">
            <div>
                <h3 style="margin: 0; font-size: 1.5em;">${patient.patient_id}</h3>
                <p style="margin: 5px 0 0 0; color: var(--text-secondary);">${patient.age} years old, ${patient.gender || 'N/A'}</p>
            </div>
            <span class="queue-risk-badge ${riskBadgeClass}" style="font-size: 1.2em; padding: 8px 16px;">${patient.risk_level || 'N/A'} RISK</span>
        </div>
        
        <div class="patient-record-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
            <div class="record-section">
                <h4 style="margin-bottom: 10px;">Vital Signs</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div><span style="color: var(--text-secondary);">Blood Pressure:</span> <strong>${patient.blood_pressure_systolic}/${patient.blood_pressure_diastolic} mmHg</strong></div>
                    <div><span style="color: var(--text-secondary);">Heart Rate:</span> <strong>${patient.heart_rate} bpm</strong></div>
                    <div><span style="color: var(--text-secondary);">Temperature:</span> <strong>${patient.temperature}°F</strong></div>
                    <div><span style="color: var(--text-secondary);">Oxygen Saturation:</span> <strong>${patient.oxygen_saturation}%</strong></div>
                    <div><span style="color: var(--text-secondary);">Pain Level:</span> <strong>${patient.pain_level}/10</strong></div>
                </div>
            </div>
            
            <div class="record-section">
                <h4 style="margin-bottom: 10px;">Assessment</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                    <div><span style="color: var(--text-secondary);">Department:</span> <strong>${patient.recommended_department || 'N/A'}</strong></div>
                    <div><span style="color: var(--text-secondary);">Symptoms:</span> <strong>${patient.symptoms || 'N/A'}</strong></div>
                    <div><span style="color: var(--text-secondary);">Conditions:</span> <strong>${patient.pre_existing_conditions || 'None'}</strong></div>
                </div>
            </div>
        </div>
    `;
    
    recordContainer.innerHTML = html;
}

// ==================== File Upload Handler ====================
async function handleFileUpload(event) {
    const fileInput = event.target;
    const file = fileInput.files[0];
    
    if (!file) {
        return;
    }
    
    // Show loading
    showLoading(true);
    hideError();
    
    // Validate file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 
                         'image/jpeg', 'image/png', 'image/jpg'];
    
    if (!allowedTypes.includes(file.type)) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid File Type',
            text: 'Please upload a PDF, DOCX, JPG, or PNG file.',
            confirmButtonColor: '#d33'
        });
        showLoading(false);
        return;
    }
    
    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        Swal.fire({
            icon: 'error',
            title: 'File Too Large',
            text: 'Maximum file size is 10MB. Please upload a smaller file.',
            confirmButtonColor: '#d33'
        });
        showLoading(false);
        return;
    }
    
    // Show loading with SweetAlert
    Swal.fire({
        title: 'Uploading...',
        text: 'Please wait while we process your document',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload-document`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close loading dialog
            Swal.close();
            
            // If patient data was extracted, populate the form
            if (data.patient_data) {
                populateFormWithPatientData(data.patient_data);
                Swal.fire({
                    icon: 'success',
                    title: 'Patient Data Extracted',
                    text: 'Patient data has been extracted from the document and populated in the form.',
                    confirmButtonColor: '#3085d6',
                    timer: 3000
                });
            } else if (data.message) {
                Swal.fire({
                    icon: 'info',
                    title: 'Document Processed',
                    text: data.message,
                    confirmButtonColor: '#3085d6',
                    timer: 3000
                });
            }
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Processing Failed',
                text: data.error || 'Failed to process document',
                confirmButtonColor: '#d33'
            });
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Upload Failed',
            text: 'Failed to upload document: ' + error.message,
            confirmButtonColor: '#d33'
        });
        console.error('Upload error:', error);
    } finally {
        showLoading(false);
        // Reset file input
        fileInput.value = '';
    }
}

function populateFormWithPatientData(patientData) {
    // Map extracted data to form fields
    if (patientData.age) {
        document.getElementById('age').value = patientData.age;
    }
    if (patientData.gender) {
        document.getElementById('gender').value = patientData.gender.toLowerCase();
    }
    if (patientData.blood_pressure_systolic) {
        document.getElementById('blood_pressure_systolic').value = patientData.blood_pressure_systolic;
    }
    if (patientData.blood_pressure_diastolic) {
        document.getElementById('blood_pressure_diastolic').value = patientData.blood_pressure_diastolic;
    }
    if (patientData.heart_rate) {
        document.getElementById('heart_rate').value = patientData.heart_rate;
    }
    if (patientData.temperature) {
        document.getElementById('temperature').value = patientData.temperature;
    }
    if (patientData.oxygen_saturation) {
        document.getElementById('oxygen_saturation').value = patientData.oxygen_saturation;
    }
    if (patientData.pain_level !== undefined && patientData.pain_level !== null) {
        document.getElementById('pain_level').value = patientData.pain_level;
    }
    if (patientData.symptoms) {
        document.getElementById('symptoms').value = patientData.symptoms;
    }
    if (patientData.pre_existing_conditions) {
        // Try to match with existing conditions
        const conditionsSelect = document.getElementById('pre_conditions');
        const conditionValue = patientData.pre_existing_conditions.toLowerCase().replace(/\s+/g, '_');
        
        // Check if the condition matches any option
        let found = false;
        for (let option of conditionsSelect.options) {
            if (option.value && conditionValue.includes(option.value.toLowerCase())) {
                conditionsSelect.value = option.value;
                found = true;
                break;
            }
        }
        if (!found) {
            // Set as custom value if no match
            conditionsSelect.value = patientData.pre_existing_conditions;
        }
    }
}

// Export functions for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        switchTab,
        handleFormSubmit,
        loadSampleData,
        startVoiceInput,
        runSimulation,
        importWearableData,
        loadFairnessData,
        searchPatient,
        viewPatientRecord,
        handleFileUpload,
        populateFormWithPatientData
    };
}
