A simple hashmap implemented in Rust. Collisions handled with linear
probing.

Implemented for the http://kpcbfellows.com/ application:

# To Run
Install Rust and Cargo by running:
```bash
curl -sSf https://static.rust-lang.org/rustup.sh | sh
```

Run `cargo build` to build the project and `cargo test` to run the
tests. All code can be found in `src/lib.rs`.

The test cases can also be found in `src/lib.rs`, at the bottom of the
source code.

# Instructions
Using only primitive types, implement a fixed-size hash map that
associates string keys with arbitrary data object references (you don't
need to copy the object). Your data structure should be optimized for
algorithmic runtime and memory usage. You should not import any external
libraries, and may not use primitive hash map or dictionary types in
languages like Python or Ruby.

The solution should be delivered in one class (or your language's
equivalent) that provides the following functions:

- constructor(size): return an instance of the class with pre-allocated
  space for the given number of objects.
- boolean set(key, value): stores the given key/value pair in the hash
  map. Returns a boolean value indicating success / failure of the
  operation.
- get(key): return the value associated with the given key, or null if
  no value is set.
- delete(key): delete the value associated with the given key, returning
  the value on success or null if the key has no value.
- float load(): return a float value representing the load factor
  (`(items in hash map)/(size of hash map)`) of the data structure.
  Since the size of the dat structure is fixed, this should never be
  greater than 1.

If your language provides a built-in hashing function for strings (ex.
`hashCode` in Java or `__hash__` in Python) you are welcome to use that.
If not, you are welcome to do something naive, or use something you find
online with proper attribution.
