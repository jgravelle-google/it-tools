#ifndef __IT_HEADER_PREFIX__
// guard against multiple declarations of this header
#define __IT_HEADER_PREFIX__

#include <malloc.h>

#include <string>
#include <vector>

// Buffer data type for passing ArrayBuffers in and out.
// Does not manage the underlying buffer; defers that to a higher level.
class ITBuffer {
protected:
    // size of the buffer in bytes; volatile to silence unused warning
    volatile int nBytes;
    void* data;
    ITBuffer() : nBytes(0), data(nullptr) {}
public:
    ITBuffer(int n, void* d) : nBytes(n), data(d) {}

    void* rawBuffer() const {
        return data;
    }
};

// Variable sized buffer.
// Manages its own memory. Either allocates itself, or takes a reference to an
// ITBuffer - probably passed in from an import.
template <typename T>
class Buffer : public ITBuffer {
    int nElems; // number of elements
    bool owned; // whether Buffer is responsible for freeing the memory
public:
    Buffer(int n) : ITBuffer(n * sizeof(T), new T[n]), nElems(n), owned(true) {}
    Buffer() : ITBuffer(0, nullptr), nElems(0), owned(false) {}
    Buffer(int n, void* _data) : ITBuffer(n * sizeof(T), _data), nElems(n), owned(false) {}
    Buffer(std::vector<T> const& vec) : Buffer(vec.size()) {
        memcpy(data, vec.data(), nBytes);
    }

    Buffer(Buffer const& other) : owned(false) {
        *this = other;
    }
    Buffer(Buffer&& other) = default;

    ~Buffer() {
        if (owned) {
            delete[] (T*)data;
        }
    }

    Buffer& operator=(Buffer const& other) {
        if (owned) {
            delete[] (T*)data;
        }
        nBytes = other.nBytes;
        nElems = other.nElems;
        owned = other.owned;
        if (owned) {
            data = new T[nElems];
            memcpy(data, other.data, nElems*sizeof(T));
        } else {
            data = other.data;
        }
        return *this;
    }

    inline T& operator[](int idx) {
        return ((T*)data)[idx];
    }
    inline T const& operator[](int idx) const {
        return ((T*)data)[idx];
    }

    int size() const {
        return nElems;
    }
};

// Fixed-size buffer
template <typename T, int N>
class FixedBuffer : public Buffer<T> {
    T items[N];
public:
    FixedBuffer() : Buffer<T>(N, items) {}
    FixedBuffer(T const _items[N]) : Buffer<T>(N, items) {
        memcpy(items, _items, N*sizeof(T));
    }

    FixedBuffer(FixedBuffer& other) : FixedBuffer(other.items) {}
    FixedBuffer(FixedBuffer&& other) = default;
    FixedBuffer& operator=(FixedBuffer other) {
        memcpy(items, other.items, N*sizeof(T));
        return *this;
    }
};

/**IT_DECLS**/

// Helper functions used in adapters
__attribute__((export_name("_it_strlen")))
int _it_strlen(const char* str) {
    int len = 0;
    while (*str++) len++;
    return len;
}

__attribute__((export_name("_it_writeStringTerm")))
void _it_writeStringTerm(char* str, int len) {
    // Writes null-terminator for imported strings
    str[len] = 0;
}

__attribute__((export_name("_it_malloc")))
void* _it_malloc(unsigned int size) {
    return malloc(size);
}

#endif // __IT_HEADER_PREFIX__
