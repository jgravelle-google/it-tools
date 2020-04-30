async function run() {
    // Load modules
    let fizz = await require('../out/fizz.js').instantiate({});
    let buzz = await require('../out/buzz.js').instantiate({});
    let fizzbuzz = await require('../out/fizzbuzz.js').instantiate({
        fizz, buzz,
        console,
    });

    // Run it
    fizzbuzz.fizzbuzz(20);
}

run();
