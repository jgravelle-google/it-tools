let fs = require('fs');

module.exports = {
    instantiate: async function(imported) {
/**MODULE_NAMES**/

        // Loads specified modules
        async function loadModule(path, imports) {
            let contents = fs.readFileSync(path);
            let wasm = await WebAssembly.instantiate(contents, imports);
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

/**LOAD_MODULES**/

        let wrappedExports = {
/**EXPORTS**/
        };

        return wrappedExports;
    },
};
