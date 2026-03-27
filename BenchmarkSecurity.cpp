#include <atomic>
#include <barrier>
#include <chrono>
#include <cinttypes>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
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


template <typename Queue>
void run(Queue& queue, bool workers_idle, const std::string& queue_type, int num_ops, int worker_threads) {
    std::barrier sync(worker_threads + 1);
    std::atomic<bool> done{false};
    std::atomic<int> workers_left{worker_threads};

    auto attacker = [&](int tid) {
        pin_thread_to_core(tid);
        std::vector<uint64_t> latencies;
        latencies.reserve(num_ops);

        sync.arrive_and_wait();

        // Warmup phase for attacker
        for (int i = 0; i < 1000; i++) {
            Payload* payload = new Payload(tid);
            Node<Payload>* item = new Node<Payload>(payload);
            queue.enqueue(item, tid);
            Node<Payload>* result = queue.dequeue(tid);
        }

        for (int i = 0; i < num_ops; i++) {
            Payload* payload = new Payload(tid);
            Node<Payload>* item = new Node<Payload>(payload);

            uint64_t start = rdtscp();
            queue.enqueue(item, tid);
            uint64_t end = rdtscp();

            latencies.push_back(end - start);
        }

        done.store(true, std::memory_order_release);

        std::string suffix = !workers_idle ? "_latencies_active.csv" : "_latencies_idle.csv";
        std::string filename = queue_type + suffix;
        bool file_exists = std::ifstream(filename).good();
        std::ofstream file(filename, std::ios::app);

        if (!file_exists) {
            file << "workers,sample,latency\n";
        }

        for (size_t i = 0; i < latencies.size(); i++) {
            file << worker_threads << "," << i << "," 
                 << latencies[i] << "\n";
        }
    };

    auto worker = [&](int tid) {
        pin_thread_to_core(tid);
        sync.arrive_and_wait();

        if (!workers_idle) {
            // Warmup
            for (int i = 0; i < 1000; i++) {
                Payload* payload = new Payload(tid);
                Node<Payload>* item = new Node<Payload>(payload);
                queue.enqueue(item, tid);
                Node<Payload>* result = queue.dequeue(tid);
            }

            // Actual work
            while (!done.load(std::memory_order_relaxed)) {
                Payload* payload = new Payload(tid);
                Node<Payload>* item = new Node<Payload>(payload);
                queue.enqueue(item, tid);
                Node<Payload>* result = queue.dequeue(tid);
            }
        }
        else {
            // Idle case: just burn a little time so structure matches better
            while (!done.load(std::memory_order_relaxed)) {
                asm volatile("pause" ::: "memory");
            }
        }


        if (workers_left.fetch_sub(1, std::memory_order_acq_rel) == 1) {
            done.store(true, std::memory_order_release);
        }
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
    int num_ops = 10000; // per-thread
    int max_workers = 15;
    std::string queue_type = "ms";

    // Parse args
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg.rfind("--queue=", 0) == 0) queue_type = arg.substr(8);
        if (arg.rfind("--ops=", 0) == 0) num_ops = std::stoi(arg.substr(6));
        if (arg.rfind("--threads=", 0) == 0) max_workers = std::stoi(arg.substr(10));
    }

    // Clean the CSVs from previous runs
    for (const std::string& condition : {"latencies_idle.csv", "latencies_active.csv"}) {
        std::remove((queue_type + "_" + condition).c_str());
    }

    for (int workers = 2; workers <= max_workers; workers++) {
            std::cout << workers;
        if (queue_type == "ms") {
            MSQueue<Payload> idle_queue(new Node<Payload>());
            MSQueue<Payload> active_queue(new Node<Payload>());
            run(idle_queue, true, queue_type, num_ops, workers);
            run(active_queue, false, queue_type, num_ops, workers);
        } else if (queue_type == "lprq") {
            LPRQ<Node<Payload>> idle_queue(nullptr);
            LPRQ<Node<Payload>> active_queue(nullptr);
            run(idle_queue, true, queue_type, num_ops, workers);
            run(active_queue, false, queue_type, num_ops, workers);
        }
        else if (queue_type == "fc") {
            FlatCombiningQueue<Node<Payload>> idle_queue(workers + 1);
            FlatCombiningQueue<Node<Payload>> active_queue(workers + 1);
            run(idle_queue, true, queue_type, num_ops, workers);
            run(active_queue, false, queue_type, num_ops, workers);
        }
    }

    return 0;
}