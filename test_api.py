#!/usr/bin/env python3
"""
Simple test script to demonstrate Pi Calculator API functionality
"""
import time

import requests
import os

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health check:", response.json())
    return response.status_code == 200

def test_pi_calculation(n_decimals, algorithm="chudnovsky"):
    """Test complete pi calculation workflow"""
    print(f"\n=== Testing {algorithm} algorithm with {n_decimals} decimals ===")

    calc_data = {"n": n_decimals, "algorithm": algorithm}
    response = requests.post(f"{BASE_URL}/calculate_pi", json=calc_data)

    if response.status_code != 202:
        print(f"Error starting calculation: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    task_id = result["task_id"]
    print(f"Started calculation with task_id: {task_id}")

    while True:
        progress_data = {"task_id": task_id}
        response = requests.post(f"{BASE_URL}/check_progress", json=progress_data)

        if response.status_code != 200:
            print(f"Error checking progress: {response.status_code}")
            return False

        progress = response.json()

        state = progress['state']
        progress_percent = progress['progress']

        progress_msg = f"State: {state}, Progress: {progress_percent:.1%}"

        if 'iteration' in progress and 'total_iterations' in progress:
            iteration = progress['iteration']
            total_iterations = progress['total_iterations']
            progress_msg += f" (Iteration {iteration}/{total_iterations})"

        if "msg" in progress:
            progress_msg += f", Message: {progress['meta']['msg']}"

        print(progress_msg)

        if state == 'FINISHED':
            result = progress.get('result', 'No result')
            if len(result) > 50:
                print(f"Result: {result[:50]}...")
                print(f"Full length: {len(result)} characters")
            else:
                print(f"Result: {result}")
            break
        elif state == 'FAILURE':
            print(f"Calculation failed: {progress.get('error', 'Unknown error')}")
            return False

        time.sleep(0.5)


    return True

def main():
    """Run all tests"""
    print("Testing Pi Calculator API with Chudnovsky algorithm...")

    if not test_health():
        print("Health check failed!")
        return

    test_cases = [
        (10, "Basic precision test"),
        (50, "Medium precision test"),
        (10000, "High precision test")
    ]

    for decimals, description in test_cases:
        print(f"\n--- {description} ---")
        if not test_pi_calculation(decimals, "chudnovsky"):
            print(f"Test failed for {decimals} decimals")
            return

    print("\n=== All tests completed! ===")
    print(f"API Documentation available at: {BASE_URL}/docs/")

if __name__ == "__main__":
    main()