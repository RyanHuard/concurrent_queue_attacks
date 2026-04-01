// #include <atomic>
// #include <barrier>
// #include <chrono>
// #include <cinttypes>
// #include <cstdio>
// #include <cstdlib>
// #include <cstring>
// #include <fstream>
// #include <iostream>
// #include <string>
// #include <thread>
// #include <vector>
// #include <pthread.h>
// #include <sched.h>
// #include <unistd.h>
// #include <x86intrin.h>

// #include "LPRQ.hpp"
// #include "MSQueue.hpp"
// #include "FCQ.hpp"
// #include "sPayload.hpp"

// struct Payload {
//     int value;
// };

// inline uint64_t rdtscp() {
//     uint32_t lo, hi;
//     __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi) :: "ecx");
//     return ((uint64_t)hi << 32) | lo;
// }

// static inline void cpu_pause() {
//     __asm__ __volatile__("pause" ::: "memory");
// }

// static bool pin_thread_to_core(int core_id) {
//     cpu_set_t cpuset;
//     CPU_ZERO(&cpuset);
//     CPU_SET(core_id, &cpuset);
//     return pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) == 0;
// }


// // template <typename Queue>
// // void run(Queue& queue, bool workers_idle, const std::string& queue_type, int num_ops, int worker_threads) {
// //     std::barrier sync(worker_threads + 1);
// //     std::atomic<bool> done{false};
// //     std::atomic<int> workers_left{worker_threads};

// //     auto attacker = [&](int tid) {
// //         pin_thread_to_core(tid);
// //         std::vector<uint64_t> latencies;
// //         latencies.reserve(num_ops);

// //         sync.arrive_and_wait();

// //         // Warmup phase for attacker
// //         for (int i = 0; i < 1000; i++) {
// //             Payload* payload = new Payload(tid);
// //             Node<Payload>* item = new Node<Payload>(payload);
// //             queue.enqueue(item, tid);
// //             Node<Payload>* result = queue.dequeue(tid);
// //         }

// //         for (int i = 0; i < num_ops; i++) {
// //             Payload* payload = new Payload(tid);
// //             Node<Payload>* item = new Node<Payload>(payload);

// //             uint64_t start = rdtscp();
// //             queue.enqueue(item, tid);
// //             uint64_t end = rdtscp();

// //             latencies.push_back(end - start);
// //         }

// //         done.store(true, std::memory_order_release);

// //         std::string suffix = !workers_idle ? "_latencies_active.csv" : "_latencies_idle.csv";
// //         std::string filename = queue_type + suffix;
// //         bool file_exists = std::ifstream(filename).good();
// //         std::ofstream file(filename, std::ios::app);

// //         if (!file_exists) {
// //             file << "workers,sample,latency\n";
// //         }

// //         for (size_t i = 0; i < latencies.size(); i++) {
// //             file << worker_threads << "," << i << "," 
// //                  << latencies[i] << "\n";
// //         }
// //     };

// //     auto worker = [&](int tid) {
// //         pin_thread_to_core(tid);
// //         sync.arrive_and_wait();

// //         if (!workers_idle) {
// //             // Warmup
// //             for (int i = 0; i < 1000; i++) {
// //                 Payload* payload = new Payload(tid);
// //                 Node<Payload>* item = new Node<Payload>(payload);
// //                 queue.enqueue(item, tid);
// //                 Node<Payload>* result = queue.dequeue(tid);
// //             }

// //             // Actual work
// //             while (!done.load(std::memory_order_relaxed)) {
// //                 Payload* payload = new Payload(tid);
// //                 Node<Payload>* item = new Node<Payload>(payload);
// //                 queue.enqueue(item, tid);
// //                 Node<Payload>* result = queue.dequeue(tid);
// //             }
// //         }
// //         else {
// //             // "Idle" 
// //             while (!done.load(std::memory_order_relaxed)) {
// //                // asm volatile("pause" ::: "memory");
// //                  Payload* payload = new Payload(tid);
// //                 Node<Payload>* item = new Node<Payload>(payload);
// //                queue.enqueue(item, tid);
// //                for (int i = 0; i < 500; i++) cpu_pause();
// //                 Node<Payload>* result = queue.dequeue(tid);
// //             }
// //         }


// //         if (workers_left.fetch_sub(1, std::memory_order_acq_rel) == 1) {
// //             done.store(true, std::memory_order_release);
// //         }
// //     };

// //     std::vector<std::thread> threads;
// //     for (int i = 0; i < worker_threads; i++) {
// //         threads.emplace_back(worker, i);
// //     }
// //     threads.emplace_back(attacker, worker_threads);

// //     for (auto& t : threads) {
// //         t.join();
// //     }
// // }

// // ---- CHANGE-POINT BENCHMARK ----
// // Workers start in one phase (idle or active), then switch mid-run.
// // The attacker logs timestamped enqueue latencies throughout.
// // Goal: measure how quickly an attacker can detect the workload transition
// // from their own latency stream alone.
 
// template <typename Queue>
// void run_changepoint(Queue& queue, const std::string& queue_type,
//                      int num_ops, int worker_threads, int trial,
//                      bool start_idle) {
//     // start_idle=true:  workers go idle -> active  (transition at midpoint)
//     // start_idle=false: workers go active -> idle
 
//     std::barrier sync(worker_threads + 1);
//     std::atomic<bool> done{false};
 
//     // Phase flag: false = phase 1, true = phase 2
//     // Attacker flips this at the midpoint of its ops
//     std::atomic<bool> phase2{false};
 
//     // Record the attacker's op index at which the switch was signaled
//     int switch_op = num_ops / 2;
 
//     auto attacker = [&](int tid) {
//         pin_thread_to_core(tid);
 
//         struct Sample {
//             uint64_t latency;
//             int op_index;
//         };
 
//         std::vector<Sample> samples;
//         samples.reserve(num_ops);
 
//         sync.arrive_and_wait();
 
//         // Warmup
//         for (int i = 0; i < 1000; i++) {
//             Payload* payload = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(payload);
//             queue.enqueue(item, tid);
//             Node<Payload>* result = queue.dequeue(tid);
//         }
 
//         for (int i = 0; i < num_ops; i++) {
//             // Signal phase transition at midpoint
//             if (i == switch_op) {
//                 phase2.store(true, std::memory_order_release);
//             }
 
//             Payload* payload = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(payload);
 
//             uint64_t start = rdtscp();
//             queue.enqueue(item, tid);
//             uint64_t end = rdtscp();
 
//             samples.push_back({end - start, i});
//         }
 
//         done.store(true, std::memory_order_release);
 
//         // Write CSV
//         std::string direction = start_idle ? "idle_to_active" : "active_to_idle";
//         std::string filename = queue_type + "_changepoint_" + direction + ".csv";
 
//         // Check if file exists (for appending across worker counts / trials)
//         bool file_exists = std::ifstream(filename).good();
//         std::ofstream file(filename, std::ios::app);
 
//         if (!file_exists) {
//             file << "workers,trial,op_index,latency,switch_op\n";
//         }
 
//         for (auto& s : samples) {
//             file << worker_threads << ","
//                  << trial << ","
//                  << s.op_index << ","
//                  << s.latency << ","
//                  << switch_op << "\n";
//         }
//     };
 
//     auto worker = [&](int tid) {
//         pin_thread_to_core(tid);
//         sync.arrive_and_wait();
 
//         // Warmup (always active)
//         for (int i = 0; i < 1000; i++) {
//             Payload* payload = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(payload);
//             queue.enqueue(item, tid);
//             Node<Payload>* result = queue.dequeue(tid);
//         }
 
//         while (!done.load(std::memory_order_relaxed)) {
//             bool in_phase2 = phase2.load(std::memory_order_relaxed);
 
//             // Determine current behavior
//             bool currently_idle;
//             if (start_idle) {
//                 currently_idle = !in_phase2;  // idle first, then active
//             } else {
//                 currently_idle = in_phase2;   // active first, then idle
//             }
 
//             Payload* payload = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(payload);
//             queue.enqueue(item, tid);
 
//             if (currently_idle) {
//                 for (int i = 0; i < 500; i++) cpu_pause();
//             }
 
//             Node<Payload>* result = queue.dequeue(tid);
//         }
//     };
 
//     std::vector<std::thread> threads;
//     for (int i = 0; i < worker_threads; i++) {
//         threads.emplace_back(worker, i);
//     }
//     threads.emplace_back(attacker, worker_threads);
 
//     for (auto& t : threads) {
//         t.join();
//     }
// }


// // int main(int argc, char* argv[]) {
// //     int num_ops = 10000; // per-thread
// //     int max_workers = 16;
// //     int trials = 1;
// //     std::string queue_type = "ms";

// //     // Parse args
// //     for (int i = 1; i < argc; i++) {
// //         std::string arg = argv[i];
// //         if (arg.rfind("--queue=", 0) == 0) queue_type = arg.substr(8);
// //         if (arg.rfind("--ops=", 0) == 0) num_ops = std::stoi(arg.substr(6));
// //         if (arg.rfind("--threads=", 0) == 0) max_workers = std::stoi(arg.substr(10));
// //     }

// //     // Clean the CSVs from previous runs
// //     for (const std::string& condition : {"latencies_idle.csv", "latencies_active.csv"}) {
// //         std::remove((queue_type + "_" + condition).c_str());
// //     }

// //     for (int workers = 2; workers <= max_workers; workers++) {
// //      //   for (int trial = 0; trial < trials; trial++) {
// //             if (queue_type == "ms") {
// //                 MSQueue<Payload> idle_queue(new Node<Payload>());
// //                 MSQueue<Payload> active_queue(new Node<Payload>());
// //                 run(idle_queue, true, queue_type, num_ops, workers);
// //                 run(active_queue, false, queue_type, num_ops, workers);
// //             } else if (queue_type == "lprq") {
// //                 LPRQ<Node<Payload>> idle_queue(nullptr);
// //                 LPRQ<Node<Payload>> active_queue(nullptr);
// //                 run(idle_queue, true, queue_type, num_ops, workers);
// //                 run(active_queue, false, queue_type, num_ops, workers);
// //             }
// //             else if (queue_type == "fc") {
// //                 FlatCombiningQueue<Node<Payload>> idle_queue(workers + 1);
// //                 FlatCombiningQueue<Node<Payload>> active_queue(workers + 1);
// //                 run(idle_queue, true, queue_type, num_ops, workers);
// //                 run(active_queue, false, queue_type, num_ops, workers);
// //             }
// //   //  }

// //     }

// //     return 0;
// // }


// int main(int argc, char* argv[]) {
//     int num_ops = 20000;      // more ops so each phase has enough samples
//     int max_workers = 15;
//     int min_workers = 7;      // focus on higher contention where signal is clearest
//     int trials = 50;
//     std::string queue_type = "ms";
 
//     for (int i = 1; i < argc; i++) {
//         std::string arg = argv[i];
//         if (arg.rfind("--queue=", 0) == 0)   queue_type = arg.substr(8);
//         if (arg.rfind("--ops=", 0) == 0)     num_ops = std::stoi(arg.substr(6));
//         if (arg.rfind("--threads=", 0) == 0) max_workers = std::stoi(arg.substr(10));
//         if (arg.rfind("--trials=", 0) == 0)  trials = std::stoi(arg.substr(9));
//         if (arg.rfind("--min-threads=", 0) == 0) min_workers = std::stoi(arg.substr(14));
//     }
 
//     // Clean CSVs from previous runs
//     for (const std::string& direction : {"idle_to_active", "active_to_idle"}) {
//         std::remove((queue_type + "_changepoint_" + direction + ".csv").c_str());
//     }
 
//     for (int workers = min_workers; workers <= max_workers; workers++) {
//         for (int trial = 0; trial < trials; trial++) {
//             std::cout << queue_type << " | workers=" << workers
//                       << " trial=" << trial << std::endl;
 
//             // idle -> active transition
//             if (queue_type == "ms") {
//                 MSQueue<Payload> q1(new Node<Payload>());
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 MSQueue<Payload> q2(new Node<Payload>());
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             } else if (queue_type == "lprq") {
//                 LPRQ<Node<Payload>> q1(nullptr);
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 LPRQ<Node<Payload>> q2(nullptr);
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             } else if (queue_type == "fc") {
//                 FlatCombiningQueue<Node<Payload>> q1(workers + 1);
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 FlatCombiningQueue<Node<Payload>> q2(workers + 1);
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             }
//         }
//     }
 
//     return 0;
// }

// #include <atomic>
// #include <barrier>
// #include <chrono>
// #include <cinttypes>
// #include <cstdio>
// #include <cstdlib>
// #include <cstring>
// #include <fstream>
// #include <iostream>
// #include <random>
// #include <string>
// #include <thread>
// #include <vector>
// #include <pthread.h>
// #include <sched.h>
// #include <unistd.h>
// #include <x86intrin.h>

// #include "LPRQ.hpp"
// #include "MSQueue.hpp"
// #include "FCQ.hpp"
// #include "sPayload.hpp"

// struct Payload {
//     int value;
// };

// inline uint64_t rdtscp() {
//     uint32_t lo, hi;
//     __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi) :: "ecx");
//     return ((uint64_t)hi << 32) | lo;
// }

// static inline void cpu_pause() {
//     __asm__ __volatile__("pause" ::: "memory");
// }

// static bool pin_thread_to_core(int core_id) {
//     cpu_set_t cpuset;
//     CPU_ZERO(&cpuset);
//     CPU_SET(core_id, &cpuset);
//     return pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) == 0;
// }

// // ---- WORKLOAD TYPES ----
// // Both do the same number of enqueue/dequeue pairs on average.
// // DETERMINISTIC: fixed pause of MEAN_PAUSE between each pair
// // VARIABLE: exponentially distributed pause with mean = MEAN_PAUSE
// //
// // Equal mean contention. Only difference is temporal pattern.

// enum class Workload { DETERMINISTIC, VARIABLE };

// static const char* workload_name(Workload w) {
//     return w == Workload::DETERMINISTIC ? "deterministic" : "variable";
// }

// static constexpr int MEAN_PAUSE = 200;

// template <typename Queue>
// void worker_loop(Queue& queue, int tid, Workload workload,
//                  std::atomic<bool>& done) {
//     std::mt19937 rng(tid * 7919 + static_cast<int>(workload));
//     std::exponential_distribution<double> exp_dist(1.0 / MEAN_PAUSE);

//     while (!done.load(std::memory_order_relaxed)) {
//         Payload* p = new Payload{tid};
//         Node<Payload>* item = new Node<Payload>(p);
//         queue.enqueue(item, tid);
//         Node<Payload>* result = queue.dequeue(tid);

//         int pause_iters;
//         if (workload == Workload::DETERMINISTIC) {
//             pause_iters = MEAN_PAUSE;
//         } else {
//             pause_iters = static_cast<int>(exp_dist(rng));
//             if (pause_iters > MEAN_PAUSE * 10) pause_iters = MEAN_PAUSE * 10;
//         }

//         for (int i = 0; i < pause_iters; i++) {
//             cpu_pause();
//         }
//     }
// }

// template <typename Queue>
// void run_classify(Queue& queue, Workload workload, const std::string& queue_type,
//                   int num_ops, int worker_threads, int trial) {

//     std::barrier sync(worker_threads + 1);
//     std::atomic<bool> done{false};

//     auto attacker = [&](int tid) {
//         pin_thread_to_core(tid);
//         std::vector<uint64_t> latencies;
//         latencies.reserve(num_ops);

//         sync.arrive_and_wait();

//         // Warmup
//         for (int i = 0; i < 1000; i++) {
//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);
//             queue.enqueue(item, tid);
//             queue.dequeue(tid);
//         }

//         for (int i = 0; i < num_ops; i++) {
//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);

//             uint64_t start = rdtscp();
//             queue.enqueue(item, tid);
//             uint64_t end = rdtscp();

//             latencies.push_back(end - start);
//         }

//         done.store(true, std::memory_order_release);

//         // Write CSV
//         std::string filename = queue_type + "_classify.csv";
//         bool file_exists = std::ifstream(filename).good();
//         std::ofstream file(filename, std::ios::app);

//         if (!file_exists) {
//             file << "workers,trial,workload,sample,latency\n";
//         }

//         for (size_t i = 0; i < latencies.size(); i++) {
//             file << worker_threads << ","
//                  << trial << ","
//                  << workload_name(workload) << ","
//                  << i << ","
//                  << latencies[i] << "\n";
//         }
//     };

//     auto worker = [&](int tid) {
//         pin_thread_to_core(tid);
//         sync.arrive_and_wait();

//         // Warmup
//         for (int i = 0; i < 1000; i++) {
//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);
//             queue.enqueue(item, tid);
//             queue.dequeue(tid);
//         }

//         worker_loop(queue, tid, workload, done);
//     };

//     std::vector<std::thread> threads;
//     for (int i = 0; i < worker_threads; i++) {
//         threads.emplace_back(worker, i);
//     }
//     threads.emplace_back(attacker, worker_threads);

//     for (auto& t : threads) {
//         t.join();
//     }
// }


// int main(int argc, char* argv[]) {
//     int num_ops = 10000;
//     int max_workers = 15;
//     int min_workers = 2;
//     int trials = 10;
//     std::string queue_type = "ms";

//     for (int i = 1; i < argc; i++) {
//         std::string arg = argv[i];
//         if (arg.rfind("--queue=", 0) == 0)       queue_type = arg.substr(8);
//         if (arg.rfind("--ops=", 0) == 0)         num_ops = std::stoi(arg.substr(6));
//         if (arg.rfind("--threads=", 0) == 0)     max_workers = std::stoi(arg.substr(10));
//         if (arg.rfind("--min-threads=", 0) == 0) min_workers = std::stoi(arg.substr(14));
//         if (arg.rfind("--trials=", 0) == 0)      trials = std::stoi(arg.substr(9));
//     }

//     std::remove((queue_type + "_classify.csv").c_str());

//     for (int workers = min_workers; workers <= max_workers; workers++) {
//         for (int trial = 0; trial < trials; trial++) {
//             for (auto wl : {Workload::DETERMINISTIC, Workload::VARIABLE}) {
//                 std::cout << queue_type << " | workers=" << workers
//                           << " trial=" << trial
//                           << " workload=" << workload_name(wl) << std::endl;

//                 if (queue_type == "ms") {
//                     MSQueue<Payload> q(new Node<Payload>());
//                     run_classify(q, wl, queue_type, num_ops, workers, trial);
//                 } else if (queue_type == "lprq") {
//                     LPRQ<Node<Payload>> q(nullptr);
//                     run_classify(q, wl, queue_type, num_ops, workers, trial);
//                 } else if (queue_type == "fc") {
//                     FlatCombiningQueue<Node<Payload>> q(workers + 1);
//                     run_classify(q, wl, queue_type, num_ops, workers, trial);
//                 }
//             }
//         }
//     }

//     return 0;
// }


// #include <atomic>
// #include <barrier>
// #include <chrono>
// #include <cinttypes>
// #include <cstdio>
// #include <cstdlib>
// #include <cstring>
// #include <fstream>
// #include <iostream>
// #include <random>
// #include <string>
// #include <thread>
// #include <vector>
// #include <pthread.h>
// #include <sched.h>
// #include <unistd.h>
// #include <x86intrin.h>

// #include "LPRQ.hpp"
// #include "MSQueue.hpp"
// #include "FCQ.hpp"
// #include "sPayload.hpp"

// struct Payload {
//     int value;
// };

// inline uint64_t rdtscp() {
//     uint32_t lo, hi;
//     __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi) :: "ecx");
//     return ((uint64_t)hi << 32) | lo;
// }

// static inline void cpu_pause() {
//     __asm__ __volatile__("pause" ::: "memory");
// }

// static bool pin_thread_to_core(int core_id) {
//     cpu_set_t cpuset;
//     CPU_ZERO(&cpuset);
//     CPU_SET(core_id, &cpuset);
//     return pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) == 0;
// }

// // ---- WORKLOAD ----
// // Same design as classification experiment:
// // DETERMINISTIC: fixed pause of MEAN_PAUSE between each enqueue/dequeue pair
// // VARIABLE: exponentially distributed pause with same mean
// //
// // Workers start in one mode, then switch at the midpoint.
// // Attacker logs continuous latency trace throughout.

// static constexpr int MEAN_PAUSE = 200;

// template <typename Queue>
// void run_changepoint(Queue& queue, const std::string& queue_type,
//                      int num_ops, int worker_threads, int trial,
//                      bool start_deterministic) {
//     // start_deterministic=true:  deterministic -> variable
//     // start_deterministic=false: variable -> deterministic

//     std::barrier sync(worker_threads + 1);
//     std::atomic<bool> done{false};
//     std::atomic<bool> phase2{false};

//     int switch_op = num_ops / 2;

//     auto attacker = [&](int tid) {
//         pin_thread_to_core(tid);

//         struct Sample {
//             uint64_t latency;
//             int op_index;
//         };

//         std::vector<Sample> samples;
//         samples.reserve(num_ops);

//         sync.arrive_and_wait();

//         // Warmup
//         for (int i = 0; i < 1000; i++) {
//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);
//             queue.enqueue(item, tid);
//             queue.dequeue(tid);
//         }

//         for (int i = 0; i < num_ops; i++) {
//             if (i == switch_op) {
//                 phase2.store(true, std::memory_order_release);
//             }

//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);

//             uint64_t start = rdtscp();
//             queue.enqueue(item, tid);
//             uint64_t end = rdtscp();

//             samples.push_back({end - start, i});
//         }

//         done.store(true, std::memory_order_release);

//         // Write CSV
//         std::string direction = start_deterministic ? "det_to_var" : "var_to_det";
//         std::string filename = queue_type + "_changepoint_" + direction + ".csv";

//         bool file_exists = std::ifstream(filename).good();
//         std::ofstream file(filename, std::ios::app);

//         if (!file_exists) {
//             file << "workers,trial,op_index,latency,switch_op\n";
//         }

//         for (auto& s : samples) {
//             file << worker_threads << ","
//                  << trial << ","
//                  << s.op_index << ","
//                  << s.latency << ","
//                  << switch_op << "\n";
//         }
//     };

//     auto worker = [&](int tid) {
//         pin_thread_to_core(tid);
//         std::mt19937 rng(tid * 7919 + trial * 31);
//         std::exponential_distribution<double> exp_dist(1.0 / MEAN_PAUSE);

//         sync.arrive_and_wait();

//         // Warmup (deterministic)
//         for (int i = 0; i < 1000; i++) {
//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);
//             queue.enqueue(item, tid);
//             queue.dequeue(tid);
//         }

//         while (!done.load(std::memory_order_relaxed)) {
//             bool in_phase2 = phase2.load(std::memory_order_relaxed);

//             // Determine current workload
//             bool use_deterministic;
//             if (start_deterministic) {
//                 use_deterministic = !in_phase2;  // det first, then var
//             } else {
//                 use_deterministic = in_phase2;   // var first, then det
//             }

//             Payload* p = new Payload{tid};
//             Node<Payload>* item = new Node<Payload>(p);
//             queue.enqueue(item, tid);
//             Node<Payload>* result = queue.dequeue(tid);

//             int pause_iters;
//             if (use_deterministic) {
//                 pause_iters = MEAN_PAUSE;
//             } else {
//                 pause_iters = static_cast<int>(exp_dist(rng));
//                 if (pause_iters > MEAN_PAUSE * 10) pause_iters = MEAN_PAUSE * 10;
//             }

//             for (int i = 0; i < pause_iters; i++) {
//                 cpu_pause();
//             }
//         }
//     };

//     std::vector<std::thread> threads;
//     for (int i = 0; i < worker_threads; i++) {
//         threads.emplace_back(worker, i);
//     }
//     threads.emplace_back(attacker, worker_threads);

//     for (auto& t : threads) {
//         t.join();
//     }
// }


// int main(int argc, char* argv[]) {
//     int num_ops = 20000;
//     int max_workers = 16;
//     int min_workers = 4;
//     int trials = 100;
//     std::string queue_type = "ms";

//     for (int i = 1; i < argc; i++) {
//         std::string arg = argv[i];
//         if (arg.rfind("--queue=", 0) == 0)       queue_type = arg.substr(8);
//         if (arg.rfind("--ops=", 0) == 0)         num_ops = std::stoi(arg.substr(6));
//         if (arg.rfind("--threads=", 0) == 0)     max_workers = std::stoi(arg.substr(10));
//         if (arg.rfind("--min-threads=", 0) == 0) min_workers = std::stoi(arg.substr(14));
//         if (arg.rfind("--trials=", 0) == 0)      trials = std::stoi(arg.substr(9));
//     }

//     // Clean CSVs
//     for (const std::string& direction : {"det_to_var", "var_to_det"}) {
//         std::remove((queue_type + "_changepoint_" + direction + ".csv").c_str());
//     }

//     for (int workers = min_workers; workers <= max_workers; workers++) {
//         for (int trial = 0; trial < trials; trial++) {
//             std::cout << queue_type << " | workers=" << workers
//                       << " trial=" << trial << std::endl;

//             if (queue_type == "ms") {
//                 MSQueue<Payload> q1(new Node<Payload>());
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 MSQueue<Payload> q2(new Node<Payload>());
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             } else if (queue_type == "lprq") {
//                 LPRQ<Node<Payload>> q1(nullptr);
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 LPRQ<Node<Payload>> q2(nullptr);
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             } else if (queue_type == "fc") {
//                 FlatCombiningQueue<Node<Payload>> q1(workers + 1);
//                 run_changepoint(q1, queue_type, num_ops, workers, trial, true);
//                 FlatCombiningQueue<Node<Payload>> q2(workers + 1);
//                 run_changepoint(q2, queue_type, num_ops, workers, trial, false);
//             }
//         }
//     }

//     return 0;
// }

#include <atomic>
#include <barrier>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <random>
#include <string>
#include <thread>
#include <vector>
#include <pthread.h>
#include <sched.h>
#include <unistd.h>
#include <x86intrin.h>

#include "LPRQ.hpp"
#include "MSQueue.hpp"
#include "FCQ.hpp"
#include "sPayload.hpp"

struct Payload {
    int value;
};

inline uint64_t rdtscp() {
    uint32_t lo, hi;
    __asm__ __volatile__("rdtscp" : "=a"(lo), "=d"(hi) :: "ecx");
    return ((uint64_t)hi << 32) | lo;
}

static inline void cpu_pause() {
    __asm__ __volatile__("pause" ::: "memory");
}

static bool pin_thread_to_core(int core_id) {
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(core_id, &cpuset);
    return pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) == 0;
}

// ============================================================
// WORKLOAD PROFILES — Multi-Tenant Shared Task Queue
//
// Scenario: multiple tenants share a worker-pool task queue.
// An attacker co-tenant probes the queue at a steady rate.
// The victim tenant's application class determines its
// enqueue/dequeue pattern.
//
// All profiles calibrated to the same MEAN_PAUSE so average
// contention is equal across conditions.
// ============================================================

enum class Workload { WEBSERVER, PIPELINE, INTERACTIVE };

static const char* workload_name(Workload w) {
    switch (w) {
        case Workload::WEBSERVER:    return "webserver";
        case Workload::PIPELINE:     return "pipeline";
        case Workload::INTERACTIVE:  return "interactive";
    }
    return "unknown";
}

// Mean pause in pause-loop iterations between operations.
// All workloads average to this value.
static constexpr int MEAN_PAUSE = 200;

// Pipeline burst parameters
static constexpr int PIPELINE_BURST_SIZE = 20;    // ops per burst
static constexpr int PIPELINE_BURST_PAUSE = 10;   // short pause within burst
// Long pause after burst to maintain same mean:
// mean = (BURST_SIZE * BURST_PAUSE + LONG_PAUSE) / (BURST_SIZE + 1)
// Solve: LONG_PAUSE = MEAN_PAUSE * (BURST_SIZE + 1) - BURST_SIZE * BURST_PAUSE
static constexpr int PIPELINE_LONG_PAUSE =
    MEAN_PAUSE * (PIPELINE_BURST_SIZE + 1) - PIPELINE_BURST_SIZE * PIPELINE_BURST_PAUSE;

template <typename Queue>
void worker_loop(Queue& queue, int tid, Workload workload,
                 std::atomic<bool>& done) {
    std::mt19937 rng(tid * 7919 + static_cast<int>(workload));
    std::exponential_distribution<double> exp_dist(1.0 / MEAN_PAUSE);

    int burst_counter = 0;

    while (!done.load(std::memory_order_relaxed)) {
        // All workloads do an enqueue/dequeue pair
        Payload* p = new Payload{tid};
        Node<Payload>* item = new Node<Payload>(p);
        queue.enqueue(item, tid);
        Node<Payload>* result = queue.dequeue(tid);

        int pause_iters;

        switch (workload) {
            case Workload::WEBSERVER: {
                // Steady API request handling — constant inter-arrival
                pause_iters = MEAN_PAUSE;
                break;
            }

            case Workload::PIPELINE: {
                // Periodic batch ingestion:
                // Rapid burst of BURST_SIZE ops with short pauses,
                // then a long quiet period. Same mean overall.
                burst_counter++;
                if (burst_counter < PIPELINE_BURST_SIZE) {
                    pause_iters = PIPELINE_BURST_PAUSE;
                } else {
                    pause_iters = PIPELINE_LONG_PAUSE;
                    burst_counter = 0;
                }
                break;
            }

            case Workload::INTERACTIVE: {
                // Human-triggered sporadic events — exponential gaps
                pause_iters = static_cast<int>(exp_dist(rng));
                if (pause_iters > MEAN_PAUSE * 10) pause_iters = MEAN_PAUSE * 10;
                break;
            }
        }

        for (int i = 0; i < pause_iters; i++) {
            cpu_pause();
        }
    }
}

template <typename Queue>
void run_fingerprint(Queue& queue, Workload workload, const std::string& queue_type,
                     int num_ops, int worker_threads, int trial) {

    std::barrier sync(worker_threads + 1);
    std::atomic<bool> done{false};

    auto attacker = [&](int tid) {
        pin_thread_to_core(tid);
        std::vector<uint64_t> latencies;
        latencies.reserve(num_ops);

        sync.arrive_and_wait();

        // Warmup
        for (int i = 0; i < 1000; i++) {
            Payload* p = new Payload{tid};
            Node<Payload>* item = new Node<Payload>(p);
            queue.enqueue(item, tid);
            queue.dequeue(tid);
        }

        // Attacker probes at steady rate (simulates legitimate co-tenant)
        for (int i = 0; i < num_ops; i++) {
            Payload* p = new Payload{tid};
            Node<Payload>* item = new Node<Payload>(p);

            uint64_t start = rdtscp();
            queue.enqueue(item, tid);
            uint64_t end = rdtscp();

            latencies.push_back(end - start);

            // Attacker has its own steady work rate
            for (int j = 0; j < 100; j++) cpu_pause();
        }

        done.store(true, std::memory_order_release);

        // Write CSV
        std::string filename = queue_type + "_fingerprint.csv";
        bool file_exists = std::ifstream(filename).good();
        std::ofstream file(filename, std::ios::app);

        if (!file_exists) {
            file << "workers,trial,workload,sample,latency\n";
        }

        for (size_t i = 0; i < latencies.size(); i++) {
            file << worker_threads << ","
                 << trial << ","
                 << workload_name(workload) << ","
                 << i << ","
                 << latencies[i] << "\n";
        }
    };

    auto worker = [&](int tid) {
        pin_thread_to_core(tid);
        sync.arrive_and_wait();

        // Warmup
        for (int i = 0; i < 1000; i++) {
            Payload* p = new Payload{tid};
            Node<Payload>* item = new Node<Payload>(p);
            queue.enqueue(item, tid);
            queue.dequeue(tid);
        }

        worker_loop(queue, tid, workload, done);
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < worker_threads; i++) {
        threads.emplace_back(worker, i);
    }
    threads.emplace_back(attacker, worker_threads);

    for (auto& t : threads) {
        t.join();
    }
}


int main(int argc, char* argv[]) {
    int num_ops = 10000;
    int max_workers = 15;
    int min_workers = 7;
    int trials = 10;
    std::string queue_type = "ms";

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg.rfind("--queue=", 0) == 0)       queue_type = arg.substr(8);
        if (arg.rfind("--ops=", 0) == 0)         num_ops = std::stoi(arg.substr(6));
        if (arg.rfind("--threads=", 0) == 0)     max_workers = std::stoi(arg.substr(10));
        if (arg.rfind("--min-threads=", 0) == 0) min_workers = std::stoi(arg.substr(14));
        if (arg.rfind("--trials=", 0) == 0)      trials = std::stoi(arg.substr(9));
    }

    std::remove((queue_type + "_fingerprint.csv").c_str());

    for (int workers = min_workers; workers <= max_workers; workers++) {
        for (int trial = 0; trial < trials; trial++) {
            for (auto wl : {Workload::WEBSERVER, Workload::PIPELINE, Workload::INTERACTIVE}) {
                std::cout << queue_type << " | workers=" << workers
                          << " trial=" << trial
                          << " workload=" << workload_name(wl) << std::endl;

                if (queue_type == "ms") {
                    MSQueue<Payload> q(new Node<Payload>());
                    run_fingerprint(q, wl, queue_type, num_ops, workers, trial);
                } else if (queue_type == "lprq") {
                    LPRQ<Node<Payload>> q(nullptr);
                    run_fingerprint(q, wl, queue_type, num_ops, workers, trial);
                } else if (queue_type == "fc") {
                    FlatCombiningQueue<Node<Payload>> q(workers + 1);
                    run_fingerprint(q, wl, queue_type, num_ops, workers, trial);
                }
            }
        }
    }

    return 0;
}