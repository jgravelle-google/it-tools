run: build
	node shell.js
.PHONY: run

build: out out/fizzbuzz.js

out:
	mkdir -p out

out/%.cpp: %.cpp
	# TODO: explicit outputs here
	python ../../src/cpp_itl_generator.py $<

out/%.wasm: out/%.cpp
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11

out/fizzbuzz.js: fizzbuzz.itl out/fizz.wasm out/buzz.wasm out/fizzbuzz.wasm
	python ../../src/adapter.py fizzbuzz.itl
