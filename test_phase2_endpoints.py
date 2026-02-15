"""
Test script for Phase 2 Real-Time Triage Simulation endpoints
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

def test_phase2_endpoints():
    """Test all Phase 2 real-time triage simulation endpoints"""
    
    print("=" * 80)
    print("PHASE 2 REAL-TIME TRIAGE SIMULATION - ENDPOINT TESTS")
    print("=" * 80)
    
    time.sleep(2)
    
    # 1. Initialize triage session
    print(f"\n{'='*80}")
    print("1. Initialize Triage Session")
    print('='*80)
    
    try:
        response = requests.post(f'{BASE_URL}/init-triage-session', json={})
        
        if response.status_code == 200:
            data = response.json()
            session_id = data.get('session_id')
            print(f"✓ Session initialized: {session_id}")
        else:
            print(f"✗ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False
    
    # 2. Triage individual patients
    print(f"\n{'='*80}")
    print("2. Triage Individual Patients")
    print('='*80)
    
    test_patients = [
        {
            'patient_id': 'P001',
            'age': 75,
            'blood_pressure_systolic': 160,
            'blood_pressure_diastolic': 95,
            'heart_rate': 92,
            'temperature': 98.6,
            'oxygen_saturation': 94,
            'pain_level': 8
        },
        {
            'patient_id': 'P002',
            'age': 45,
            'blood_pressure_systolic': 120,
            'blood_pressure_diastolic': 80,
            'heart_rate': 70,
            'temperature': 98.6,
            'oxygen_saturation': 98,
            'pain_level': 3
        },
        {
            'patient_id': 'P003',
            'age': 60,
            'blood_pressure_systolic': 130,
            'blood_pressure_diastolic': 85,
            'heart_rate': 88,
            'temperature': 99.5,
            'oxygen_saturation': 96,
            'pain_level': 5
        }
    ]
    
    triaged_patients = []
    for patient in test_patients:
        try:
            response = requests.post(f'{BASE_URL}/triage-patient', json=patient)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {data['patient_id']}: {data['risk_level']} risk → {data['assigned_department']}")
                print(f"  Queue position: {data['queue_position']}, Est. wait: {data['estimated_wait_time_minutes']} min")
                triaged_patients.append(data)
            else:
                print(f"✗ Failed to triage {patient['patient_id']}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    # 3. Get department status
    print(f"\n{'='*80}")
    print("3. Department Status")
    print('='*80)
    
    try:
        response = requests.get(f'{BASE_URL}/department-status')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total patients in system: {data['total_patients_in_system']}")
            print(f"\nDepartment Status:")
            
            for dept, status in data['department_status'].items():
                print(f"\n  {dept}:")
                print(f"    Status: {status['status']}")
                print(f"    Utilization: {status['utilization_percentage']}%")
                print(f"    Patients: {status['high_risk_count']} high-risk, {status['medium_risk_count']} medium, {status['low_risk_count']} low")
                print(f"    Est. wait: {status['estimated_wait_time_minutes']} min")
                if status['warning']:
                    print(f"    ⚠️  WARNING: {status['warning']}")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 4. Get prioritized queues
    print(f"\n{'='*80}")
    print("4. Prioritized Queue (Emergency Department)")
    print('='*80)
    
    try:
        response = requests.get(f'{BASE_URL}/queue-priority?department=Emergency')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total in Emergency queue: {data['total_in_queue']}")
            print(f"\nTop prioritized patients:")
            
            for patient in data['prioritized_queue'][:5]:
                print(f"  {patient['position']}. {patient['patient_id']}: {patient['risk_level']} risk")
                print(f"     Priority score: {patient['priority_score']}, Wait time: {patient['wait_time_minutes']} min")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 5. Test batch streaming
    print(f"\n{'='*80}")
    print("5. Batch Stream Processing")
    print('='*80)
    
    batch_patients = [
        {
            'patient_id': f'BATCH_{i}',
            'age': 40 + i * 5,
            'blood_pressure_systolic': 120 + i * 2,
            'blood_pressure_diastolic': 80 + i * 1,
            'heart_rate': 70 + i * 3,
            'temperature': 98.6,
            'oxygen_saturation': 98 - i,
            'pain_level': i % 3
        }
        for i in range(5)
    ]
    
    try:
        response = requests.post(f'{BASE_URL}/triage-batch-stream', 
                                json={'patients': batch_patients})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Processed {data['patients_processed']} patients in batch")
            
            for result in data['results'][:3]:
                print(f"  {result['patient_id']}: {result['risk_level']} → {result['assigned_department']}")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    # 6. Resource utilization
    print(f"\n{'='*80}")
    print("6. Resource Utilization Metrics")
    print('='*80)
    
    try:
        response = requests.get(f'{BASE_URL}/resource-utilization')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Total patients: {data['total_patients_in_system']}")
            print(f"  Avg utilization: {data['average_utilization_percentage']}%")
            print(f"  System efficiency score: {data['system_efficiency_score']}")
            
            print(f"\nTop 3 most utilized departments:")
            sorted_depts = sorted(
                data['utilization_metrics'].items(),
                key=lambda x: x[1]['utilization_percentage'],
                reverse=True
            )
            
            for dept, metrics in sorted_depts[:3]:
                print(f"  {dept}: {metrics['utilization_percentage']}% utilization, "
                      f"Weighted: {metrics['weighted_utilization_percentage']}%")
        else:
            print(f"✗ Failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
    
    print(f"\n{'='*80}")
    print("PHASE 2 TESTING COMPLETED")
    print('='*80)
    return True

if __name__ == '__main__':
    success = test_phase2_endpoints()
    exit(0 if success else 1)
