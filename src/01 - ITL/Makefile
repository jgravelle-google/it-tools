run: build
	node shell.js
.PHONY: run

build: out out/fizz.wasm out/buzz.wasm out/fizzbuzz.wasm \
out/fizz.js out/buzz.js out/fizzbuzz.js

out:
	mkdir -p out

out/%.js: %.itl
	python ../adapter.py $<

out/%.wasm: %.cpp
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -std=c++11
