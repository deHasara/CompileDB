import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# Load CSV
# ==============================
csv_path = "output_cost_model.csv"

df = pd.read_csv(csv_path)

# ==============================
# Pick columns
# ==============================
numeric_cols = df.select_dtypes(include="number").columns.tolist()

if "est_cost" in df.columns:
    x_col = "est_cost"
else:
    x_col = numeric_cols[0]

if "exec_time" in df.columns:
    y_col = "exec_time"
else:
    y_col = numeric_cols[1]

x = df[x_col].to_numpy()
y = df[y_col].to_numpy()

# ==============================
# Keep only positive values
# (required for log scale)
# ==============================
mask = (x > 0) & (y > 0)
x = x[mask]
y = y[mask]

# ==============================
# Log transform
# ==============================
logx = np.log10(x)
logy = np.log10(y)

# ==============================
# Fit line in log-log space
# log10(y) = m * log10(x) + b
# ==============================
m, b = np.polyfit(logx, logy, 1)
logy_fit = m * logx + b

# sort x values for a clean fitted line
sort_idx = np.argsort(logx)
logx_sorted = logx[sort_idx]
logy_fit_sorted = logy_fit[sort_idx]

# ==============================
# Plot
# ==============================
plt.figure(figsize=(6,4))
# 🔽 smaller points (default ~36, try 8–15 for papers)
plt.scatter(logx, logy, s=10, alpha=0.7)
plt.plot(logx_sorted, logy_fit_sorted, color='red')
plt.xlabel("log10(est cost)")
plt.ylabel("log10(exec time)")
#plt.title("Log-Log: Estimated Cost vs Execution Time")
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

plt.tight_layout()

# ==============================
# Save plot
# ==============================
output_path = "loglog_plot.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()

# ==============================
# Print fitted equation
# ==============================
print(f"log10(exec_time) = {m:.6f} * log10(est_cost) + {b:.6f}")
print(f"Power-law form: exec_time ≈ 10^({b:.6f}) * est_cost^({m:.6f})")