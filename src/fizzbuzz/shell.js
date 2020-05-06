async function run() {
    // Load modules
    let fizz = await require('./out/fizz.js').instantiate({});
    let buzz = await require('./out/buzz.js').instantiate({});
    let fizzbuzz = await require('./out/fizzbuzz.js').instantiate({
        fizz, buzz,
        console,
    });

    // Run it
    try {
        fizzbuzz.fizzbuzz(20);
    } catch (e) {
        // Echo errors on stdout so make prints them
        console.log('[[shell.js ERROR]]')
        console.log(e);
    }
}

run();
