#!/usr/bin/env python3
"""
Simple test script to demonstrate Pi Calculator API functionality
"""
import time
import math

import requests
import os

BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

# Known pi values for validation
PI_10_DIGITS = "3.1415926535"
PI_50_DIGITS = "3.14159265358979323846264338327950288419716939937510"
PI_FIRST_FEW = "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print("Health check:", response.json())
    return response.status_code == 200

def test_pi_calculation(n_decimals):
    """Test complete pi calculation workflow"""
    print(f"\n=== Testing algorithm with {n_decimals} decimals ===")

    response = requests.get(f"{BASE_URL}/calculate_pi?n={n_decimals}")

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

def test_pi_correctness(n_decimals, expected_prefix):
    """
    Unit test to verify that pi calculation is correct by comparing with known values.

    Args:
        n_decimals (int): Number of decimal places to calculate
        expected_prefix (str): Expected prefix of the pi result

    Returns:
        bool: True if calculation is correct, False otherwise
    """
    print(f"\n=== Unit Test: Verifying π correctness for {n_decimals} decimals ===")

    response = requests.get(f"{BASE_URL}/calculate_pi?n={n_decimals}")

    if response.status_code != 202:
        print(f"❌ Error starting calculation: {response.status_code}")
        return False

    result = response.json()
    task_id = result["task_id"]

    # Wait for completion
    while True:
        progress_data = {"task_id": task_id}
        response = requests.post(f"{BASE_URL}/check_progress", json=progress_data)

        if response.status_code != 200:
            print(f"❌ Error checking progress: {response.status_code}")
            return False

        progress = response.json()
        state = progress['state']

        if state == 'FINISHED':
            pi_result = progress.get('result')
            break
        elif state == 'FAILURE':
            print(f"❌ Calculation failed: {progress.get('error', 'Unknown error')}")
            return False

        time.sleep(0.5)

    # Validate the result
    if not pi_result:
        print("❌ No result returned")
        return False

    # Check if the result starts with expected prefix
    if pi_result.startswith(expected_prefix):
        print(f"✅ π calculation correct for {n_decimals} decimals")
        print(f"   Result: {pi_result[:min(50, len(pi_result))]}...")
        return True
    else:
        print(f"❌ π calculation INCORRECT for {n_decimals} decimals")
        print(f"   Expected: {expected_prefix[:53]}...")
        print(f"   Got:      {pi_result[:53]}...")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print(f"\n=== Unit Test: Testing edge cases ===")

    # Test invalid n values
    invalid_cases = [
        ("n=0", "Zero decimals"),
        ("n=-1", "Negative decimals"),
        ("n=abc", "Non-numeric decimals"),
    ]

    success_count = 0

    for param, description in invalid_cases:
        print(f"\nTesting {description}: {param}")
        response = requests.get(f"{BASE_URL}/calculate_pi?{param}")

        if response.status_code == 400:
            print(f"✅ Correctly rejected invalid input: {description}")
            success_count += 1
        else:
            print(f"❌ Should have rejected invalid input: {description}")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text}")

    # Test missing parameter
    print(f"\nTesting missing parameter")
    response = requests.get(f"{BASE_URL}/calculate_pi")

    if response.status_code == 400:
        print(f"✅ Correctly rejected missing parameter")
        success_count += 1
    else:
        print(f"❌ Should have rejected missing parameter")
        print(f"   Status code: {response.status_code}")

    return success_count == 4  # 4 invalid cases should be caught

def test_basic_functionality():
    """Test basic functionality with mathematical verification"""
    print(f"\n=== Unit Test: Basic mathematical verification ===")

    # Test with 5 decimals and verify against math.pi
    n_decimals = 5
    response = requests.get(f"{BASE_URL}/calculate_pi?n={n_decimals}")

    if response.status_code != 202:
        print(f"❌ Error starting calculation: {response.status_code}")
        return False

    result = response.json()
    task_id = result["task_id"]

    # Wait for completion
    while True:
        progress_data = {"task_id": task_id}
        response = requests.post(f"{BASE_URL}/check_progress", json=progress_data)

        if response.status_code != 200:
            print(f"❌ Error checking progress: {response.status_code}")
            return False

        progress = response.json()
        state = progress['state']

        if state == 'FINISHED':
            pi_result = progress.get('result')
            break
        elif state == 'FAILURE':
            print(f"❌ Calculation failed: {progress.get('error', 'Unknown error')}")
            return False

        time.sleep(0.5)

    # Convert to float and compare with math.pi
    try:
        calculated_pi = float(pi_result)
        math_pi = round(math.pi, n_decimals)

        if abs(calculated_pi - math_pi) < 0.5 * (10 ** -n_decimals):
            print(f"✅ Basic math verification passed")
            print(f"   Calculated: {calculated_pi}")
            print(f"   Expected:   {math_pi}")
            print(f"   Difference: {abs(calculated_pi - math_pi)}")
            return True
        else:
            print(f"❌ Basic math verification failed")
            print(f"   Calculated: {calculated_pi}")
            print(f"   Expected:   {math_pi}")
            print(f"   Difference: {abs(calculated_pi - math_pi)}")
            return False
    except ValueError as e:
        print(f"❌ Could not convert result to float: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Pi Calculator API with Chudnovsky algorithm...")

    # Health check first
    if not test_health():
        print("❌ Health check failed!")
        return

    print("✅ Health check passed!")

    # Unit tests for correctness
    print(f"\n{'='*60}")
    print("RUNNING UNIT TESTS FOR CORRECTNESS")
    print(f"{'='*60}")

    # Test known values
    correctness_tests = [
        (10, PI_10_DIGITS),
        (50, PI_50_DIGITS),
    ]

    all_correctness_passed = True
    for decimals, expected in correctness_tests:
        if not test_pi_correctness(decimals, expected):
            all_correctness_passed = False

    # Test basic mathematical verification
    if not test_basic_functionality():
        all_correctness_passed = False

    # Test edge cases and error handling
    if not test_edge_cases():
        all_correctness_passed = False

    # Integration tests (original functionality)
    print(f"\n{'='*60}")
    print("RUNNING INTEGRATION TESTS")
    print(f"{'='*60}")

    integration_test_cases = [
        (100, "Medium precision integration test"),
        (1000, "High precision integration test"),
    ]

    all_integration_passed = True
    for decimals, description in integration_test_cases:
        print(f"\n--- {description} ---")
        if not test_pi_calculation(decimals):
            print(f"❌ Integration test failed for {decimals} decimals")
            all_integration_passed = False

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    if all_correctness_passed:
        print("✅ All UNIT TESTS passed - π calculations are mathematically correct!")
    else:
        print("❌ Some UNIT TESTS failed - π calculations may be incorrect!")

    if all_integration_passed:
        print("✅ All INTEGRATION TESTS passed - API works correctly!")
    else:
        print("❌ Some INTEGRATION TESTS failed - API may have issues!")

    if all_correctness_passed and all_integration_passed:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
        print(f"API Documentation available at: {BASE_URL}/docs/")
    else:
        print(f"\n💥 SOME TESTS FAILED 💥")
        print("Please check the output above for details.")

if __name__ == "__main__":
    main()