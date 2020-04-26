let print = console.log;

async function run() {
    let fizz = await require('../out/fizz.js').instantiate({});
    for (let i = 1; i <= 10; ++i) {
        if (fizz.isFizz(i)) {
            print(fizz.fizzStr());
        } else {
            print(i);
        }
    }
}

run();
