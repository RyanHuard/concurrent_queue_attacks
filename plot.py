# import pandas as pd
# import matplotlib.pyplot as plt
# import glob

# files = glob.glob("*_latencies_*.csv")

# for f in files:
#     df = pd.read_csv(f)
#    #df = df[df["latency"] < df["latency"].quantile(0.9)]
#     label = f.replace(".csv", "").replace("_latencies_", " ")
#     plt.hist(df["latency"], bins=50, alpha=0.6, label=label)

# plt.xlabel("Enqueue Latency (cycles)")
# plt.ylabel("Frequency")
# plt.legend()
# plt.xscale("log")
# plt.title("Attacker Enqueue Latency: Idle vs Active Workers")
# plt.savefig("latency_comparison.png")
# plt.show()

import pandas as pd
import matplotlib.pyplot as plt
import glob

overtake = {
    "ms":   {2: 18, 4: 35, 8: 52, 16: 65},
    "lprq": {2: 4,  4: 8, 8: 10, 16: 20},
    "fc":   {2: 6,  4: 17, 8: 25, 16: 35}
}

files = glob.glob("*_latencies_*.csv")
dfs = []
for f in files:
    df = pd.read_csv(f)
    parts = f.replace(".csv", "").split("_latencies_")
    df["queue"] = parts[0]
    df["condition"] = parts[1]
    dfs.append(df)

data = pd.concat(dfs)
data = data[data["latency"] < data.groupby(["queue", "workers", "condition"])["latency"].transform(lambda x: x.quantile(0.99))]

stats = data.groupby(["queue", "workers", "condition"])["latency"].std().reset_index()
stats.columns = ["queue", "workers", "condition", "std"]
active = stats[stats["condition"] == "active"]

colors = {"ms": "blue", "lprq": "orange", "fc": "green"}

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()

for queue, group in active.groupby("queue"):
    ax1.plot(group["workers"], group["std"], marker="o",
             color=colors[queue], linestyle="-", label=f"{queue} latency std")

    ot = overtake[queue]
    threads = list(ot.keys())
    pcts = list(ot.values())
    ax2.plot(threads, pcts, marker="s",
             color=colors[queue], linestyle="--", label=f"{queue} overtake %")

ax1.set_xlabel("Worker Thread Count")
ax1.set_ylabel("Enqueue Latency Std Dev (cycles)")
ax1.set_yscale("log")
ax2.set_ylabel("Overtake Percentage (%)")

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

plt.title("Enqueue Latency Std Dev and Fairness vs Thread Count")
plt.tight_layout()
plt.savefig("fairness_vs_signal.png")
plt.show()