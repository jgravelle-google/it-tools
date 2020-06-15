# Example #6 - IT in Browser

Previous examples were ran in Node. This example runs in the browser.

Requires browser support for the [reference types proposal]
(https://github.com/WebAssembly/reference-types/blob/master/proposals/reference-types/Overview.md).

# Changes from #5

* index.html loads shell.js in a worker, which loads it_loader.js
* it_loader.js changed to use fetch and sync-XHR instead of Node's `fs` module
