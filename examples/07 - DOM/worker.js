onmessage = (message) => {
    console.log('worker recvd msg:', message);
};

async function run() {
    importScripts('it_loader.js');
    try {
        // Load modules
        let fizz = await ITLoader.instantiate('out/it_fizz.wasm', {});
        let buzz = await ITLoader.instantiate('out/it_buzz.wasm', {});
        function log(x) {
            // On the main thread:
            // let li = document.createElement('li');
            // li.innerText = x + '';
            // ul.append(li);
            postMessage(['add', x]);
        }
        let fizzbuzz = await ITLoader.instantiate('out/it_fizzbuzz.wasm', {
            fizz, buzz,
            console: {
                log,
                logInt: log,
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
