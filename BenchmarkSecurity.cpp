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


int main(int argc, char* argv[]) {
    int num_ops = 1000;
    bool workers_idle = (argc > 1 && std::string(argv[1]) == "--idle");

    LPRQ<Payload> queue(nullptr);
    
    // make sure all threads start at same time
    std::barrier sync(5);

    auto attacker = [&](int tid) {
        std::vector<uint64_t> latencies;

        sync.arrive_and_wait();

        for (int i = 0; i < num_ops; i++) {
            Payload* item = new Payload{tid};

            uint64_t start = rdtscp();
            queue.enqueue(item);
            uint64_t end = rdtscp();

            latencies.push_back(end - start);
        }
        
        std::string filename = workers_idle ? "latencies_idle.csv" : "latencies_active.csv";
        std::ofstream file(filename);
        file << "sample,latency\n";
        for (int i = 0; i < latencies.size(); i++) {
            file << i << ","<< latencies[i] << "\n";
        }
    };

    auto worker = [&](int tid) {
        sync.arrive_and_wait();
        
        if (workers_idle) return;

        for (int i = 0; i < num_ops; i++) {
            Payload* item = new Payload{tid};
            queue.enqueue(item);
            Payload* result = queue.dequeue();
        }
    };

    std::vector<std::thread> threads;
    for (int i = 0; i < 4; i++) {
        threads.emplace_back(worker, i);
    }
    threads.emplace_back(attacker, 4);

    for (auto& t : threads) {
        t.join();
    }

    return 0;
}