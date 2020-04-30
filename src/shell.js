async function run() {
    let fizz = await require('../out/fizz.js').instantiate({});
    let buzz = await require('../out/buzz.js').instantiate({});
    let fizzbuzz = await require('../out/buzz.js').instantiate({
        fizz, buzz,
        printer: { print: console.log },
    });
    fizzbuzz.fuzzbuzz(20);
    // for (let i = 1; i <= 20; ++i) {
    //     if (buzz.isBuzz(i)) {
    //         print(buzz.buzzStr());
    //     } else {
    //         print(i);
    //     }
    // }
}

run();
