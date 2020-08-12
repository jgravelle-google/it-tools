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

/**COMPONENT_FUNCTIONS**/

/**LOAD_MODULES**/
        let wrappedExports = {
/**EXPORTS**/
        };

        return wrappedExports;
    }
};
