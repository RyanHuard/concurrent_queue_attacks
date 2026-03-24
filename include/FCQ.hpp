#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>
#include <tuple>




enum class Opcode : uint8_t { Done = 0, Enqueue = 1, Dequeue = 2 };

template <typename sPayload>
struct FCNode {
    sPayload* payload;
};

template <typename sPayload>
struct alignas(64) Operation {
    std::atomic<Opcode> opcode{Opcode::Done};
    FCNode<sPayload>    node{};  
    bool                success = false; 
};

template <typename T>
class FlatCombiningQueue {
public:

    explicit FlatCombiningQueue(size_t num_threads)
        : operations_(num_threads) {}

    T* enqueue(T* item, int tid) {

        auto& slot = operations_[tid];
        slot.node.payload   = item;
        slot.opcode.store(Opcode::Enqueue, std::memory_order_release);

        while (true) {
            if (lock_.try_lock()) { 
                scan_combine_apply(); 
                lock_.unlock(); 
                return item; 
            }
            if (slot.opcode.load(std::memory_order_acquire) == Opcode::Done) 
                return item;
        }
    }

    T* dequeue(int tid) {

        auto& slot = operations_[tid];
        slot.node.payload = nullptr;
        slot.success = false;
        slot.opcode.store(Opcode::Dequeue, std::memory_order_release);

        while (true) {
            if (lock_.try_lock()) { 
                scan_combine_apply(); 
                lock_.unlock(); 
                break; 
            }
            if (slot.opcode.load(std::memory_order_acquire) == Opcode::Done) 
                break;
        }
        
        return slot.node.payload;
    }


private:
    void scan_combine_apply() {
        for (size_t i = 0; i < operations_.size(); ++i) {
            auto& slot = operations_[i];
            Opcode code = slot.opcode.load(std::memory_order_acquire);

            if (code == Opcode::Enqueue) {
                FCNode<T> n = slot.node;

                q_.push(n);
                slot.opcode.store(Opcode::Done, std::memory_order_release);
            }
            else if (code == Opcode::Dequeue) {
                if (!q_.empty()) {
                    FCNode<T> n = q_.front(); 
                    q_.pop();

      
                    slot.success = true;
                } else {
                    slot.success = false;
                }
                slot.opcode.store(Opcode::Done, std::memory_order_release);
            }
        }
    }

    std::vector<Operation<T>> operations_;
    std::queue<FCNode<T>>     q_;
    std::mutex                lock_;
};