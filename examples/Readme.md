# Code samples

This directory holds examples for use with the tools in this repo. It has two
functions, one is to show the sorts of things that Interface Types makes
possible. The other is to serve as test code.

# Implemented

These samples are buildable and runnable. They come with Makefiles that describe
how they are built + ran.

Today all the samples are built into Node modules and run from the command line.

### 01 - ITL

Introduces the ITL file format, a low-level IDL that targets IT.

### 02 - C++ DSL

Introduces a higher-level DSL for generating bindings for C++. Compiles to ITL,
which can then be translated into JS.

### 03- Static Linking (Wasm)

Demonstrates loading multiple wasm modules from one IT component.

# Planned

These samples are not.

### Self-hosting

IT linking implemented in Wasm. May depend on multiple memories.

### Static Component Linking

Loading multiple sub-components from one IT component.

### Structs

### Arrays

### Arrays of Strings
