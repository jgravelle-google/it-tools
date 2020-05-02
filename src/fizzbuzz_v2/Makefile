# run: build
#     node shell.js
# .PHONY: run

build: out out/fizz.js out/fizz.wasm
# out/buzz.wasm out/fizzbuzz.wasm

out:
	mkdir -p out

out/%.itl: %.cpp
	python ../cpp_itl_generator.py $<

out/%.js out/%_impl.h: out/%.itl
	python ../adapter.py $<

out/%.wasm: %.cpp out/%_impl.h
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -std=c++11
