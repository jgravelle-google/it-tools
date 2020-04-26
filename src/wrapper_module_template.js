let fs = require('fs');

module.exports = {
    instantiate: async function(imports) {
        let contents = fs.readFileSync('/**WASM_PATH**/');
        let wasm = await WebAssembly.instantiate(contents, imports);
        return wasm.instance.exports;
    },
};
