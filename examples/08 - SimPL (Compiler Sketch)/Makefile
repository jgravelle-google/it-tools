build: out out/parser.wasm

clean: out
	rm -r out/
.PHONY: clean

serve: build
	emrun --no_browser --port 8080 .
.PHONY: serve

out:
	mkdir -p out

out/%.cpp out/%.itl: %.cpp
	python ../../src/cpp_itl_generator.py $< --cpp out/$*.cpp --itl out/$*.itl --wasm out/$*.wasm

out/%.wasm: out/%.cpp out/%.itl
	python ../../src/adapter.py out/$*.itl -o out/$*.js
	emcc $< -o out/$*.wasm -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11 --no-entry --profiling-funcs
	wasm2wat out/$*.wasm -o out/$*.wat
	wasm-decompile out/$*.wasm -o out/$*.wade
