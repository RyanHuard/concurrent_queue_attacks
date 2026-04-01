
# # import pandas as pd
# # import matplotlib.pyplot as plt
# # from scipy.stats import ks_2samp, pearsonr
# # import numpy as np

# # # # ---- CONFIG ----
# # queues = ["ms", "fc", "lprq"]
# # colors = {"ms": "blue", "lprq": "orange", "fc": "green"}

# # workers = 15
# # trial = None
# # bins = 25

# # threads = [2,3,4,5,6,7,8,9,10,11,12,13,14,15]

# # overtake = {
# #     "ms": {
# #         1: 0, 2: 0, 3: 4, 4: 21, 5: 33, 6: 40, 7: 45, 8: 48,
# #         9: 46, 10: 47, 11: 50, 12: 54, 13: 58, 14: 61, 15: 64, 16: 66
# #     },
# #     "lprq": {
# #         1: 0, 2: 2, 3: 4, 4: 6, 5: 7, 6: 8, 7: 8, 8: 9,
# #         9: 12, 10: 15, 11: 17, 12: 19, 13: 20, 14: 20, 15: 20, 16: 21
# #     },
# #     "fc": {
# #         1: 0, 2: 6, 3: 13, 4: 18, 5: 20, 6: 22, 7: 24, 8: 25,
# #         9: 26, 10: 29, 11: 30, 12: 32, 13: 33, 14: 35, 15: 36, 16: 37
# #     }
# # }

# # def filter_df(df):
# #     df = df[df["workers"] == workers]
# #     if trial is not None:
# #         df = df[df["trial"] == trial]
# #     return df

# # def clip_99(df):
# #     p99 = df["latency"].quantile(1)
# #     return df[df["latency"] <= p99]


# # # for q in queues:
# # for q in queues:
# #     active = pd.read_csv(f"{q}_latencies_active.csv")
# #     idle   = pd.read_csv(f"{q}_latencies_idle.csv")
    

# #     active = clip_99(filter_df(active))
# #     idle   = clip_99(filter_df(idle))

# #     plt.hist(
# #         active["latency"],
# #         bins=bins,
# #         histtype="step",
# #         linewidth=1,
# #         label=f"{q} active"
# #     )

# #     plt.hist(
# #         idle["latency"],
# #         bins=bins,
# #         histtype="step",
# #         linestyle="dashed",
# #         linewidth=1,
# #         label=f"{q} idle"
# #     )

# # print(active["latency"].min(), idle["latency"].min())
# # plt.xlabel("Latency (cycles)")
# # plt.ylabel("Density")
# # plt.title(f"Latency Distributions (≤99th percentile, workers={workers})")
# # plt.legend()

# # plt.xscale("log")
# # plt.yscale("log")
# # plt.savefig("test")
# # plt.show()

# # def filter_df(df):
# #     df = df[df["workers"] == workers]
# #     if trial is not None:
# #         df = df[df["trial"] == trial]
# #     return df

# # def clip_shared_99(active, idle):
# #     combined = pd.concat([active["latency"], idle["latency"]])
# #     p99 = combined.quantile(0.99)
# #     return (
# #         active[active["latency"] <= p99],
# #         idle[idle["latency"] <= p99]
# #     )

# # def plot_cdf(data, label, linestyle="-"):
# #     x = np.sort(data)
# #     y = np.arange(1, len(x) + 1) / len(x)
# #     plt.plot(x, y, linestyle=linestyle, label=label)

# # plt.figure()

# # for q in queues:
# #     active = pd.read_csv(f"{q}_latencies_active.csv")
# #     idle   = pd.read_csv(f"{q}_latencies_idle.csv")

# #     active = filter_df(active)
# #     idle   = filter_df(idle)
# #     active, idle = clip_shared_99(active, idle)

# #     plot_cdf(active["latency"].to_numpy(), f"{q} active", "-")
# #     plot_cdf(idle["latency"].to_numpy(), f"{q} idle", "--")

# # plt.xscale("log")
# # plt.xlabel("Latency (cycles)")
# # plt.ylabel("CDF")
# # plt.title(f"Latency CDFs (<=99th percentile, workers={workers})")
# # plt.legend()
# # plt.savefig("latency_cdf")
# # plt.show()


# # def load_latency_data():
# #     files = glob.glob("*_latencies.csv")
# #     dfs = []

# #     for f in files:
# #         df = pd.read_csv(f)

# #         # Expect filenames like "ms_latencies.csv"
# #         queue = f.replace("_latencies.csv", "")
# #         df["queue"] = queue

# #         # Require trial column now
# #         if "trial" not in df.columns:
# #             raise ValueError(f"{f} is missing required 'trial' column")

# #         dfs.append(df)

# #     if not dfs:
# #         raise FileNotFoundError("No *_latencies.csv files found")

# #     return pd.concat(dfs, ignore_index=True)


# # def filter_outliers_per_trial(df):
# #     return df[
# #         df["latency"]
# #         < df.groupby(["queue", "trial", "workers"])["latency"]
# #             .transform(lambda x: x.quantile(0.99))
# #     ]


# # def compute_latency_std_by_worker(df, queue):
# #     qdf = df[df["queue"] == queue].copy()
# #     if qdf.empty:
# #         return pd.DataFrame(columns=["workers", "mean_std", "std_std"])

# #     trial_stats = (
# #         qdf.groupby(["trial", "workers"])["latency"]
# #         .std()
# #         .reset_index(name="latency_std")
# #     )

# #     stats = (
# #         trial_stats.groupby("workers")["latency_std"]
# #         .agg(["mean", "std"])
# #         .reset_index()
# #         .rename(columns={"mean": "mean_std", "std": "std_std"})
# #     )

# #     return stats


# # def plot_std_vs_overtake_dual_axis():
# #     queues = ["ms", "lprq", "fc"]

# #     fig, ax1 = plt.subplots(figsize=(8,5))
# #     ax2 = ax1.twinx()

# #     markers = {"ms": "o", "lprq": "s", "fc": "^"}

# #     for q in queues:
# #         active = pd.read_csv(f"{q}_latencies_active.csv")

# #         stds = []
# #         ovs = []

# #         for t in threads:
# #             df = active[active["workers"] == t]

# #             if len(df) > 0:
# #                 # clip top 1% (recommended)
# #                 p99 = df["latency"].quantile(.99)
# #                 df = df[df["latency"] <= p99]

# #                 std = df["latency"].std()
# #                 stds.append(std)
# #             else:
# #                 stds.append(np.nan)

# #             ovs.append(overtake[q].get(t, np.nan))

# #         ax1.plot(
# #             threads,
# #             stds,
# #             marker=markers[q],
# #             linestyle="-",
# #             label=f"{q} std"
# #         )

# #         ax2.plot(
# #             threads,
# #             ovs,
# #             marker=markers[q],
# #             linestyle="--",
# #             label=f"{q} overtake"
# #         )

# #     ax1.set_xlabel("Thread Count")
# #     ax1.set_ylabel("Enqueue Latency Std Dev (cycles)")
# #     ax1.set_yscale("log")
# #     ax2.set_ylabel("Overtake Percentage")

# #     ax1.set_title("Enqueue Latency Std Dev vs Fairness")

# #     # combine legends
# #     lines1, labels1 = ax1.get_legend_handles_labels()
# #     lines2, labels2 = ax2.get_legend_handles_labels()
# #     ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

# #     fig.tight_layout()

# #     # ---- SAVE FIGURE ----
# #     filename = "std_vs_overtake.png"
# #     fig.savefig(filename, dpi=200, bbox_inches="tight")
# #     print(f"Saved plot to {filename}")

# #     # ---- TRY TO SHOW ----
# #     plt.show()

# #     return filename




# # plot_std_vs_overtake_dual_axis()


# # from scipy.stats import ks_2samp

# # def workload_ks(queue):
# #     active = pd.read_csv(f"{queue}_latencies_active.csv")
# #     idle = pd.read_csv(f"{queue}_latencies_idle.csv")

# #     results = []

# #     for workers in sorted(active["workers"].unique()):
# #         a = active[active["workers"] == workers]["latency"].values[:5000]
# #         i = idle[idle["workers"] == workers]["latency"].values[:5000]

# #         if len(a) > 100 and len(i) > 100:
# #             stat, pval = ks_2samp(a, i)
# #             results.append({
# #                 "workers": workers,
# #                 "ks_stat": stat
# #             })
# #             print(f"  workers={workers}: KS={stat:.4f}")

# #     return pd.DataFrame(results)

# # print("\nWorkload KS (active vs slow-access):")
# # for queue in ["ms", "lprq", "fc"]:
# #     print(f"\n{queue}:")
# #     try:
# #         df = workload_ks(queue)
# #     except FileNotFoundError:
# #         print("  files not found")


# # fig, ax = plt.subplots()

# # for queue in ["ms", "lprq", "fc"]:
# #     try:
# #         df = workload_ks(queue)
# #         ax.plot(df["workers"], df["ks_stat"], marker="o",
# #                 color=colors[queue], label=queue)
# #     except FileNotFoundError:
# #         pass

# # ax.set_xlabel("Worker Thread Count")
# # ax.set_ylabel("KS Statistic (Active vs Slow-Access)")
# # ax.legend()
# # ax.set_title("Workload Distinguishability by Queue")
# # plt.tight_layout()
# # plt.savefig("workload_ks.png")
# # plt.show()



# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.signal import medfilt

# # ---- CONFIG ----
# queues = ["ms", "fc", "lprq"]
# colors = {"ms": "#1f77b4", "lprq": "#ff7f0e", "fc": "#2ca02c"}
# markers = {"ms": "o", "fc": "^", "lprq": "s"}
# direction = "idle_to_active"   # or "active_to_idle"
# window = 100                   # rolling window for CUSUM / rolling stats
# workers_to_plot = 15           # thread count for detailed plots

# # ---- LOAD DATA ----
# def load(queue, direction):
#     fname = f"{queue}_changepoint_{direction}.csv"
#     try:
#         return pd.read_csv(fname)
#     except FileNotFoundError:
#         print(f"  {fname} not found")
#         return None

# # ---- CUSUM CHANGE-POINT DETECTOR ----
# # Simple CUSUM: accumulates deviation from running mean.
# # Detects the op_index where cumulative sum exceeds a threshold.
# def cusum_detect(latencies, switch_op, threshold_sigma=5.0, burnin=400):
#     if len(latencies) < burnin + 100:
#         return -1

#     # Use median/MAD for robust baseline (outlier-resistant)
#     baseline = latencies[:burnin]
#     mu = np.median(baseline)
#     mad = np.median(np.abs(baseline - mu))
#     sigma = mad * 1.4826  # scale MAD to std dev equivalent

#     if sigma == 0:
#         return -1

#     threshold = threshold_sigma * sigma
#     cusum_pos = 0.0

#     # Only start scanning AFTER the switch point
#     for i in range(switch_op, len(latencies)):
#         z = latencies[i] - mu
#         cusum_pos = max(0, cusum_pos + z)

#         if cusum_pos > threshold:
#             return i

#     return -1


# # ---- ROLLING STATISTICS DETECTOR (simpler alternative) ----
# def rolling_std_detect(latencies, window=100, threshold_sigma=2.5, burnin=500):
#     """
#     Detect change-point by monitoring rolling std dev.
#     When rolling std deviates from baseline std by threshold_sigma, flag it.
#     """
#     if len(latencies) < burnin + window:
#         return -1

#     baseline_std = np.std(latencies[:burnin])
#     if baseline_std == 0:
#         return -1

#     for i in range(burnin, len(latencies) - window):
#         local_std = np.std(latencies[i:i + window])
#         if abs(local_std - baseline_std) / baseline_std > threshold_sigma:
#             return i

#     return -1


# # ============================================================
# # PLOT 1: Raw attacker latency trace with true switch marked
# # ============================================================
# def plot_raw_traces(direction="idle_to_active", workers=15):
#     fig, axes = plt.subplots(len(queues), 1, figsize=(12, 3 * len(queues)),
#                              sharex=True)

#     for ax, q in zip(axes, queues):
#         df = load(q, direction)
#         if df is None:
#             continue

#         sub = df[(df["workers"] == workers) & (df["trial"] == 0)]
#         if sub.empty:
#             continue

#         switch_op = sub["switch_op"].iloc[0]

#         # Median filter for visual clarity
#         raw = sub["latency"].values
#         smoothed = medfilt(raw, kernel_size=51)

#         ax.plot(sub["op_index"], raw, alpha=0.15, color=colors[q], linewidth=0.5)
#         ax.plot(sub["op_index"], smoothed, color=colors[q], linewidth=1.5,
#                 label=f"{q.upper()} (median-filtered)")
#         ax.axvline(x=switch_op, color="red", linestyle="--", linewidth=1.5,
#                    label="True switch point")

#         ax.set_ylabel("Latency (cycles)")
#         ax.set_yscale("log")
#         ax.legend(loc="upper right")
#         ax.set_title(f"{q.upper()} — {direction.replace('_', ' ')}")

#     axes[-1].set_xlabel("Attacker Op Index")
#     plt.suptitle(f"Attacker Latency Traces ({direction.replace('_', ' ')}, "
#                  f"workers={workers})", fontsize=13, y=1.01)
#     plt.tight_layout()
#     plt.savefig(f"changepoint_traces_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_traces_{direction}.png")


# # ============================================================
# # PLOT 2: Detection latency comparison across queues
# # ============================================================
# def plot_detection_latency(direction="idle_to_active"):
#     """
#     For each queue and worker count, run CUSUM across all trials.
#     Report: mean detection delay (detected_op - true_switch_op) in #ops.
#     Lower = attacker detects faster = worse for security.
#     """
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         worker_counts = sorted(df["workers"].unique())
#         mean_delays = []
#         std_delays = []
#         valid_workers = []

#         for w in worker_counts:
#             wdf = df[df["workers"] == w]
#             switch_op = wdf["switch_op"].iloc[0]
#             delays = []

#             for trial in wdf["trial"].unique():
#                 tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#                 latencies = tdf["latency"].values

#                 from scipy.ndimage import uniform_filter1d

#                 smoothed = pd.Series(latencies).rolling(window=50, min_periods=1).median().values
#                 detected = cusum_detect(smoothed, switch_op, threshold_sigma=5.0, burnin=400)
                
#                 if detected > 0:
#                     delay = detected - switch_op
#                     delays.append(delay)

#             if delays:
#                 valid_workers.append(w)
#                 mean_delays.append(np.median(delays))  # instead of np.mean
#                 std_delays.append(np.std(delays))

#         if valid_workers:
#             ax.plot(valid_workers, mean_delays, marker=markers[q], color=colors[q],
#             label=q.upper(), linewidth=1.5)

#     ax.set_xlabel("Worker Thread Count")
#     ax.set_ylabel("Detection Delay (ops after true switch)")
#     ax.set_title(f"Change-Point Detection Latency ({direction.replace('_', ' ')})")
#     ax.legend()
#     ax.axhline(y=0, color="gray", linestyle=":", alpha=0.5)
#     plt.tight_layout()

#     plt.savefig(f"changepoint_delay_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_delay_{direction}.png")


# # ============================================================
# # PLOT 3: Detection success rate across queues
# # ============================================================
# def plot_detection_rate(direction="idle_to_active"):
#     """
#     Fraction of trials where CUSUM successfully detected the change-point.
#     MS Queue should have highest detection rate (worst security).
#     """
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         worker_counts = sorted(df["workers"].unique())
#         rates = []
#         valid_workers = []

#         for w in worker_counts:
#             wdf = df[df["workers"] == w]
#             switch_op = wdf["switch_op"].iloc[0]
#             n_trials = len(wdf["trial"].unique())
#             n_detected = 0

#             for trial in wdf["trial"].unique():
#                 tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#                 latencies = tdf["latency"].values

#                 detected = cusum_detect(latencies, switch_op, threshold_sigma=5.0,
#                                         burnin=min(500, switch_op - 100))
#                 # Count as detected if it fires within a reasonable window
#                 # after the true switch (not a false positive before it)
#                 if 0 < detected and detected >= switch_op - 50:
#                     n_detected += 1

#             valid_workers.append(w)
#             rates.append(n_detected / n_trials)

#         if valid_workers:
#             ax.plot(valid_workers, rates, marker=markers[q], color=colors[q],
#                     label=q.upper(), linewidth=1.5)

#     ax.set_xlabel("Worker Thread Count")
#     ax.set_ylabel("Detection Rate")
#     ax.set_ylim(-0.05, 1.05)
#     ax.set_title(f"Change-Point Detection Success Rate ({direction.replace('_', ' ')})")
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig(f"changepoint_rate_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_rate_{direction}.png")


# # ============================================================
# # PLOT 4: CUSUM trace overlay (shows the detector in action)
# # ============================================================
# def plot_cusum_traces(direction="idle_to_active", workers=15, trial=0):
#     """
#     Show the CUSUM accumulator for each queue on the same plot.
#     Visualizes how quickly the signal builds after the transition.
#     """
#     fig, ax = plt.subplots(figsize=(10, 5))

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         sub = df[(df["workers"] == workers) & (df["trial"] == trial)]
#         if sub.empty:
#             continue

#         sub = sub.sort_values("op_index")
#         latencies = sub["latency"].values
#         switch_op = sub["switch_op"].iloc[0]
#         burnin = min(500, switch_op - 100)

#         if len(latencies) < burnin + 100:
#             continue

#         mu = np.mean(latencies[:burnin])

#         # Compute running CUSUM
#         cusum = np.zeros(len(latencies))
#         for i in range(burnin, len(latencies)):
#             cusum[i] = max(0, cusum[i - 1] + (latencies[i] - mu))

#         ax.plot(sub["op_index"].values, cusum, color=colors[q],
#                 label=q.upper(), linewidth=1.5)

#     ax.axvline(x=switch_op, color="red", linestyle="--", linewidth=1.5,
#                label="True switch point")
#     ax.set_xlabel("Attacker Op Index")
#     ax.set_ylabel("CUSUM Accumulator")
#     ax.set_title(f"CUSUM Traces ({direction.replace('_', ' ')}, "
#                  f"workers={workers}, trial={trial})")
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig(f"changepoint_cusum_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_cusum_{direction}.png")


# from scipy.ndimage import uniform_filter1d
# def plot_detection_bar(direction="idle_to_active", workers=15):
#     fig, ax = plt.subplots(figsize=(6, 4))

#     labels = []
#     delays = []

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         wdf = df[df["workers"] == workers]
#         switch_op = wdf["switch_op"].iloc[0]
#         trial_delays = []

#         for trial in wdf["trial"].unique():
#             tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#             latencies = tdf["latency"].values
#             smoothed = pd.Series(latencies).rolling(window=50, min_periods=1).median().values
#             detected = cusum_detect(smoothed, switch_op, threshold_sigma=5.0, burnin=400)

#             if detected > 0:
#                 trial_delays.append(detected - switch_op)

#         labels.append(q.upper())
#         delays.append(np.median(trial_delays) if trial_delays else num_ops // 2)

#     ax.bar(labels, delays, color=[colors[q] for q in queues])
#     ax.set_ylabel("Median Detection Delay (ops)")
#     ax.set_title(f"Change-Point Detection Latency (workers={workers})")
#     plt.tight_layout()
#     plt.savefig(f"changepoint_bar_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()

# # ---- RUN ALL PLOTS ----
# if __name__ == "__main__":
#     for d in ["idle_to_active"]:
#         print(f"\n=== {d} ===")
#         plot_raw_traces(direction=d, workers=workers_to_plot)
#         plot_detection_latency(direction=d)
#         plot_detection_bar(direction=d, workers=workers_to_plot)
#         plot_cusum_traces(direction=d, workers=workers_to_plot, trial=0)




# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import cross_val_score, StratifiedKFold
# from sklearn.preprocessing import LabelEncoder
# from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
# from scipy.stats import skew, kurtosis

# # ---- CONFIG ----
# queues = ["ms", "fc", "lprq"]
# colors = {"ms": "#1f77b4", "lprq": "#ff7f0e", "fc": "#2ca02c"}
# markers = {"ms": "o", "fc": "^", "lprq": "s"}

# WINDOW_SIZES = [50, 100, 200, 500]


# def load(queue):
#     fname = f"{queue}_classify.csv"
#     try:
#         return pd.read_csv(fname)
#     except FileNotFoundError:
#         print(f"  {fname} not found")
#         return None


# # ---- FEATURE EXTRACTION ----
# # Shape-only features. No mean/median/percentiles — those capture
# # contention level, not contention pattern. We only want features
# # that distinguish steady vs. bursty temporal patterns.
# def extract_features(latencies):
#     mu = np.mean(latencies)
#     std = np.std(latencies)
#     return {
#         "std": std,
#         "cv": std / mu if mu > 0 else 0,
#         "iqr": np.percentile(latencies, 75) - np.percentile(latencies, 25),
#         "skewness": skew(latencies) if std > 0 else 0,
#         "kurtosis": kurtosis(latencies) if std > 0 else 0,
#         "range": np.max(latencies) - np.min(latencies),
#         # Autocorrelation at lag 1: captures temporal structure
#         # (bursty workload creates correlated attacker latencies)
#         "autocorr_1": np.corrcoef(latencies[:-1], latencies[1:])[0, 1]
#                        if len(latencies) > 2 and std > 0 else 0,
#     }


# def build_feature_matrix(df, window_size, workers=None):
#     if workers is not None:
#         df = df[df["workers"] == workers]

#     features = []
#     labels = []

#     for (wl, trial), group in df.groupby(["workload", "trial"]):
#         latencies = group.sort_values("sample")["latency"].values

#         # Clip top 1%
#         p99 = np.percentile(latencies, 99)
#         latencies = np.clip(latencies, 0, p99)

#         # Slide with 50% overlap
#         step = window_size // 2
#         for start in range(0, len(latencies) - window_size, step):
#             window = latencies[start:start + window_size]
#             feat = extract_features(window)
#             feat["trial"] = trial
#             features.append(feat)
#             labels.append(wl)

#     X = pd.DataFrame(features)
#     y = np.array(labels)
#     return X, y


# # ============================================================
# # PLOT 1: Classification accuracy vs window size
# # ============================================================
# def plot_accuracy_vs_window(workers=15):
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q)
#         if df is None:
#             continue

#         accuracies = []
#         stds = []

#         for ws in WINDOW_SIZES:
#             X, y = build_feature_matrix(df, ws, workers=workers)

#             if len(X) < 20 or len(np.unique(y)) < 2:
#                 accuracies.append(np.nan)
#                 stds.append(np.nan)
#                 continue

#             X_train = X.drop(columns=["trial"])
#             le = LabelEncoder()
#             y_enc = le.fit_transform(y)

#             clf = RandomForestClassifier(n_estimators=100, random_state=42)
#             cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#             scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")

#             accuracies.append(scores.mean())
#             stds.append(scores.std())

#         ax.errorbar(WINDOW_SIZES, accuracies, yerr=stds,
#                     marker=markers[q], color=colors[q],
#                     label=q.upper(), capsize=3, linewidth=1.5)

#     ax.axhline(y=0.5, color="gray", linestyle=":", label="Chance (50%)")
#     ax.set_xlabel("Attacker Window Size (# ops)")
#     ax.set_ylabel("Classification Accuracy")
#     ax.set_title(f"Deterministic vs. Variable Classification (workers={workers})")
#     ax.set_ylim(0.4, 1.05)
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig("classify_accuracy_vs_window.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print("Saved classify_accuracy_vs_window.png")


# # ============================================================
# # PLOT 2: Classification accuracy vs thread count
# # ============================================================
# def plot_accuracy_vs_threads(window_size=200):
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q)
#         if df is None:
#             continue

#         worker_counts = sorted(df["workers"].unique())
#         accuracies = []
#         valid_workers = []

#         for w in worker_counts:
#             X, y = build_feature_matrix(df, window_size, workers=w)

#             if len(X) < 20 or len(np.unique(y)) < 2:
#                 continue

#             X_train = X.drop(columns=["trial"])
#             le = LabelEncoder()
#             y_enc = le.fit_transform(y)

#             clf = RandomForestClassifier(n_estimators=100, random_state=42)
#             cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#             scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")

#             valid_workers.append(w)
#             accuracies.append(scores.mean())

#         if valid_workers:
#             ax.plot(valid_workers, accuracies, marker=markers[q],
#                     color=colors[q], label=q.upper(), linewidth=1.5)

#     ax.axhline(y=0.5, color="gray", linestyle=":", label="Chance (50%)")
#     ax.set_xlabel("Worker Thread Count")
#     ax.set_ylabel("Classification Accuracy")
#     ax.set_title(f"Deterministic vs. Variable Classification (window={window_size})")
#     ax.set_ylim(0.4, 1.05)
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig("classify_accuracy_vs_threads.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print("Saved classify_accuracy_vs_threads.png")


# # ============================================================
# # PLOT 3: Feature importance per queue
# # ============================================================
# def plot_feature_importance(workers=15, window_size=200):
#     fig, axes = plt.subplots(1, len(queues), figsize=(5 * len(queues), 4),
#                              sharey=True)

#     for ax, q in zip(axes, queues):
#         df = load(q)
#         if df is None:
#             continue

#         X, y = build_feature_matrix(df, window_size, workers=workers)
#         if len(X) < 20:
#             continue

#         X_train = X.drop(columns=["trial"])
#         le = LabelEncoder()
#         y_enc = le.fit_transform(y)

#         clf = RandomForestClassifier(n_estimators=100, random_state=42)
#         clf.fit(X_train, y_enc)

#         importances = pd.Series(clf.feature_importances_,
#                                 index=X_train.columns).sort_values()
#         importances.plot.barh(ax=ax, color=colors[q])
#         ax.set_title(f"{q.upper()}")
#         ax.set_xlabel("Importance")

#     plt.suptitle(f"Feature Importances (workers={workers}, window={window_size})",
#                  fontsize=13)
#     plt.tight_layout()
#     plt.savefig("classify_feature_importance.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print("Saved classify_feature_importance.png")


# # ============================================================
# # PLOT 4: Feature distributions (det vs variable) per queue
# # ============================================================
# def plot_feature_distributions(workers=15, window_size=200):
#     features_to_plot = ["std", "cv", "autocorr_1", "kurtosis"]

#     fig, axes = plt.subplots(len(queues), len(features_to_plot),
#                              figsize=(4 * len(features_to_plot), 3.5 * len(queues)))

#     for row, q in enumerate(queues):
#         df = load(q)
#         if df is None:
#             continue

#         X, y = build_feature_matrix(df, window_size, workers=workers)
#         X["workload"] = y

#         for col, feat in enumerate(features_to_plot):
#             ax = axes[row][col]

#             det = X[X["workload"] == "deterministic"][feat].values
#             var = X[X["workload"] == "variable"][feat].values

#             ax.hist(det, bins=30, alpha=0.6, label="deterministic",
#                     color="steelblue", density=True)
#             ax.hist(var, bins=30, alpha=0.6, label="variable",
#                     color="coral", density=True)

#             if row == 0:
#                 ax.set_title(feat)
#             if col == 0:
#                 ax.set_ylabel(f"{q.upper()}\nDensity")
#             if row == len(queues) - 1:
#                 ax.set_xlabel(feat)
#             if row == 0 and col == 0:
#                 ax.legend(fontsize=7)

#     plt.suptitle(f"Feature Distributions: Deterministic vs Variable "
#                  f"(workers={workers})", fontsize=13, y=1.01)
#     plt.tight_layout()
#     plt.savefig("classify_feature_dists.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print("Saved classify_feature_dists.png")


# # ============================================================
# # SUMMARY TABLE
# # ============================================================
# def print_summary_table(workers=15):
#     print(f"\n{'Queue':<8}", end="")
#     for ws in WINDOW_SIZES:
#         print(f"{'w=' + str(ws):<12}", end="")
#     print()
#     print("-" * (8 + 12 * len(WINDOW_SIZES)))

#     for q in queues:
#         df = load(q)
#         if df is None:
#             continue

#         print(f"{q.upper():<8}", end="")
#         for ws in WINDOW_SIZES:
#             X, y = build_feature_matrix(df, ws, workers=workers)
#             if len(X) < 20 or len(np.unique(y)) < 2:
#                 print(f"{'N/A':<12}", end="")
#                 continue

#             X_train = X.drop(columns=["trial"])
#             le = LabelEncoder()
#             y_enc = le.fit_transform(y)

#             clf = RandomForestClassifier(n_estimators=100, random_state=42)
#             cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
#             scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")
#             print(f"{scores.mean():.3f}±{scores.std():.3f}  ", end="")
#         print()


# # ---- RUN ALL ----
# if __name__ == "__main__":
#     print_summary_table(workers=15)

#     plot_accuracy_vs_window(workers=15)
#     plot_accuracy_vs_threads(window_size=200)
#     plot_feature_importance(workers=15, window_size=200)
#     plot_feature_distributions(workers=15, window_size=200)


# import pandas as pd
# import numpy as np
# import matplotlib.pyplot as plt
# from scipy.signal import medfilt

# # ---- CONFIG ----
# queues = ["ms", "fc", "lprq"]
# colors = {"ms": "#1f77b4", "lprq": "#ff7f0e", "fc": "#2ca02c"}
# markers = {"ms": "o", "fc": "^", "lprq": "s"}
# workers_to_plot = 15


# def load(queue, direction):
#     fname = f"{queue}_changepoint_{direction}.csv"
#     try:
#         return pd.read_csv(fname)
#     except FileNotFoundError:
#         print(f"  {fname} not found")
#         return None


# # ---- CUSUM DETECTOR ----
# # Uses robust baseline from phase 1 (before switch_op).
# # Only scans from switch_op onward — no false positives before the switch.
# # Operates on smoothed (rolling median) input for stability.
# def cusum_detect(latencies, switch_op, threshold_sigma=5.0, burnin=400):
#     if len(latencies) < burnin + 100:
#         return -1

#     baseline = latencies[:burnin]
#     mu = np.median(baseline)
#     mad = np.median(np.abs(baseline - mu))
#     sigma = mad * 1.4826  # MAD -> std dev

#     if sigma == 0:
#         return -1

#     threshold = threshold_sigma * sigma
#     cusum_pos = 0.0

#     for i in range(switch_op, len(latencies)):
#         z = latencies[i] - mu
#         cusum_pos = max(0, cusum_pos + z)

#         if cusum_pos > threshold:
#             return i

#     return -1


# def smooth_causal(latencies, window=50):
#     """Backward-looking rolling median — no lookahead."""
#     return pd.Series(latencies).rolling(window=window, min_periods=1).median().values




# # ============================================================
# # PLOT 2: Detection delay bar chart (fixed worker count)
# # ============================================================
# def plot_detection_bar(direction="det_to_var", workers=15):
#     fig, ax = plt.subplots(figsize=(6, 4))

#     labels = []
#     delays = []

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         wdf = df[df["workers"] == workers]
#         if wdf.empty:
#             continue

#         switch_op = wdf["switch_op"].iloc[0]
#         trial_delays = []

#         for trial in wdf["trial"].unique():
#             tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#             latencies = tdf["latency"].values
#             smoothed = smooth_causal(latencies, window=50)

#             detected = cusum_detect(smoothed, switch_op,
#                                     threshold_sigma=1.0, burnin=400)
#             if detected > 0:
#                 trial_delays.append(detected - switch_op)

#         labels.append(q.upper())
#         if trial_delays:
#             delays.append(np.median(trial_delays))
#         else:
#             # Never detected — show as max possible delay
#             delays.append(switch_op)

#     ax.bar(labels, delays, color=[colors[q] for q in queues])
#     ax.set_ylabel("Median Detection Delay (ops)")

#     direction_label = direction.replace("_", " → ").replace("det", "deterministic").replace("var", "variable")
#     ax.set_title(f"Change-Point Detection Delay ({direction_label}, workers={workers})")
#     plt.tight_layout()
#     plt.savefig(f"changepoint_bar_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_bar_{direction}.png")


# # ============================================================
# # PLOT 3: Detection delay vs thread count (line plot)
# # ============================================================
# def plot_detection_vs_threads(direction="det_to_var"):
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         worker_counts = sorted(df["workers"].unique())
#         median_delays = []
#         valid_workers = []

#         for w in worker_counts:
#             wdf = df[df["workers"] == w]
#             switch_op = wdf["switch_op"].iloc[0]
#             trial_delays = []

#             for trial in wdf["trial"].unique():
#                 tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#                 latencies = tdf["latency"].values
#                 smoothed = smooth_causal(latencies, window=50)

#                 detected = cusum_detect(smoothed, switch_op,
#                                         threshold_sigma=1.0, burnin=400)
#                 if detected > 0:
#                     trial_delays.append(detected - switch_op)

#             valid_workers.append(w)
#             if trial_delays:
#                 median_delays.append(np.median(trial_delays))
#             else:
#                 median_delays.append(switch_op)

#         if valid_workers:
#             ax.plot(valid_workers, median_delays, marker=markers[q],
#                     color=colors[q], label=q.upper(), linewidth=1.5)

#     ax.set_xlabel("Worker Thread Count")
#     ax.set_ylabel("Median Detection Delay (ops)")
#     ax.set_yscale("log")

#     direction_label = direction.replace("_", " → ").replace("det", "deterministic").replace("var", "variable")
#     ax.set_title(f"Change-Point Detection Delay ({direction_label})")
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig(f"changepoint_delay_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_delay_{direction}.png")


# # ============================================================
# # PLOT 4: Detection success rate
# # ============================================================
# def plot_detection_rate(direction="det_to_var"):
#     fig, ax = plt.subplots(figsize=(8, 5))

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         worker_counts = sorted(df["workers"].unique())
#         rates = []
#         valid_workers = []

#         for w in worker_counts:
#             wdf = df[df["workers"] == w]
#             switch_op = wdf["switch_op"].iloc[0]
#             n_trials = len(wdf["trial"].unique())
#             n_detected = 0

#             for trial in wdf["trial"].unique():
#                 tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#                 latencies = tdf["latency"].values
#                 smoothed = smooth_causal(latencies, window=50)

#                 detected = cusum_detect(smoothed, switch_op,
#                                         threshold_sigma=1.0, burnin=400)
#                 if detected > 0:
#                     n_detected += 1

#             valid_workers.append(w)
#             rates.append(n_detected / n_trials)

#         if valid_workers:
#             ax.plot(valid_workers, rates, marker=markers[q],
#                     color=colors[q], label=q.upper(), linewidth=1.5)

#     ax.set_xlabel("Worker Thread Count")
#     ax.set_ylabel("Detection Rate")
#     ax.set_ylim(-0.05, 1.05)

#     direction_label = direction.replace("_", " → ").replace("det", "deterministic").replace("var", "variable")
#     ax.set_title(f"Change-Point Detection Rate ({direction_label})")
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig(f"changepoint_rate_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
#     print(f"Saved changepoint_rate_{direction}.png")
    


# def plot_delay_scatter_overtake(direction="det_to_var"):
#     overtake = {
#         "ms": {1:0,2:0,3:4,4:21,5:33,6:40,7:45,8:48,9:46,10:47,11:50,12:54,13:58,14:61,15:64,16:66},
#         "lprq": {1:0,2:2,3:4,4:6,5:7,6:8,7:8,8:9,9:12,10:15,11:17,12:19,13:20,14:20,15:20,16:21},
#         "fc": {1:0,2:6,3:13,4:18,5:20,6:22,7:24,8:25,9:26,10:29,11:30,12:32,13:33,14:35,15:36,16:37}
#     }

#     fig, ax = plt.subplots(figsize=(7, 5))

#     all_ovs = []
#     all_delays = []

#     for q in queues:
#         df = load(q, direction)
#         if df is None:
#             continue

#         ovs = []
#         delays = []

#         for w in sorted(df["workers"].unique()):
#             wdf = df[df["workers"] == w]
#             switch_op = wdf["switch_op"].iloc[0]
#             trial_delays = []

#             for trial in wdf["trial"].unique():
#                 tdf = wdf[wdf["trial"] == trial].sort_values("op_index")
#                 latencies = tdf["latency"].values
#                 smoothed = smooth_causal(latencies, window=50)
#                 detected = cusum_detect(smoothed, switch_op,
#                                         threshold_sigma=5.0, burnin=400)
#                 if detected > 0:
#                     trial_delays.append(detected - switch_op)

#             ov = overtake[q].get(w, np.nan)
#             if trial_delays and not np.isnan(ov):
#                 ovs.append(ov)
#                 delays.append(np.median(trial_delays))

#         ax.scatter(ovs, delays, marker=markers[q], color=colors[q],
#                    label=q.upper(), s=60)
#         all_ovs.extend(ovs)
#         all_delays.extend(delays)

#     # Fit and plot trendline
#     if all_ovs and all_delays:
#         from scipy.stats import pearsonr
#         r, p = pearsonr(all_ovs, all_delays)
#         z = np.polyfit(all_ovs, all_delays, 1)
#         x_line = np.linspace(min(all_ovs), max(all_ovs), 100)
#         ax.plot(x_line, np.polyval(z, x_line), color="gray", linestyle="--",
#                 label=f"r={r:.2f}, p={p:.4f}")

#     ax.set_xlabel("Overtake Percentage (less fair →)")
#     ax.set_ylabel("Median Detection Delay (ops)")
#     ax.set_title("Fairness vs. Change-Point Detection Delay")
#     ax.legend()
#     plt.tight_layout()
#     plt.savefig(f"changepoint_scatter_overtake_{direction}.png", dpi=200, bbox_inches="tight")
#     plt.show()
# # ---- RUN ALL ----
# if __name__ == "__main__":
#     for d in ["det_to_var"]:
#         print(f"\n=== {d} ===")
#         # plot_detection_bar(direction=d, workers=workers_to_plot)
#         # plot_detection_vs_threads(direction=d)
#         # plot_detection_rate(direction=d)
#         plot_delay_scatter_overtake(direction=d)


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from scipy.stats import skew, kurtosis

# ---- CONFIG ----
queues = ["ms", "fc", "lprq"]
colors = {"ms": "#1f77b4", "lprq": "#ff7f0e", "fc": "#2ca02c"}
markers = {"ms": "o", "fc": "^", "lprq": "s"}

WINDOW_SIZES = [50, 100, 200, 500]
WORKLOAD_LABELS = ["webserver", "pipeline", "interactive"]


def load(queue):
    fname = f"{queue}_fingerprint.csv"
    try:
        return pd.read_csv(fname)
    except FileNotFoundError:
        print(f"  {fname} not found")
        return None


# ---- FEATURE EXTRACTION ----
# Shape-only features — no mean/median/percentiles.
# Attacker can only exploit distributional shape, not contention level.
def extract_features(latencies):
    mu = np.mean(latencies)
    std = np.std(latencies)
    return {
        "std": std,
        "cv": std / mu if mu > 0 else 0,
        "iqr": np.percentile(latencies, 75) - np.percentile(latencies, 25),
        "skewness": skew(latencies) if std > 0 else 0,
        "kurtosis": kurtosis(latencies) if std > 0 else 0,
        "range": np.max(latencies) - np.min(latencies),
        "autocorr_1": np.corrcoef(latencies[:-1], latencies[1:])[0, 1]
                       if len(latencies) > 2 and std > 0 else 0,
    }


def build_feature_matrix(df, window_size, workers=None):
    if workers is not None:
        df = df[df["workers"] == workers]

    features = []
    labels = []

    for (wl, trial), group in df.groupby(["workload", "trial"]):
        latencies = group.sort_values("sample")["latency"].values

        p99 = np.percentile(latencies, 99)
        latencies = np.clip(latencies, 0, p99)

        step = window_size // 2
        for start in range(0, len(latencies) - window_size, step):
            window = latencies[start:start + window_size]
            feat = extract_features(window)
            feat["trial"] = trial
            features.append(feat)
            labels.append(wl)

    X = pd.DataFrame(features)
    y = np.array(labels)
    return X, y


# ============================================================
# PLOT 1: Fingerprinting accuracy vs window size per queue
# ============================================================
def plot_accuracy_vs_window(workers=15):
    fig, ax = plt.subplots(figsize=(8, 5))

    for q in queues:
        df = load(q)
        if df is None:
            continue

        accuracies = []
        stds = []

        for ws in WINDOW_SIZES:
            X, y = build_feature_matrix(df, ws, workers=workers)

            if len(X) < 20 or len(np.unique(y)) < 2:
                accuracies.append(np.nan)
                stds.append(np.nan)
                continue

            X_train = X.drop(columns=["trial"])
            le = LabelEncoder()
            y_enc = le.fit_transform(y)

            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")

            accuracies.append(scores.mean())
            stds.append(scores.std())

        ax.errorbar(WINDOW_SIZES, accuracies, yerr=stds,
                    marker=markers[q], color=colors[q],
                    label=q.upper(), capsize=3, linewidth=1.5)

    chance = 1.0 / len(WORKLOAD_LABELS)
    ax.axhline(y=chance, color="gray", linestyle=":",
               label=f"Chance ({chance:.0%})")
    ax.set_xlabel("Attacker Observation Window (# ops)")
    ax.set_ylabel("Fingerprinting Accuracy")
    ax.set_title(f"Workload Fingerprinting Accuracy (workers={workers})")
    ax.set_ylim(0.2, 1.05)
    ax.legend()
    plt.tight_layout()
    plt.savefig("fingerprint_accuracy_vs_window.png", dpi=200, bbox_inches="tight")
    plt.show()
    print("Saved fingerprint_accuracy_vs_window.png")


# ============================================================
# PLOT 2: Fingerprinting accuracy vs thread count
# ============================================================
def plot_accuracy_vs_threads(window_size=200):
    fig, ax = plt.subplots(figsize=(8, 5))

    for q in queues:
        df = load(q)
        if df is None:
            continue

        worker_counts = sorted(df["workers"].unique())
        accuracies = []
        valid_workers = []

        for w in worker_counts:
            X, y = build_feature_matrix(df, window_size, workers=w)

            if len(X) < 20 or len(np.unique(y)) < 2:
                continue

            X_train = X.drop(columns=["trial"])
            le = LabelEncoder()
            y_enc = le.fit_transform(y)

            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")

            valid_workers.append(w)
            accuracies.append(scores.mean())

        if valid_workers:
            ax.plot(valid_workers, accuracies, marker=markers[q],
                    color=colors[q], label=q.upper(), linewidth=1.5)

    chance = 1.0 / len(WORKLOAD_LABELS)
    ax.axhline(y=chance, color="gray", linestyle=":",
               label=f"Chance ({chance:.0%})")
    ax.set_xlabel("Worker Thread Count")
    ax.set_ylabel("Fingerprinting Accuracy")
    ax.set_title(f"Workload Fingerprinting Accuracy (window={window_size})")
    ax.set_ylim(0.2, 1.05)
    ax.legend()
    plt.tight_layout()
    plt.savefig("fingerprint_accuracy_vs_threads.png", dpi=200, bbox_inches="tight")
    plt.show()
    print("Saved fingerprint_accuracy_vs_threads.png")


# ============================================================
# PLOT 3: Confusion matrices per queue
# ============================================================
def plot_confusion_matrices(workers=15, window_size=200):
    fig, axes = plt.subplots(1, len(queues), figsize=(6 * len(queues), 5))

    for ax, q in zip(axes, queues):
        df = load(q)
        if df is None:
            continue

        X, y = build_feature_matrix(df, window_size, workers=workers)
        if len(X) < 20:
            continue

        X_train = X.drop(columns=["trial"])
        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        # Train/test split by trial to avoid leakage
        trials = X["trial"].values
        unique_trials = np.unique(trials)
        split = len(unique_trials) // 2
        train_trials = set(unique_trials[:split])

        train_mask = np.array([t in train_trials for t in trials])
        test_mask = ~train_mask

        if sum(test_mask) < 10:
            # Fall back to full fit if not enough trials
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train, y_enc)
            y_pred = clf.predict(X_train)
            y_true = y_enc
        else:
            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            clf.fit(X_train[train_mask], y_enc[train_mask])
            y_pred = clf.predict(X_train[test_mask])
            y_true = y_enc[test_mask]

        cm = confusion_matrix(y_true, y_pred, normalize="true")
        disp = ConfusionMatrixDisplay(cm, display_labels=le.classes_)
        disp.plot(ax=ax, cmap="Blues", values_format=".2f", colorbar=False)
        ax.set_title(f"{q.upper()}")

    plt.suptitle(f"Workload Fingerprinting Confusion Matrices\n"
                 f"(workers={workers}, window={window_size})", fontsize=13)
    plt.tight_layout()
    plt.savefig("fingerprint_confusion.png", dpi=200, bbox_inches="tight")
    plt.show()
    print("Saved fingerprint_confusion.png")


# ============================================================
# PLOT 4: Feature importance per queue
# ============================================================
def plot_feature_importance(workers=15, window_size=200):
    fig, axes = plt.subplots(1, len(queues), figsize=(5 * len(queues), 4),
                             sharey=True)

    for ax, q in zip(axes, queues):
        df = load(q)
        if df is None:
            continue

        X, y = build_feature_matrix(df, window_size, workers=workers)
        if len(X) < 20:
            continue

        X_train = X.drop(columns=["trial"])
        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_enc)

        importances = pd.Series(clf.feature_importances_,
                                index=X_train.columns).sort_values()
        importances.plot.barh(ax=ax, color=colors[q])
        ax.set_title(f"{q.upper()}")
        ax.set_xlabel("Importance")

    plt.suptitle(f"Feature Importances for Workload Fingerprinting\n"
                 f"(workers={workers}, window={window_size})", fontsize=13)
    plt.tight_layout()
    plt.savefig("fingerprint_feature_importance.png", dpi=200, bbox_inches="tight")
    plt.show()
    print("Saved fingerprint_feature_importance.png")


# ============================================================
# PLOT 5: Accuracy gap bar chart (headline figure)
# ============================================================
def plot_accuracy_gap(workers=15, window_size=200):
    """
    Single bar chart showing fingerprinting accuracy per queue.
    The gap between MS Queue and LPRQ is the key result.
    """
    fig, ax = plt.subplots(figsize=(6, 4))

    labels = []
    accs = []

    for q in queues:
        df = load(q)
        if df is None:
            continue

        X, y = build_feature_matrix(df, window_size, workers=workers)
        if len(X) < 20 or len(np.unique(y)) < 2:
            continue

        X_train = X.drop(columns=["trial"])
        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")

        labels.append(q.upper())
        accs.append(scores.mean())

    bars = ax.bar(labels, accs, color=[colors[q] for q in queues])

    chance = 1.0 / len(WORKLOAD_LABELS)
    ax.axhline(y=chance, color="gray", linestyle=":", linewidth=1.5,
               label=f"Chance ({chance:.0%})")

    # Add value labels on bars
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                f"{acc:.1%}", ha="center", va="bottom", fontsize=11)

    ax.set_ylabel("Fingerprinting Accuracy")
    ax.set_title(f"Co-Tenant Workload Fingerprinting\n"
                 f"(workers={workers}, window={window_size} ops)")
    ax.set_ylim(0, 1.15)
    ax.legend()
    plt.tight_layout()
    plt.savefig("fingerprint_accuracy_bar.png", dpi=200, bbox_inches="tight")
    plt.show()
    print("Saved fingerprint_accuracy_bar.png")


# ============================================================
# SUMMARY TABLE
# ============================================================
def print_summary_table(workers=15):
    print(f"\n{'Queue':<8}", end="")
    for ws in WINDOW_SIZES:
        print(f"{'w=' + str(ws):<12}", end="")
    print()
    print("-" * (8 + 12 * len(WINDOW_SIZES)))

    for q in queues:
        df = load(q)
        if df is None:
            continue

        print(f"{q.upper():<8}", end="")
        for ws in WINDOW_SIZES:
            X, y = build_feature_matrix(df, ws, workers=workers)
            if len(X) < 20 or len(np.unique(y)) < 2:
                print(f"{'N/A':<12}", end="")
                continue

            X_train = X.drop(columns=["trial"])
            le = LabelEncoder()
            y_enc = le.fit_transform(y)

            clf = RandomForestClassifier(n_estimators=100, random_state=42)
            cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            scores = cross_val_score(clf, X_train, y_enc, cv=cv, scoring="accuracy")
            print(f"{scores.mean():.3f}±{scores.std():.3f}  ", end="")
        print()




# ---- RUN ALL ----
if __name__ == "__main__":
    print_summary_table(workers=15)

    plot_accuracy_gap(workers=15, window_size=200)
    plot_accuracy_vs_window(workers=15)
    plot_accuracy_vs_threads(window_size=200)
    plot_confusion_matrices(workers=15, window_size=200)
    plot_feature_importance(workers=15, window_size=200)



