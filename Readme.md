# Interface Types Tools

This repository serves as a collection of tools useful for prototyping code
related to the WebAssembly Interface Types proposal.

None of these tools are Production-ready, or have any stability guarantees
whatsoever. The intention for these tools is to serve as a proof of concept,
rather than a complete solution.

## Things to read

* [List of Tools](src/Readme.md) - Summary of each tool in this repo
* [Example 05](examples/05%20-%20Self%20Hosting%20%28generated%29/Readme.md) -
  Walks through the code and output of each step of a specific sample
* [Article: Replacing Embind](design/article_replace_embind.md) - A motivating
  use-case. How we might use these tools (and Interface Types in general) to
  improve a specific element of the Emscripten toolchain. Something to aim for.
* [Article: LLVM](design/llvm_integration.md) - Some thoughts on how we might
  generate IT bindings from LLVM directly, at some point in the future.

## Other interesting repos

* [em-import](https://github.com/jgravelle-google/emscripten/tree/em_import/tools/em-import) -
  Branch in Emscripten, test of implementing EM_IMPORT, a means of using a custom
  clang tool to facilitate IT generation that integrates with `emcc`
* [interface-embind](https://github.com/jgravelle-google/interface-embind) -
  Examples of the EM_IMPORT mechanism using canvas, with direct comparison to embind
    * js_canvas.js : JS version, 20 ms frame time
    * canvas.cpp : embind version, 200 ms frame time (10x slowdown)
    * import_canvas.cpp: EM_IMPORT version, 22 ms frame time (10% slowdown)
* [web-sys](https://github.com/jgravelle-google/web-sys) - An EM_IMPORT equivalent
  to wasm-bindgen's web-sys crate. Tool to generate a bunch of C++ headers with
  annotations that would generate IT bindings.
* [Dynamic IT Polyfill](https://github.com/jgravelle-google/wasm-webidl-polyfill) -
  An early prototype, mostly a historical footnote. Included for posterity.
