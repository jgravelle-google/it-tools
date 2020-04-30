async function run() {
    let fizz = await require('../out/fizz.js').instantiate({});
    // let buzz = await require('../out/buzz.js').instantiate({});
    // let fizzbuzz = await require('../out/buzz.js').instantiate({
    //     fizz, buzz,
    //     printer: { print: console.log },
    // });

    let print = console.log;
    for (let i = 1; i <= 20; ++i) {
        if (fizz.isFizz(i)) {
            print(fizz.fizzStr());
        } else {
            print(i);
        }
    }

    // for (let i = 1; i <= 20; ++i) {
    //     if (buzz.isBuzz(i)) {
    //         print(buzz.buzzStr());
    //     } else {
    //         print(i);
    //     }
    // }

    // fizzbuzz.fuzzbuzz(20);
}

run();
