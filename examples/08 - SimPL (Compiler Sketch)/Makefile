serve: build
	emrun --no_browser --port 8080 .
.PHONY: serve

build: out out/parser.wasm

out:
	mkdir -p out

out/%.cpp out/%.itl: %.cpp
	python ../../src/cpp_itl_generator.py $< --cpp out/$*.cpp --itl out/$*.itl --wasm out/$*_core.wasm

out/%.wasm: out/%.cpp out/%.itl
	python ../../src/wasm_adapter.py out/$*.itl -o out/$*.wat
	wat2wasm --enable-reference-types out/$*.wat -o out/$*.wasm --debug-names
	emcc $< -o out/$*_core.wasm -O1 -s ERROR_ON_UNDEFINED_SYMBOLS=0 -Iout -I. -std=c++11 --no-entry --profiling-funcs
	wasm-decompile out/$*_core.wasm -o out/$*_core.wade
