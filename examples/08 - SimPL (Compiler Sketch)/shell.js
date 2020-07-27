async function run() {
    // Load modules
    let parser = await parserComponent.instantiate('out/parser.wasm', {
        console: {
            log: console.log,
            logInt: console.log,
        },
    });

    // Run it
    parser.parse("print 101;");
}

run();
