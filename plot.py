
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import ks_2samp, pearsonr
import numpy as np

# ---- CONFIG ----
queues = ["ms", "fc", "lprq"]
colors = {"ms": "blue", "lprq": "orange", "fc": "green"}

workers = 7
trial = None
bins = 100

threads = [2,3,4,5,6,7,8,9,10,11,12,13,14,15]

overtake = {
    "ms": {
        1: 0, 2: 0, 3: 4, 4: 21, 5: 33, 6: 40, 7: 45, 8: 48,
        9: 46, 10: 47, 11: 50, 12: 54, 13: 58, 14: 61, 15: 64, 16: 66
    },
    "lprq": {
        1: 0, 2: 2, 3: 4, 4: 6, 5: 7, 6: 8, 7: 8, 8: 9,
        9: 12, 10: 15, 11: 17, 12: 19, 13: 20, 14: 20, 15: 20, 16: 21
    },
    "fc": {
        1: 0, 2: 6, 3: 13, 4: 18, 5: 20, 6: 22, 7: 24, 8: 25,
        9: 26, 10: 29, 11: 30, 12: 32, 13: 33, 14: 35, 15: 36, 16: 37
    }
}

def filter_df(df):
    df = df[df["workers"] == workers]
    if trial is not None:
        df = df[df["trial"] == trial]
    return df

def clip_99(df):
    p99 = df["latency"].quantile(0.99)
    return df[df["latency"] <= p99]


# for q in queues:
#     active = pd.read_csv(f"{q}_latencies_active.csv")
#     idle   = pd.read_csv(f"{q}_latencies_idle.csv")

#     active = clip_99(filter_df(active))
#     idle   = clip_99(filter_df(idle))

#     plt.hist(
#         active["latency"],
#         bins=bins,
#         histtype="step",
#         linewidth=2,
#         label=f"{q} active"
#     )

#     plt.hist(
#         idle["latency"],
#         bins=bins,
#         histtype="step",
#         linestyle="dashed",
#         linewidth=2,
#         label=f"{q} idle"
#     )

# plt.xlabel("Latency (cycles)")
# plt.ylabel("Density")
# plt.title(f"Latency Distributions (≤99th percentile, workers={workers})")
# plt.legend()
# plt.xscale("log")
# plt.yscale("log")
# plt.show()

def filter_df(df):
    df = df[df["workers"] == workers]
    if trial is not None:
        df = df[df["trial"] == trial]
    return df

def clip_shared_99(active, idle):
    combined = pd.concat([active["latency"], idle["latency"]])
    p99 = combined.quantile(0.99)
    return (
        active[active["latency"] <= p99],
        idle[idle["latency"] <= p99]
    )

def plot_cdf(data, label, linestyle="-"):
    x = np.sort(data)
    y = np.arange(1, len(x) + 1) / len(x)
    plt.plot(x, y, linestyle=linestyle, label=label)

plt.figure()

for q in queues:
    active = pd.read_csv(f"{q}_latencies_active.csv")
    idle   = pd.read_csv(f"{q}_latencies_idle.csv")

    active = filter_df(active)
    idle   = filter_df(idle)
    active, idle = clip_shared_99(active, idle)

    plot_cdf(active["latency"].to_numpy(), f"{q} active", "-")
    plot_cdf(idle["latency"].to_numpy(), f"{q} idle", "--")

plt.xscale("log")
plt.xlabel("Latency (cycles)")
plt.ylabel("CDF")
plt.title(f"Latency CDFs (<=99th percentile, workers={workers})")
plt.legend()
plt.show()


def load_latency_data():
    files = glob.glob("*_latencies.csv")
    dfs = []

    for f in files:
        df = pd.read_csv(f)

        # Expect filenames like "ms_latencies.csv"
        queue = f.replace("_latencies.csv", "")
        df["queue"] = queue

        # Require trial column now
        if "trial" not in df.columns:
            raise ValueError(f"{f} is missing required 'trial' column")

        dfs.append(df)

    if not dfs:
        raise FileNotFoundError("No *_latencies.csv files found")

    return pd.concat(dfs, ignore_index=True)


def filter_outliers_per_trial(df):
    return df[
        df["latency"]
        < df.groupby(["queue", "trial", "workers"])["latency"]
            .transform(lambda x: x.quantile(0.99))
    ]


def compute_latency_std_by_worker(df, queue):
    qdf = df[df["queue"] == queue].copy()
    if qdf.empty:
        return pd.DataFrame(columns=["workers", "mean_std", "std_std"])

    trial_stats = (
        qdf.groupby(["trial", "workers"])["latency"]
        .std()
        .reset_index(name="latency_std")
    )

    stats = (
        trial_stats.groupby("workers")["latency_std"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "mean_std", "std": "std_std"})
    )

    return stats


def plot_std_vs_overtake_dual_axis():
    queues = ["ms", "lprq", "fc"]

    fig, ax1 = plt.subplots(figsize=(8,5))
    ax2 = ax1.twinx()

    markers = {"ms": "o", "lprq": "s", "fc": "^"}

    for q in queues:
        active = pd.read_csv(f"{q}_latencies_active.csv")

        stds = []
        ovs = []

        for t in threads:
            df = active[active["workers"] == t]

            if len(df) > 0:
                # clip top 1% (recommended)
                p99 = df["latency"].quantile(1)
                df = df[df["latency"] <= p99]

                std = df["latency"].std()
                stds.append(std)
            else:
                stds.append(np.nan)

            ovs.append(overtake[q].get(t, np.nan))

        ax1.plot(
            threads,
            stds,
            marker=markers[q],
            linestyle="-",
            label=f"{q} std"
        )

        ax2.plot(
            threads,
            ovs,
            marker=markers[q],
            linestyle="--",
            label=f"{q} overtake"
        )

    ax1.set_xlabel("Thread Count")
    ax1.set_ylabel("Latency Std Dev (cycles)")
    ax1.set_yscale("log")
    ax2.set_ylabel("Overtake Percentage")

    ax1.set_title("Latency Variability vs Fairness")

    # combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    fig.tight_layout()

    # ---- SAVE FIGURE ----
    filename = "std_vs_overtake.png"
    fig.savefig(filename, dpi=200, bbox_inches="tight")
    print(f"Saved plot to {filename}")

    # ---- TRY TO SHOW ----
    plt.show()

    return filename


def plot_iqr_vs_overtake_dual_axis():
    queues = ["ms", "lprq", "fc"]

    fig, ax1 = plt.subplots(figsize=(8,5))
    ax2 = ax1.twinx()

    markers = {"ms": "o", "lprq": "s", "fc": "^"}

    for q in queues:
        active = pd.read_csv(f"{q}_latencies_active.csv")

        iqrs = []
        ovs = []

        for t in threads:
            df = active[active["workers"] == t]

            if len(df) > 0:
                lat = df["latency"]

                # optional: shared p99 clipping (keep or remove as you prefer)
                p99 = lat.quantile(0.99)
                lat = lat[lat <= p99]

                q25 = lat.quantile(0.25)
                q75 = lat.quantile(0.75)
                iqr = q75 - q25

                iqrs.append(iqr)
            else:
                iqrs.append(np.nan)

            ovs.append(overtake[q].get(t, np.nan))

        # left axis: IQR
        ax1.plot(
            threads,
            iqrs,
            marker=markers[q],
            linestyle="-",
            label=f"{q} IQR"
        )

        # right axis: overtake
        ax2.plot(
            threads,
            ovs,
            marker=markers[q],
            linestyle="--",
            label=f"{q} overtake"
        )

    ax1.set_xlabel("Thread Count")
    ax1.set_ylabel("Latency IQR (cycles)")
    ax2.set_ylabel("Overtake Percentage")

    ax1.set_title("Latency Variability (IQR) vs Fairness")

    # optional log scale (often helpful)
    ax1.set_yscale("log")

    # combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    fig.tight_layout()

    filename = "iqr_vs_overtake.png"
    fig.savefig(filename, dpi=200, bbox_inches="tight")
    print(f"Saved plot to {filename}")

    plt.show()


# plot_std_vs_overtake_dual_axis()
# plot_iqr_vs_overtake_dual_axis()

import glob


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