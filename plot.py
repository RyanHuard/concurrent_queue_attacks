import pandas as pd
import matplotlib.pyplot as plt

idle = pd.read_csv("latencies_idle.csv")
active = pd.read_csv("latencies_active.csv")

plt.hist(idle["latency"], bins=50, label="idle")
plt.hist(active["latency"], bins=50, label="active")
plt.xlabel("Enqueue Latency (cycles)")
plt.ylabel("Frequency")
plt.legend()
plt.title("Attacker Enqueue Latency: Idle vs Active Workers (4 threads)")
plt.xlim(0, 1000)
plt.savefig("latency_comparison.png")
plt.show()