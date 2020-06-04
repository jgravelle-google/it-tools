run: build
	node --experimental-wasm-anyref shell.js
.PHONY: run

build: out out/fizz.wasm out/buzz.wasm out/fizzbuzz.wasm

out:
	mkdir -p out

out/%.cpp out/%.itl: %.cpp
	# TODO: explicit outputs here
	python ../../src/cpp_itl_generator.py $<

out/%.wasm: out/%.cpp out/%.itl
	python ../../src/wasm_adapter.py out/$*.itl -o out/it_$*.wat
	wat2wasm --enable-reference-types out/it_$*.wat -o out/it_$*.wasm --debug-names
	emcc $< -o $@ -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11
	wasm-decompile $@ -o out/$*.wade
