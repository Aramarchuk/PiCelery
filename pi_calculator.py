from decimal import Decimal, getcontext
import time
import csv
import os


def write_iteration_data(csv_file, iteration, elapsed_time, progress, remaining_time):
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(['iteration', 'elapsed_time', 'progress', 'remaining_time'])

        writer.writerow([iteration, f"{elapsed_time:.4f}", f"{progress:.4f}", f"{remaining_time:.4f}"])


def chudnovsky_pi(n_decimals, task_id=None, update_state=None):
    getcontext().prec = n_decimals + 10

    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L

    iterations = max(1, n_decimals // 14 + 2)
    csv_file = 'data.csv'

    start_time = time.time()
    last_update_time = start_time

    print(f"Starting Chudnovsky calculation: {iterations} iterations for {n_decimals} decimals")
    print(f"Iteration data will be saved to {csv_file}")

    for i in range(1, iterations + 1):
        M = (K**3 - 16*K) * M // i**3
        L += 545140134
        X *= -262537412640768000
        K += 12

        term = Decimal(M * L) / X
        S += term

        current_time = time.time()
        total_elapsed = current_time - start_time
        progress = i / iterations

        if progress > 0:
            estimated_total = total_elapsed / progress
            remaining_time = estimated_total - total_elapsed
        else:
            remaining_time = 0

        write_iteration_data(csv_file, i, total_elapsed, progress, remaining_time)

        update_frequency = 1 if iterations <= 100 else max(1, iterations // 50)

        if update_state and i % update_frequency == 0:
            elapsed_time = current_time - last_update_time

            update_state(
                state='PROGRESS',
                meta={
                    'progress': progress,
                    'task_id': task_id,
                    'iteration': i,
                    'total_iterations': iterations,
                    'elapsed_time': total_elapsed,
                    'eta': remaining_time,
                    'last_step_time': elapsed_time
                }
            )

            last_update_time = current_time

    pi_result = C / S
    total_time = time.time() - start_time

    if update_state:
        update_state(
            state='PROGRESS',
            meta={
                'progress': 0.99,
                'task_id': task_id,
                'total_time': total_time
            }
        )

    print(f"Calculation completed in {total_time:.2f} seconds")

    format_str = f"{{0:.{n_decimals}f}}"
    return format_str.format(pi_result)


def calculate_pi_with_algorithm(n_decimals, algorithm='chudnovsky', task_id=None, update_state=None):
    if algorithm != 'chudnovsky':
        raise ValueError(f"Only Chudnovsky algorithm is supported. Got: {algorithm}")

    return chudnovsky_pi(n_decimals, task_id, update_state)