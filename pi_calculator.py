import json
from decimal import Decimal, getcontext
from typing import Optional, Callable
import time

from logariphmic_aproximation import predict


def calculate_pi(
    n_decimals: int,
    task_id: Optional[str] = None,
    update_state: Optional[Callable] = None
) -> str:
    getcontext().prec = n_decimals + 10

    C = 426880 * Decimal(10005).sqrt()
    M = 1
    L = 13591409
    X = 1
    K = 6
    S = L

    iterations = max(1, n_decimals // 14 + 2)

    start_time = time.time()

    print(f"Starting Chudnovsky calculation: {iterations} iterations for {n_decimals} decimals")

    parametrs = json.load(open('approximation_params.json', 'r'))
    a = parametrs['a']['value']
    b = parametrs['b']['value']

    update_frequency = 1 if iterations <= 1000 else max(1, iterations // 1000)
    total_estimated = predict(a, b, iterations)

    for i in range(1, iterations + 1):
        M = (K**3 - 16*K) * M // i**3
        L += 545140134
        X *= -262537412640768000
        K += 12

        term = Decimal(M * L) / X
        S += term

        current_time = time.time()
        total_elapsed = current_time - start_time

        if update_state and i % update_frequency == 0:
            update_state(
                state='PROGRESS',
                meta={
                    'progress': min(predict(a, b, i) / total_estimated, 0.999),
                    'task_id': task_id,
                    'iteration': i,
                    'total_iterations': iterations,
                    'elapsed_time': total_elapsed,
                    'msg': f"Completed {i} out of {iterations} iterations., {predict(a, b, i)}, {total_estimated}"
                }
            )

    pi_result = C / S
    total_time = time.time() - start_time

    print(f"Calculation completed in {total_time:.2f} seconds")

    format_str = f"{{0:.{n_decimals}f}}"
    return format_str.format(pi_result)

if __name__ == '__main__':
    n = 1000
    pi_value = calculate_pi(n)
    print(f"Pi to {n} decimal places:\n{pi_value}")