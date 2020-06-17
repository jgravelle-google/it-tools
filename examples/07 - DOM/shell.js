let list = document.createElement('ul');
document.body.append(list);

function log(x) {
    let item = document.createElement('li');
    item.innerText = x;
    list.append(item);
}

async function run() {
    // Load modules
    let fizz = await fizzComponent.instantiate({});
    let buzz = await buzzComponent.instantiate({});
    let fizzbuzz = await fizzbuzzComponent.instantiate({
        fizz, buzz,
        console: {
            log,
            logInt: log,
        },
    });

    let input = document.getElementById('iterations');
    function update() {
        // clear existing list
        while (list.children.length > 0) {
            list.children[0].remove();
        }

        let iters = input.value | 0;
        fizzbuzz.fizzbuzz(iters);
    }

    update();
    input.onchange = update;
}

run();
