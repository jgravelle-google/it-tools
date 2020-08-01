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

template <typename T, int N>
class Buffer {
    T* data;
public:
    Buffer() : data(new T[N * sizeof(T)]) {}
    ~Buffer() {
        delete[] data;
    }

    T& operator[](int idx) {
        return data[idx];
    }

    operator ITBuffer() const {
        return ITBuffer(N * sizeof(T), data);
    }
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
