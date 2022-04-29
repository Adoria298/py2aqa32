# TODO List

- [ ] Memory Management - Scope
- [ ] If/elif/else
- [ ] Bitwise logic
- [ ] For loops
- [ ] Extensions: print, input, video_memory
- [ ] Functions
- [ ] Strings
- [ ] Multiplication & Division

# Memory Management

At present rates,programs will quickly run out of space in the registers.
We need to:
1. delete unreferenced and out-of-scope variables: garbage collection
2. transfer variables currently in scope but otherwise unused to the end of main memory when a register fills
    1. the simplest way to do this would be to transfer R0 first (though if you did that twice in quick succession you'd have to transfer it back)

The python programmer does not need to worry about addressing modes or an object's location in memory.

# Bitwise logic

i.e. AND, OR, NOT, XOR and the bitshifts

last part of the AQA spec that should be implemented.
The above are all ast.BinOp: MVN is an ast.Invert (though note that Python assumes signed integers).

# Extensions

Peter Higginson provides three extensions: INP, OUT and video memory.
(To facilitate video memory he provides indirect addressing for the compiler).

When a function is called we should check if it is `print`, `input`, or `cell_out`.
`cell_out` is a special builtin function that takes a cell and a colour and writes to video memory.
If it is one of these three it needs special assembly.
Other functions should be called like normal.

# Strings 

Strings will have to be represented as a series of chars in main memory.
As much as possible they should be loaded within one temporary register per string, with each char moved in and out as needed.

