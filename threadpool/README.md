Earlier this year, I interviewed at Dropbox. One of their interview
questions essentially boiled down to implementing the
`ThreadPoolExecutor` from `concurrent.futures` in Python. I'm ashamed to
admit that I totally choked and floundered for about 20 minutes before
starting to converge on a solution (which I didn't finish).

To make myself feel better, I decided to finish the implementation (in
Go, because goroutines and channels make are pretty nice primitives for
message passing). I also came up with an alternative solution in Python
using only things from Python's `threading` module (which notably does
*not* include the `queue` model).
