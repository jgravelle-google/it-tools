let fs = require('fs');

module.exports = {
    instantiate: async function(imported) {
        let exported;
        function memToString(memoryName, ptr, len) {
            let u8 = new Uint8Array(exported[memoryName].buffer);
            let str = '';
            for (var i = 0; i < len; ++i) {
                str += String.fromCharCode(u8[ptr + i]);
            }
            return str;
        }

        let wrappedImports = {
/**IMPORTS**/
        };

        let contents = fs.readFileSync('/**WASM_PATH**/');
        let wasm = await WebAssembly.instantiate(contents, wrappedImports);
        exported = wasm.instance.exports;

        let wrappedExports = {
/**EXPORTS**/
        };

        return wrappedExports;
    },
};
