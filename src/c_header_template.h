#ifndef __IT_HEADER_PREFIX__
// guard against multiple declarations of this header
#define __IT_HEADER_PREFIX__

// Buffer data type for passing ArrayBuffers in and out.
// Does not manage the underlying buffer; defers that to a higher level.
class ITBuffer {
    int size;
protected:
    void* data;
public:
    ITBuffer(int n, void* d) : size(n), data(d) {}

    void* rawBuffer() const {
        return data;
    }
};

// Variable sized buffer.
// Manages its own memory. Either allocates itself, or takes a reference to an
// ITBuffer - probably passed in from an import.
template <typename T>
class Buffer : public ITBuffer {
    int count;
public:
    Buffer(int n) : ITBuffer(n * sizeof(T), new T[n * sizeof(T)]), count(n) {}
    Buffer() : ITBuffer(0, nullptr), count(0) {}
    // ITBuffers are unmanaged, so the destructor shouldn't double-free if we
    // take ownership of one.
    Buffer(ITBuffer* buffer, int n) : ITBuffer(n * sizeof(T), buffer->rawBuffer()) {}

    ~Buffer() {
        if (data) {
            delete[] (T*)data;
        }
    }

    inline T& operator[](int idx) {
        return ((T*)data)[idx];
    }
};

// Fixed-size buffer
template <typename T, int N>
class FixedBuffer : public Buffer<T> {
public:
    FixedBuffer() : Buffer<T>(N) {}
};

// Types
/**TYPE_DECLS**/

// Imports
/**IMPORT_DECLS**/

// Exports
/**EXPORT_DECLS**/

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

#include <malloc.h>

__attribute__((export_name("_it_malloc")))
void* _it_malloc(unsigned int size) {
    return malloc(size);
}

#endif // __IT_HEADER_PREFIX__
