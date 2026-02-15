"""Test script for Hugging Face API integration"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"
HF_TOKEN = "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"

# Test 1: Configure the token
print("=" * 50)
print("Test 1: Configuring Hugging Face token...")
print("=" * 50)
response = requests.post(
    f"{BASE_URL}/hf/configure",
    json={"token": HF_TOKEN}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test 2: Check status
print("=" * 50)
print("Test 2: Checking Hugging Face status...")
print("=" * 50)
response = requests.get(f"{BASE_URL}/hf/status")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
print()

# Test 3: Get embedding
print("=" * 50)
print("Test 3: Getting text embedding...")
print("=" * 50)
response = requests.post(
    f"{BASE_URL}/hf/embedding",
    json={"text": "chest pain and shortness of breath"}
)
print(f"Status: {response.status_code}")
result = response.json()
if result.get('success'):
    print(f"Embedding length: {result.get('embedding_length')}")
    print(f"First 5 values: {result.get('embedding')[:5]}")
else:
    print(f"Error: {result.get('error')}")
print()

print("=" * 50)
print("All tests completed!")
print("=" * 50)
