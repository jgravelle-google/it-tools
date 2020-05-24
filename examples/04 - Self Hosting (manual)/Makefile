run: build
	node --experimental-wasm-anyref shell.js
.PHONY: run

build: out out/fizzbuzz.wasm out/fizz.wasm out/buzz.wasm \
out/pre_fizzbuzz.wasm out/pre_fizz.wasm out/pre_buzz.wasm

out:
	mkdir -p out

out/%.cpp: %.cpp
	# TODO: explicit outputs here
	python ../../src/cpp_itl_generator.py $<

out/%.wasm: out/%.cpp
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11
	wasm-decompile $@ -o out/$*.wade

out/%.wasm: %.wat
	wat2wasm $< -o $@ --debug-names
