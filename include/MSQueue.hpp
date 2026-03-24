#ifndef MSQUEUE_HPP
#define MSQUEUE_HPP

#pragma once

#include <cstdint>
#include <cstddef>
#include <atomic>


// Forward declaration
template <typename sPayload>
struct Node;

// 16-byte aligned pointer with ABA prevention counter
template <typename sPayload>
struct alignas(16) Pointer_t {
    Node<sPayload>* ptr;
    uint64_t count;

    Pointer_t() noexcept : ptr(nullptr), count(0) {}
    Pointer_t(Node<sPayload>* p, uint64_t c) noexcept : ptr(p), count(c) {}

    bool operator==(const Pointer_t& other) const noexcept {
        return ptr == other.ptr && count == other.count;
    }
    bool operator!=(const Pointer_t& other) const noexcept {
        return !(*this == other);
    }
};

// Queue Node
template <typename sPayload>
struct Node {
    sPayload* Payload;
    std::atomic<Pointer_t<sPayload>> next;

    Node() noexcept : Payload(nullptr), next(Pointer_t<sPayload>()) {}
    explicit Node(sPayload* p) noexcept : Payload(p), next(Pointer_t<sPayload>()) {}
};

template <typename sPayload>
struct alignas(64) MSQueue {
    alignas(64) std::atomic<Pointer_t<sPayload>> head;
    alignas(64) std::atomic<Pointer_t<sPayload>> tail;

    // Construct an empty queue with a single dummy node.
    explicit MSQueue(Node<sPayload> *dummy) noexcept {
        Pointer_t<sPayload> d(dummy, 0);
        head.store(d, std::memory_order_relaxed);
        tail.store(d, std::memory_order_relaxed);
        dummy->next.store(Pointer_t<sPayload>(nullptr, 0), std::memory_order_relaxed);
        dummy->Payload = nullptr;
    }
    
    // No copy/move -- queue positions are shared state.
    MSQueue(const MSQueue &) = delete;
    MSQueue &operator=(const MSQueue &) = delete;

    sPayload* enqueue(Node<sPayload>* new_node, int tid) {
        new_node->next.store(Pointer_t<sPayload>(nullptr, 0), std::memory_order_relaxed);

        while(true) {
            Pointer_t<sPayload> tail_snapshot = tail.load(std::memory_order_acquire);
            Pointer_t<sPayload> tail_next = tail_snapshot.ptr->next.load(std::memory_order_acquire);

            // Are tail and next consistent?
            if(tail_snapshot == tail.load(std::memory_order_acquire)) {
                // Was tail pointing to the last node?
                if(tail_next.ptr == nullptr) {
                    // Try to link node at the end of the linked list
                    Pointer_t<sPayload> new_next(new_node, tail_next.count + 1);
                    if(tail_snapshot.ptr->next.compare_exchange_weak(tail_next, new_next, std::memory_order_release, std::memory_order_relaxed)) {
                        // Enqueue is done. Try to swing tail to the inserted node.
                        Pointer_t<sPayload> new_tail(new_node, tail_snapshot.count + 1);
                        tail.compare_exchange_weak(tail_snapshot, new_tail, std::memory_order_release, std::memory_order_relaxed);
                        return new_node->Payload;
                    }
                } else {
                    // Tail was not pointing to the last node. Try to swing tail to the next node.
                    Pointer_t<sPayload> new_tail(tail_next.ptr, tail_snapshot.count + 1);
                    tail.compare_exchange_weak(tail_snapshot, new_tail, std::memory_order_release, std::memory_order_relaxed);
                }
            }
            __asm__ __volatile__("pause" ::: "memory");
        }
    }

    Node<sPayload>* dequeue(int tid) {
        while(true) {
            Pointer_t<sPayload> head_snapshot = head.load(std::memory_order_acquire);
            Pointer_t<sPayload> tail_snapshot = tail.load(std::memory_order_acquire);
            Pointer_t<sPayload> head_next = head_snapshot.ptr->next.load(std::memory_order_acquire);

            // Are head, tail, and next consistent?
            if(head_snapshot == head.load(std::memory_order_acquire)) {
                // Is queue empty or tail falling behind?
                if(head_snapshot.ptr == tail_snapshot.ptr) {
                    // Is queue empty?
                    if(head_next.ptr == nullptr) {
                        return nullptr;
                    } else {
                        // Tail is falling behind. Try to advance it.
                        Pointer_t<sPayload> new_tail(head_next.ptr, tail_snapshot.count + 1);
                        tail.compare_exchange_weak(tail_snapshot, new_tail, std::memory_order_release, std::memory_order_relaxed);
                    }
                } else {
                    // Read the actual dequeued payload from the *next* node beforeCAS
                    sPayload* dequeued_payload = head_next.ptr->Payload;
                    Pointer_t<sPayload> new_head(head_next.ptr, head_snapshot.count + 1);
                    
                    if(head.compare_exchange_weak(head_snapshot, new_head, std::memory_order_release, std::memory_order_relaxed)) {
                        head_snapshot.ptr->Payload = dequeued_payload;
                        return head_snapshot.ptr;
                    }
                }
            }
            __asm__ __volatile__("pause" ::: "memory");
        }
    }
};

#endif // MSQUEUE_HPP