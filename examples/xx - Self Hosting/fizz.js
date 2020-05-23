let fs = require('fs');

module.exports = {
    instantiate: async function(imports) {
        let wasm;

        // Loads specified modules
        async function loadModule(path, wrappedImports) {
            let contents = fs.readFileSync(path);
            let wasm = await WebAssembly.instantiate(contents, wrappedImports);
            return wasm.instance.exports;
        }

        // Nontrivial adapter instructions
        let memory;
        let _it_runtime = {
            "string-len": (x) => x.length,
            "mem-to-string": (ptr, len) => {
                let u8 = new Uint8Array(memory.buffer);
                let str = '';
                for (var i = 0; i < len; ++i) {
                    str += String.fromCharCode(u8[ptr + i]);
                }
                return str;
            },
            "string-to-mem": (str, ptr) => {
                let u8 = new Uint8Array(memory.buffer);
                let len = str.length;
                for (var i = 0; i < len; ++i) {
                    u8[ptr + i] = str.charCodeAt(i);
                }
                return len;
            },
        };
        let pre_wasm = await loadModule('out/pre_fizz.wasm', {
            _it_runtime,
        });

        wasm = await loadModule("out/fizz.wasm", {
        });

        memory = wasm.memory;
        pre_wasm.table.set(0, wasm.malloc);
        pre_wasm.table.set(1, wasm._it_writeStringTerm);
        pre_wasm.table.set(2, wasm._it_strlen);
        pre_wasm.table.set(3, wasm.isFizz);
        pre_wasm.table.set(4, wasm.fizzStr);

        return pre_wasm;
    },
};
