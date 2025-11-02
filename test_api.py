#!/usr/bin/env python3
"""
Simple test script to demonstrate Pi Calculator API functionality
"""

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

    # Start calculation
    calc_data = {"n": n_decimals, "algorithm": algorithm}
    response = requests.post(f"{BASE_URL}/calculate_pi", json=calc_data)

    if response.status_code != 202:
        print(f"Error starting calculation: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    task_id = result["task_id"]
    print(f"Started calculation with task_id: {task_id}")

    return True

    # Monitor progress
    # while True:
    #     progress_data = {"task_id": task_id}
    #     response = requests.post(f"{BASE_URL}/check_progress", json=progress_data)
    #
    #     if response.status_code != 200:
    #         print(f"Error checking progress: {response.status_code}")
    #         return False
    #
    #     progress = response.json()
    #
    #     # Extract detailed progress information
    #     state = progress['state']
    #     progress_percent = progress['progress']
    #
    #     # Build detailed progress message
    #     progress_msg = f"State: {state}, Progress: {progress_percent:.1%}"
    #
    #     # Add detailed information if available
    #     if 'iteration' in progress and 'total_iterations' in progress:
    #         iteration = progress['iteration']
    #         total_iterations = progress['total_iterations']
    #         progress_msg += f" (Iteration {iteration}/{total_iterations})"
    #
    #     if 'last_step_time' in progress:
    #         last_step = progress['last_step_time']
    #         progress_msg += f", Last step: {last_step:.2f}s"
    #
    #     if 'elapsed_time' in progress:
    #         elapsed = progress['elapsed_time']
    #         progress_msg += f", Total: {elapsed:.1f}s"
    #
    #     if 'eta' in progress:
    #         eta = progress['eta']
    #         progress_msg += f", ETA: {eta:.1f}s"
    #
    #     print(progress_msg)
    #
    #     if state == 'FINISHED':
    #         result = progress.get('result', 'No result')
    #         # Show full result for high precision
    #         if len(result) > 50:
    #             print(f"Result: {result[:50]}...")
    #             print(f"Full length: {len(result)} characters")
    #         else:
    #             print(f"Result: {result}")
    #         break
    #     elif state == 'FAILURE':
    #         print(f"Calculation failed: {progress.get('error', 'Unknown error')}")
    #         return False
    #
    #
    # return True

def main():
    """Run all tests"""
    print("Testing Pi Calculator API with Chudnovsky algorithm...")

    # Test health
    if not test_health():
        print("Health check failed!")
        return

    # Test Chudnovsky algorithm with different precision
    test_cases = [
        (10, "Basic precision test"),
        (50, "Medium precision test"),
        (100000, "High precision test")
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