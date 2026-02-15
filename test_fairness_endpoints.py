"""
Test script for Phase 1 Fairness Module endpoints
"""

import requests
import json
import time

BASE_URL = 'http://127.0.0.1:5000'

def test_endpoints():
    """Test all new fairness endpoints"""
    
    print("=" * 80)
    print("PHASE 1 FAIRNESS MODULE - ENDPOINT TESTS")
    print("=" * 80)
    
    # Give Flask a moment to initialize
    time.sleep(2)
    
    endpoints = [
        ('/fairness-analysis', 'Comprehensive Fairness Analysis'),
        ('/department-fairness', 'Department-Level Fairness Analysis'),
        ('/bias-detection', 'Bias Detection Analysis'),
        ('/resource-allocation', 'Resource Allocation Analysis')
    ]
    
    for endpoint, description in endpoints:
        print(f"\n{'='*80}")
        print(f"Testing: {description}")
        print(f"Endpoint: GET {endpoint}")
        print('='*80)
        
        try:
            response = requests.get(f'{BASE_URL}{endpoint}', timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Status: {response.status_code} - SUCCESS")
                print(f"\nResponse Summary:")
                print(json.dumps(data, indent=2)[:1000] + "...\n")  # Print first 1000 chars
                
                if data.get('success'):
                    print(f"✓ Response successful: {data.get('message', 'OK')}")
                else:
                    print(f"✗ Error: {data.get('error', 'Unknown error')}")
            else:
                print(f"✗ Status: {response.status_code} - FAILED")
                print(f"Response: {response.text[:500]}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection Error: Cannot connect to Flask server at {BASE_URL}")
            print("  Make sure Flask is running: python app.py")
            return False
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    print(f"\n{'='*80}")
    print("PHASE 1 TESTING COMPLETED")
    print('='*80)
    return True

if __name__ == '__main__':
    success = test_endpoints()
    exit(0 if success else 1)
