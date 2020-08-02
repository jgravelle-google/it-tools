#ifndef __IT_HEADER_PREFIX__
// guard against multiple declarations of this header
#define __IT_HEADER_PREFIX__

// Buffer data type for passing ArrayBuffers in and out
class ITBuffer {
    int size;
    void* data;
public:
    ITBuffer(int n, void* d) : size(n), data(d) {}
};

// Variable sized buffer
template <typename T>
class Buffer {
    int size;
    T* data;
public:
    Buffer(int n) : size(n), data(new T[n * sizeof(T)]) {}
    ~Buffer() {
        delete[] data;
    }

    inline T& operator[](int idx) {
        return data[idx];
    }

    inline operator ITBuffer() const {
        return ITBuffer(size * sizeof(T), data);
    }
};

// Fixed-size buffer
template <typename T, int N>
class FixedBuffer : public Buffer<T> {
public:
    FixedBuffer() : Buffer<T>(N) {}
};

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

#endif // __IT_HEADER_PREFIX__
