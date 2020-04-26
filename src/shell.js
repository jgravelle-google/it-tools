let print = console.log;

// Assumption: running in NodeJS
let fs = require('fs');

async function loadWasm(path, imports) {
    let contents = fs.readFileSync(path);
    let wasm = await WebAssembly.instantiate(contents, imports);
    return wasm.instance.exports;
}

async function run() {
    let fizz = await loadWasm('out/fizz.wasm', {});
    for (let i = 1; i <= 10; ++i) {
        if (fizz.isFizz(i)) {
            print(fizz.fizzStr());
        } else {
            print(i);
        }
    }
}

run();
