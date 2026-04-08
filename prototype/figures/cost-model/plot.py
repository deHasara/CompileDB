import pandas as pd
import matplotlib.pyplot as plt


# replace with your filename
csv_path = "output_cost_model-1.csv"



# Read CSV. Works whether file has a header or not.
# If your file has a header like "x,y" set header=0, otherwise header=None
df = pd.read_csv(csv_path, header=0, names=["x", "y"], comment='#',
                 skip_blank_lines=True)

# Make sure values are numeric (drops rows that can't be parsed)
df["x"] = pd.to_numeric(df["x"], errors="coerce")
df["y"] = pd.to_numeric(df["y"], errors="coerce")
df = df.dropna(subset=["x", "y"])

# Scale y by 1000 to convert ms to s
df["y"] = df["y"] / (1000.0*1000.0)

# Simple linear plot
plt.figure(figsize=(6,4))
#plt.plot(df["x"], df["y"], marker="o")   # marker is allowed; no explicit color set
plt.scatter(df["x"], df["y"], marker="o")  # dots, no connecting lines
plt.yscale("log")
#plt.ylim(bottom=1.3e3)



plt.xlabel("est cost")
plt.ylabel("exec time(s)")
plt.title("est cost vs exec time(s)")
plt.grid(True)
plt.tight_layout()

# show on screen
plt.show()

# optionally save to file
plt.savefig("cost_model_plot1.png", bbox_inches="tight")
