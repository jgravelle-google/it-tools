async function run() {
    // Load modules
    let fizz = await fizzComponent.instantiate({});
    let buzz = await buzzComponent.instantiate({});
    function log(x) {
        console.log('AAGH:',x);
    }
    let fizzbuzz = await fizzbuzzComponent.instantiate({
        fizz, buzz,
        console: {
            log,
            logInt: log,
        },
    });

    // Run it
    fizzbuzz.fizzbuzz(20);
}

run();
