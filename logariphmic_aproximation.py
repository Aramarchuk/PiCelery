import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import datetime
from typing import Tuple


def fit_power_law(iterations: np.ndarray, times: np.ndarray) -> Tuple[float, float]:
    """
    Fit log-log linear model: log T = a + b log n.

    Performs power-law regression to model the relationship between
    the number of iterations and execution time. This is used for
    time estimation in π calculations.

    Args:
        iterations (np.ndarray): Array of iteration counts (n values).
        times (np.ndarray): Array of corresponding execution times (T values).

    Returns:
        Tuple[float, float]: A tuple containing:
            - a (float): Intercept parameter of the power-law model.
            - b (float): Exponent parameter of the power-law model.

    Raises:
        ValueError: If there are fewer than 2 valid data points.

    Note:
        - Filters out non-positive values because log requires > 0
        - Uses least squares regression on log-transformed data
        - Model: T = exp(a) * n^b
    """
    mask = (iterations > 0) & (times > 0)
    it = iterations[mask]
    t = times[mask]
    if it.size < 2:
        raise ValueError("Not enough valid (positive) points to fit power-law model")

    logn = np.log(it)
    logT = np.log(t)
    b = np.cov(logn, logT, bias=True)[0, 1] / np.var(logn)
    a = np.mean(logT) - b * np.mean(logn)
    return float(a), float(b)


def save_params_json(
    a: float,
    b: float,
    json_path: str = 'approximation_params.json'
) -> None:
    """
    Save power-law approximation parameters to JSON file.

    Stores the fitted parameters with multiple representations for
    precision preservation and metadata.

    Args:
        a (float): Intercept parameter from power-law fit.
        b (float): Exponent parameter from power-law fit.
        json_path (str): Path to save the JSON file.
                        Defaults to 'approximation_params.json'.

    Note:
        - Saves value, repr, and hex representations for precision
        - Includes timestamp and data type metadata
        - Used by π calculator for time estimation
    """
    payload = {
        'a': {
            'value': float(a),
            'repr': repr(float(a)),
            'hex': float(a).hex(),
        },
        'b': {
            'value': float(b),
            'repr': repr(float(b)),
            'hex': float(b).hex(),
        },
        'dtype': 'float64',
        'created_at': datetime.datetime.now(datetime.UTC).isoformat(),
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def predict(
    a: float,
    b: float,
    n: np.ndarray | float
) -> np.ndarray | float:
    """
    Predict execution time using power-law model.

    Estimates computation time based on the fitted power-law model
    T = exp(a) * n^b, where n is the number of iterations.

    Args:
        a (float): Intercept parameter from power-law fit.
        b (float): Exponent parameter from power-law fit.
        n (np.ndarray | float): Number of iterations (scalar or array).

    Returns:
        np.ndarray | float: Predicted execution time(s).
                           Type matches input type.
    """
    return np.exp(a) * np.power(n, b)

def compute_approximation(task_id):
    pass


if __name__ == '__main__':
    data = np.loadtxt('data.csv', delimiter=',', skiprows=1)
    iterations = data[:, 0]
    times = data[:, 1]
    a, b = fit_power_law(iterations, times)

    print(f"a = {a:.3f}, b = {b:.3f}")
    print("T(1e6) ≈", predict(a, b, 1e6))

    order = np.argsort(iterations)
    it_sorted = iterations[order]
    n_grid = np.linspace(it_sorted.min(), it_sorted.max(), 500)
    T_pred = predict(a, b, n_grid)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.scatter(iterations, times, s=18, alpha=0.65, label='Data')
    ax1.plot(n_grid, T_pred, color='crimson', linewidth=2,
             label=f'Fit: T = {np.exp(a):.3g} · n^{b:.3f}')
    ax1.set_xlabel('Iterations (n)')
    ax1.set_ylabel('Time (T)')
    ax1.set_title('Power-law fit (linear scale)')
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2.scatter(iterations, times, s=18, alpha=0.65, label='Data')
    ax2.plot(n_grid, T_pred, color='crimson', linewidth=2, label='Fit')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel('Iterations (n) [log]')
    ax2.set_ylabel('Time (T) [log]')
    ax2.set_title('Power-law fit (log-log)')
    ax2.grid(True, which='both', alpha=0.3)
    ax2.legend()

    fig.suptitle(f'Fitted model: T ≈ {np.exp(a):.3g} · n^{b:.3f}', fontsize=11)
    fig.tight_layout(rect=(0.0, 0.03, 1.0, 0.95))
    output_path = 'approximation_plot.png'
    plt.savefig(output_path, dpi=150)
    print(f'Plot saved to {output_path}')
