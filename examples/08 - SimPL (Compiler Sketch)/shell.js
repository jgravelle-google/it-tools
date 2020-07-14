async function run() {
    importScripts('it_loader.js');
    // Load modules
    let parser = await ITLoader.instantiate('out/parser.wasm', {
        console: {
            log: console.log,
            logInt: console.log,
        },
    });

    // Run it
    parser.parse("print 101;");
}

run();
