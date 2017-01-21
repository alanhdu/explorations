Earlier this year, I interviewed at Dropbox. One of their interview
questions essentially boiled down to implementing the
`ThreadPoolExecutor` from `concurrent.futures` in Python. I'm ashamed to
admit that I totally choked and floundered for about 20 minutes before
starting to converge on a solution (which I didn't end up finishing).
Equally embarassingly, (and maybe partly why I choked), I realized that
I didn't actually *know* how to impelement a threadpool with primitives.

To make myself feel better, I went ahead and actually finished the
solution I was thinking of (although this time in Go, because goroutines
and channels make message passing super easy). If I have time, I might
go back and try to see what other implementations I can come up with.
