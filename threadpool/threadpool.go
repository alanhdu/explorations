package threadpool

import (
	"sync"
	"time"
)

type futureState int

const (
	done = iota
	running
	waiting
)

type Future struct {
	state    futureState
	function func() interface{}

	channel chan interface{}
}

type ThreadPoolExecutor struct {
	NumThreads int

	queue    chan *Future
	shutdown chan bool
	wg       sync.WaitGroup
}

func NewThreadPoolExecutor(n int) *ThreadPoolExecutor {
	t := &ThreadPoolExecutor{
		NumThreads: n,

		// TODO: I'm too lazy to implement a real non-blocking
		// channel, so just use a really high capacity
		queue:    make(chan *Future, 1024),
		shutdown: make(chan bool, n),
	}

	t.wg.Add(n)
	for i := 0; i < n; i++ {
		go func(i int) {
			t.run(i)
		}(i)
	}

	return t
}

func (t *ThreadPoolExecutor) run(id int) {
	defer t.wg.Done()

	var wait bool
	for {
		select {
		case future := <-t.queue:
			// channel was closed and we're done processing
			if future == nil {
				return
			}

			future.state = running
			result := future.function()
			future.state = done

			future.channel <- result
		case wait = <-t.shutdown:
			if !wait {
				return
			}
		}
	}
}

func (t *ThreadPoolExecutor) Submit(f func() interface{}) *Future {
	future := &Future{
		state:    waiting,
		function: f,

		channel: make(chan interface{}, 1),
	}

	t.queue <- future
	return future
}

func (t *ThreadPoolExecutor) Shutdown(wait bool) {
	for i := 0; i < t.NumThreads; i++ {
		t.shutdown <- wait
	}
	close(t.queue)
	if wait {
		t.wg.Wait()
	}
}

func (f *Future) Result(timeout time.Duration) *interface{} {
	select {
	case result := <-f.channel:
		return &result
	case <-time.After(timeout):
		return nil
	}
}

func (f *Future) Done() bool {
	return f.state == done
}
