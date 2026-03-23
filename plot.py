import pandas as pd
import matplotlib.pyplot as plt
import glob

files = glob.glob("*_latencies_*.csv")

for f in files:
    df = pd.read_csv(f)
   #df = df[df["latency"] < df["latency"].quantile(0.9)]
    label = f.replace(".csv", "").replace("_latencies_", " ")
    plt.hist(df["latency"], bins=50, alpha=0.6, label=label)

plt.xlabel("Enqueue Latency (cycles)")
plt.ylabel("Frequency")
plt.legend()
plt.xscale("log")
plt.title("Attacker Enqueue Latency: Idle vs Active Workers")
plt.savefig("latency_comparison.png")
plt.show()