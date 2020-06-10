let fs = require('fs');

module.exports = {
    instantiate: async function(filename, imports) {
        let self;

        // Loads specified modules
        async function loadModule(path, wrappedImports) {
            let contents = fs.readFileSync(path);
            let wasm = await WebAssembly.instantiate(contents, wrappedImports);
            return wasm.instance.exports;
        }
       function loadModuleSync(path, wrappedImports) {
            let contents = fs.readFileSync(path);
            let mod = new WebAssembly.Module(contents);
            let wasm = new WebAssembly.Instance(mod, wrappedImports);
            return wasm.exports;
        }

        // Nontrivial adapter instructions
        let string_table = new WeakMap();
        function memReadString(memory, ptr, len) {
            let u8 = new Uint8Array(memory.buffer);
            let str = '';
            for (var i = 0; i < len; ++i) {
                str += String.fromCharCode(u8[ptr + i]);
            }
            return str;
        }
        function readITString(ptr) {
            // Read IT-module string
            // ABI is first byte = length, followed by chars

            // If string has been read before, just reuse it
            if (!string_table.has(self)) {
                string_table.set(self, {});
            }
            let str = string_table.get(self)[ptr];
            if (str !== undefined) {
                return str;
            }

            // Read string out of memory, and cache it
            let memory = self["_it_memory"];
            let u8 = new Uint8Array(memory.buffer);
            let len = u8[ptr];
            str = memReadString(memory, ptr + 1, len)
            string_table.get(self)[ptr] = str;
            return str;
        }
        function readITValue(ptr) {
            let str = readITString(ptr);
            return self[str];
        }

        let _it_runtime = {
            string_len: (str) => str.length,
            mem_to_string: (mod, mem, ptr, len) => {
                let memory = mod[readITString(mem)];
                return memReadString(memory, ptr, len);
            },
            string_to_mem: (mod, mem, str, ptr) => {
                let memory = mod[readITString(mem)];
                let u8 = new Uint8Array(memory.buffer);
                let len = str.length;
                for (var i = 0; i < len; ++i) {
                    u8[ptr + i] = str.charCodeAt(i);
                }
                return len;
            },
            load_wasm(ptr) {
                let filename = readITString(ptr);
                let wasm_imports = {};
                for (let key in imports) {
                    wasm_imports[key] = self;
                }
                // XXX: awkwardness because we can't async here
                return loadModuleSync(filename, wasm_imports);
            },
            set_table_func(idx, mod, namePtr) {
                // sets IT table index to a property on a module
                let table = self._it_table;
                let name = readITString(namePtr);
                let val = mod[name];
                table.set(idx, val);
            },
        };

        let modified_imports = { _it_runtime };
        for (let key in imports) {
            modified_imports[key] = imports[key];
        }
        self = await loadModule(filename, modified_imports);
        self._it_init();
        return self;
    },
};
