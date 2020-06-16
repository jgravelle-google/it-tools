serve: build
	emrun --no_browser --port 8080 .
.PHONY: serve

build: out out/fizz.wasm out/buzz.wasm out/fizzbuzz.wasm \
out/fizzbuzz.itl out/fizzbuzz.cpp \
out/fizz.js out/buzz.js out/fizzbuzz.js

out:
	mkdir -p out

out/%.cpp out/%.itl: %.cpp
	# TODO: explicit outputs here
	python ../../src/cpp_itl_generator.py $<

out/%.js: out/%.itl
	python ../../src/adapter.py $<

out/%.wasm: out/%.cpp out/%.js
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11 --no-entry
