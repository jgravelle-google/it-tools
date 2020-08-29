const /**COMPONENT_NAME**/ = {
    async instantiate(imports) {
/**MODULE_NAMES**/

        // Loads specified modules
        async function loadModule(path, wrappedImports) {
            let contents = await fetch(path);
            let bytes = await contents.arrayBuffer();
            let wasm = await WebAssembly.instantiate(bytes, wrappedImports);
            return wasm.instance.exports;
        }

        // Nontrivial adapter instructions
        function memToString(memory, ptr, len) {
            let u8 = new Uint8Array(memory.buffer);
            let str = '';
            for (let i = 0; i < len; ++i) {
                str += String.fromCharCode(u8[ptr + i]);
            }
            return str;
        }
        function stringToMem(memory, str, ptr) {
            let u8 = new Uint8Array(memory.buffer);
            let len = str.length;
            for (let i = 0; i < len; ++i) {
                u8[ptr + i] = str.charCodeAt(i);
            }
            return len;
        }
        function memToBuffer(memory, ptr, len) {
            return memory.buffer.slice(ptr, ptr + len);
        }
        function bufferToMem(memory, buffer, ptr) {
            let u8 = new Uint8Array(memory.buffer);
            let b8 = new Uint8Array(buffer);
            u8.set(b8, ptr);
        }
        let arrayTypes = {
            'u1': Uint8Array,
            'u8': Uint8Array,
            'i8': Int8Array,
            'i16': Int16Array,
            'u16': Uint16Array,
            'i32': Int32Array,
            'u32': Uint32Array,
            'f32': Float32Array,
        };
        function liftArray(ty, stride, ptr, len, body) {
            let constructor = arrayTypes[ty] || Array;
            let ret = new constructor(len);
            for (let i = 0; i < len; ++i) {
                ret[i] = body(ptr + i*stride);
            }
            return ret;
        }

        // References
        // first elem is null so we avoid assigning 0 as a valid index
        let refArray = [null];
        let refToIdx = new WeakMap();
        function liftRef(idx) {
            // TODO: create new ref entries for native wasm refs
            return refArray[idx];
        }
        function lowerRef(ref) {
            if (!ref) {
                // null refs can be valid; return as 0
                return 0;
            }
            if (!refToIdx.has(ref)) {
                refToIdx.set(ref, refArray.length);
                refArray.push(ref);
            }
            return refToIdx.get(ref);
        }

/**COMPONENT_FUNCTIONS**/

/**LOAD_MODULES**/
        let wrappedExports = {
/**EXPORTS**/
        };

        return wrappedExports;
    }
};
