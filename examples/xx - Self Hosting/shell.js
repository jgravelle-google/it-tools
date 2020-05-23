async function run() {
    try {
        // Load modules
        let fizz = await require('./fizz.js').instantiate({});
        let buzz = await require('./buzz.js').instantiate({});
        let fizzbuzz = await require('./fizzbuzz.js').instantiate({
            fizz, buzz,
            console: {
                log: console.log,
                logInt: console.log,
            },
        });

        // Run it
        fizzbuzz.fizzbuzz(20);
    } catch (e) {
        // Echo errors on stdout so make prints them
        console.log('[[shell.js ERROR]]')
        console.log(e);
    }
}

run();
