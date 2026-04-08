import pandas as pd
import numpy as np

df = pd.read_csv("output_cost_model-1.csv", header=0)


x = df["exec time"].values
y = df["est cost"].values

# Fit line y = ax + b
a, b = np.polyfit(x, y, 1)

# Predicted values
y_pred = a * x + b

# Absolute residuals
errors = np.abs(y - y_pred)

max_error = errors.max()

print("Max error:", max_error)

# Optional: relative max error
relative_errors = errors / np.abs(y)
print("Max relative error:", relative_errors.max())

# Median
median_relative_error = np.median(relative_errors)
print("Median relative error:", median_relative_error)

