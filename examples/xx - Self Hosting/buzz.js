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
        function memToString(memory, ptr, len) {
            let u8 = new Uint8Array(memory.buffer);
            let str = '';
            for (var i = 0; i < len; ++i) {
                str += String.fromCharCode(u8[ptr + i]);
            }
            return str;
        }
        function stringToMem(memory, str, ptr) {
            let u8 = new Uint8Array(memory.buffer);
            let len = str.length;
            for (var i = 0; i < len; ++i) {
                u8[ptr + i] = str.charCodeAt(i);
            }
            return len;
        }

        function _it_cppToString(x0) {
            return memToString(wasm["memory"], x0, wasm["_it_strlen"](x0));
        };
        function _it_stringToCpp(x0) {
            let x1 = wasm["malloc"]((x0.length + 1));
            stringToMem(wasm["memory"], x0, x1);
            wasm["_it_writeStringTerm"](x1, x0.length);
            return x1;
        };

        wasm = await loadModule("out/buzz.wasm", {
        });

        let wrappedExports = {
            "isBuzz": function(x0) {
                return wasm["isBuzz"](x0);
            },
            "buzzStr": function() {
                return _it_cppToString(wasm["buzzStr"]());
            },
        };

        return wrappedExports;
    },
};
