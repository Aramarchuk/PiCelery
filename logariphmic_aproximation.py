import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for headless environments
import matplotlib.pyplot as plt
import json
import datetime

data = np.loadtxt('data.csv', delimiter=',', skiprows=1)
iterations = data[:, 0]
times = data[:, 1]

logn = np.log(iterations)
logT = np.log(times)

b = np.cov(logn, logT, bias=True)[0, 1] / np.var(logn)
a = np.mean(logT) - b * np.mean(logn)


def predict(n):
    return np.exp(a) * n ** b


print(f"a = {a:.3f}, b = {b:.3f}")
print("T(1e6) ≈", predict(1e6))

# Save parameters with maximum precision
json_path = 'approximation_params.json'
npz_path = 'approximation_params.npz'
params_payload = {
    'a': {
        'value': float(a),           # JSON numeric (double precision)
        'repr': repr(float(a)),      # Full precision decimal representation
        'hex': float(a).hex()        # Exact binary representation
    },
    'b': {
        'value': float(b),
        'repr': repr(float(b)),
        'hex': float(b).hex()
    },
    'dtype': 'float64',
    'created_at': datetime.datetime.now(datetime.UTC).isoformat()
}
with open(json_path, 'w+', encoding='utf-8') as f:
    json.dump(params_payload, f, ensure_ascii=False, indent=2)

# Also store exact binary floats
np.savez(npz_path, a=np.float64(a), b=np.float64(b))
print(f'Parameters saved to {json_path} and {npz_path}')

# --- Plot data points and fitted curve ---
# Sort for smooth line
order = np.argsort(iterations)
it_sorted = iterations[order]
T_sorted = times[order]

n_grid = np.linspace(it_sorted.min(), it_sorted.max(), 500)
T_pred = predict(n_grid)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Linear scale
ax1.scatter(iterations, times, s=18, alpha=0.65, label='Data')
ax1.plot(n_grid, T_pred, color='crimson', linewidth=2,
         label=f'Fit: T = {np.exp(a):.3g} · n^{b:.3f}')
ax1.set_xlabel('Iterations (n)')
ax1.set_ylabel('Time (T)')
ax1.set_title('Power-law fit (linear scale)')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Log-Log scale (power law becomes a straight line)
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
