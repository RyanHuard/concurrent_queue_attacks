#ifndef LPRQ_HPP
#define LPRQ_HPP

#pragma once

#include <cstdint>
#include <string>
#include <atomic>
#include <pthread.h>

template <typename sPayload>
struct LPRQNode{
    static const uint64_t RING_SIZE = 1024;

    struct alignas(16) Cell
    {
        std::atomic<sPayload*> payload;
        std::atomic<uint64_t> epoch;
    };

    std::atomic<long long int> head;
    std::atomic<long long int> tail;
    bool closed;
    
    Cell ring[RING_SIZE];

    std::atomic<LPRQNode*> next;

    LPRQNode() : head(RING_SIZE), tail(RING_SIZE), closed(false), next(nullptr) {
        for (size_t i = 0; i < RING_SIZE; ++i) {
            ring[i].payload.store(nullptr, std::memory_order_relaxed);
            ring[i].epoch.store(0, std::memory_order_relaxed);
        }
    }
};

template<typename NodeType>
class LPRQ {
    using PRQ = LPRQNode<NodeType>;
    alignas(64) std::atomic<PRQ*> head_PRQ;
    alignas(64) std::atomic<PRQ*> tail_PRQ;

    //------Thread token management-------------
    //Use lowest bit of NodeType as thread token

    inline NodeType* get_thread_token()
    {
        uintptr_t tid = (uintptr_t)pthread_self();
        return reinterpret_cast<NodeType*> ((tid << 1) | 1);
    }

    inline bool is_token(NodeType* ptr)
    {
        return (reinterpret_cast<uintptr_t>(ptr) & 1) != 0;
    }
    // Extracts the node index from an cell
    inline uint64_t node_index(uint64_t e) { return (e & ~(1ull << 63)); }
    // Checks if a specific cell has been marked as unsafe
    inline uint64_t node_unsafe(uint64_t e) { return (e & (1ull << 63)); }

    inline bool prq_is_closed(uint64_t t) { return (t & (1ull << 63)) != 0; }

public:
    explicit LPRQ(NodeType* dummy)
    {
        PRQ* sentinel = new PRQ();
        head_PRQ.store(sentinel, std::memory_order_relaxed);
        tail_PRQ.store(sentinel, std::memory_order_relaxed);
    }

    ~LPRQ() {
        // Cleanup all PRQs in the chain
        PRQ* current = head_PRQ.load(std::memory_order_relaxed);
        while (current) {
            PRQ* next = current->next.load(std::memory_order_relaxed);
            delete current;
            current = next;
        }
    }

    NodeType* enqueue(NodeType* new_payload, int tid)
    {
        while(true)
        {
            PRQ* local_tail_PRQ = tail_PRQ.load(std::memory_order_acquire);
            PRQ* local_tail_PRQ_next = local_tail_PRQ->next.load(std::memory_order_acquire);

            if(local_tail_PRQ_next != nullptr){
                // Tail is lagging, try to advance it
                tail_PRQ.compare_exchange_strong(local_tail_PRQ, local_tail_PRQ_next, std::memory_order_release, std::memory_order_relaxed);
                continue;
            }

            uint64_t tailTicket = local_tail_PRQ->tail.fetch_add(1);

            if(prq_is_closed(tailTicket)){
                PRQ* new_prq = new PRQ();
                new_prq->ring[0].payload.store(new_payload, std::memory_order_relaxed);
                new_prq->ring[0].epoch.store(1, std::memory_order_release);
                new_prq->tail.store(PRQ::RING_SIZE + 1, std::memory_order_relaxed);

                PRQ* expected = nullptr;
                if(local_tail_PRQ->next.compare_exchange_strong(expected, new_prq, std::memory_order_release, std::memory_order_relaxed)){
                    tail_PRQ.compare_exchange_strong(local_tail_PRQ, new_prq, std::memory_order_release, std::memory_order_relaxed);
                    return new_payload;
                }

                delete new_prq; // Another thread added the new PRQ, discard ours
                continue;
            }

            uint64_t cycle = tailTicket / PRQ::RING_SIZE;
            uint64_t i = tailTicket % PRQ::RING_SIZE;

            auto& cell = local_tail_PRQ->ring[i];
            uint64_t cell_epoch = cell.epoch.load(std::memory_order_acquire);
            NodeType* payload = cell.payload.load(std::memory_order_acquire);
            
            uint64_t epoch = node_index(cell_epoch); // Extract the epoch from the cell
            bool safe = !node_unsafe(cell_epoch); // Check if the cell is marked as unsafe

            if(payload == nullptr && epoch < cycle && (safe || local_tail_PRQ->head.load() <= (int64_t)tailTicket))
            {
                //Lock the cell with thread token
                NodeType* expected_payload = payload;
                if(!cell.payload.compare_exchange_strong(expected_payload, get_thread_token(), std::memory_order_release, std::memory_order_relaxed)){
                    goto checkOverflow;
                }

                //Advance the epoch
                uint64_t expected_epoch = cell_epoch;
                uint64_t new_epoch = cycle;
                if(!cell.epoch.compare_exchange_strong(expected_epoch, new_epoch, std::memory_order_release, std::memory_order_relaxed)){
                    // Clean up and restart
                    NodeType* expected_token = get_thread_token();
                    cell.payload.compare_exchange_strong(expected_token, nullptr, std::memory_order_release, std::memory_order_relaxed);
                    goto checkOverflow;
                }

                //Publish item
                NodeType* expected_token = get_thread_token();
                if(cell.payload.compare_exchange_strong(expected_token, new_payload, std::memory_order_release, std::memory_order_relaxed)){
                    return new_payload;
                }
            }

            checkOverflow:
                //Close the PRQ if it appears to be full
                if((int64_t)(tailTicket - local_tail_PRQ->head.load()) >= (int64_t)PRQ::RING_SIZE){
                    long long int expected_tail = tailTicket + 1;
                    long long int closed_val = (tailTicket + 1) | (1ull << 63);
                    local_tail_PRQ->tail.compare_exchange_strong(expected_tail, closed_val);
                }
            __asm__ __volatile__("pause" ::: "memory");
        }
    }

    NodeType* dequeue(int tid)
    {
        while(true){
            PRQ* local_head_PRQ = head_PRQ.load(std::memory_order_acquire);
            uint64_t headTicket = local_head_PRQ->head.fetch_add(1);

            uint64_t cycle = headTicket / PRQ::RING_SIZE;
            uint64_t i = headTicket % PRQ::RING_SIZE;

            while(true)
            {
                auto &cell = local_head_PRQ->ring[i];
                uint64_t cell_epoch = cell.epoch.load(std::memory_order_acquire);
                NodeType* payload = cell.payload.load(std::memory_order_acquire);
                
                //inconsistent view of the cell
                if(cell_epoch != cell.epoch.load(std::memory_order_acquire))
                {
                    __asm__ __volatile__("pause" ::: "memory");
                    continue;
                }
                uint64_t epoch = node_index(cell_epoch); // Extract the epoch from the cell
                uint64_t unsafe_bit = node_unsafe(cell_epoch); // Check if the cell is marked as unsafe

                //DeQ is overtaken
                if(epoch > cycle)
                {
                    break;
                }

                //Preserve the unsafe bit while advancing epoch
                uint64_t next_epoch = cycle | unsafe_bit;

                //dequeue transition
                if(epoch == cycle && payload != nullptr && !is_token(payload))
                {
                    cell.payload.store(nullptr, std::memory_order_release);
                    return payload;
                }

                //empty transition
                else if(epoch <= cycle && (payload == nullptr || is_token(payload)))
                {
                    if(is_token(payload))
                    {
                        NodeType* expected_payload = payload;
                        if(!cell.payload.compare_exchange_strong(expected_payload, nullptr, std::memory_order_release, std::memory_order_relaxed))
                        {
                            __asm__ __volatile__("pause" ::: "memory");
                            continue;
                        }
                    }

                    //Advance the epoch to prevent overtaking
                    uint64_t expected_epoch = cell_epoch;
                    if(cell.epoch.compare_exchange_strong(expected_epoch, next_epoch, std::memory_order_release, std::memory_order_relaxed))
                        break;
                    else {
                        __asm__ __volatile__("pause" ::: "memory");
                        continue;
                    }
                }

                //unsafe transition
                else if(epoch < cycle && payload != nullptr && !is_token(payload))
                {
                    uint64_t marked_unsafe = cell_epoch | (1ull << 63);
                    if(cell.epoch.compare_exchange_strong(cell_epoch, marked_unsafe, std::memory_order_release, std::memory_order_relaxed)){
                        break;
                    }
                }
                __asm__ __volatile__("pause" ::: "memory");
            }   

            //Is queue empty?
            uint64_t current_tail = local_head_PRQ->tail.load(std::memory_order_acquire);
            uint64_t unclosed_tail = current_tail & ~(1ull << 63);
            if(unclosed_tail <= headTicket + 1){
                // Check if there is a next ring buffer linked
                PRQ* next_prq = local_head_PRQ->next.load(std::memory_order_acquire);
                if (next_prq == nullptr) {
                    return nullptr; // Truly empty
                }
                
                // Ring is exhausted but a new one exists. Advance head_PRQ and retry.
                head_PRQ.compare_exchange_strong(local_head_PRQ, next_prq, std::memory_order_release, std::memory_order_relaxed);
            }
            __asm__ __volatile__("pause" ::: "memory");
        }
    }
};
#endif // LPRQ_HPP