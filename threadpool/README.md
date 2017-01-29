Earlier this year, I interviewed at Dropbox. One of their interview
questions essentially boiled down to implementing the
`ThreadPoolExecutor` from `concurrent.futures` in Python. I'm ashamed to
admit that I totally choked and floundered for about 20 minutes before
starting to converge on a solution (which I didn't finish).

To make myself feel better, I decided to finish 3 different
implementations:

- One in Go, based on my original solution using message passing
- One in Python, using only its `threading` module (which notably does
  *not* include a non-blocking queue
- One in Rust, to play around with types and lifetimes. Unfortunately,
  due to https://github.com/rust-lang/rust/issues/28796, I needed to use
  nightly Rust for my solution (at which point I decided to also take
  advantage of the unstable `impl Trait` feature). It has the nice
  feature of being lock-free (thanks to a nice lock-free queue from the
  Crossbeam create).
