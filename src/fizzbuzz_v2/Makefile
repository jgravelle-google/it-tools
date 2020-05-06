run: build
	node shell.js
.PHONY: run

build: out out/fizz.wasm out/buzz.wasm out/fizzbuzz.wasm \
out/fizzbuzz.itl out/fizzbuzz.cpp \
out/fizz.js out/buzz.js out/fizzbuzz.js

out:
	mkdir -p out

out/%.itl out/%.cpp out/%_impl.h: %.cpp
	python ../cpp_itl_generator.py $<

out/%.js: out/%.itl
	python ../adapter.py $<

out/%.wasm: out/%.cpp out/%_impl.h out/%.js
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11
