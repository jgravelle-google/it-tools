run: build
	node --experimental-wasm-anyref shell.js
.PHONY: run

build: out out/fizzbuzz.wasm out/fizz.wasm out/buzz.wasm \
out/it_fizzbuzz.wasm out/it_fizz.wasm out/it_buzz.wasm

out:
	mkdir -p out

out/%.cpp: %.cpp
	# TODO: explicit outputs here
	python ../../src/cpp_itl_generator.py $<

out/%.wasm: out/%.cpp
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11 --no-entry
	wasm-decompile $@ -o out/$*.wade

out/%.wasm: %.wat
	wat2wasm --enable-reference-types $< -o $@ --debug-names
