let worker = new Worker('worker.js');

let ul = document.createElement('ul');
document.body.append(ul);

// All told, this is a very silly way to do this
worker.onmessage = (message) => {
    let text = message.data[1];
    let li = document.createElement('li');
    li.innerText = text;
    ul.append(li);
};
