package threadpool

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestNewThreadPoolExecutor(t *testing.T) {
	pool := NewThreadPoolExecutor(10)

	assert.Equal(t, pool.NumThreads, 10)
	assert.Empty(t, pool.queue)
	pool.Shutdown(false)
}

func TestBasicSubmit(t *testing.T) {
	pool := NewThreadPoolExecutor(1)
	defer pool.Shutdown(false)

	f := pool.Submit(func() interface{} {
		time.Sleep(time.Millisecond * 200)
		return 5
	})

	assert.False(t, f.Done())

	r := f.Result(time.Second)
	assert.Equal(t, 5, (*r).(int))
	assert.True(t, f.Done())
}

func TestBigSubmit(t *testing.T) {
	pool := NewThreadPoolExecutor(8)
	defer pool.Shutdown(false)

	n := 1000
	futures := make([]*Future, n, n)
	for i := 0; i < n; i++ {
		// ugh... closures
		func(i int) {
			futures[i] = pool.Submit(func() interface{} {
				return i
			})
		}(i)
	}

	for i := 0; i < n; i++ {
		r := futures[i].Result(time.Second)
		assert.Equal(t, i, (*r).(int))
		assert.True(t, futures[i].Done())
	}
}

func TestShutdownNow(t *testing.T) {
	pool := NewThreadPoolExecutor(8)

	for i := 0; i < 100; i++ {
		pool.Submit(func() interface{} {
			time.Sleep(time.Millisecond * 100)
			return 0
		})
	}

	c := make(chan int)

	go func() {
		pool.Shutdown(false)
		c <- len(pool.queue)
	}()

	select {
	case l := <-c:
		// Check that nothing has processed on the pool queue
		assert.Equal(t, len(pool.queue), l)
	case <-time.After(100 * time.Millisecond):
		t.Errorf("Shutdown took too long")
	}
}

func TestShutdownWait(t *testing.T) {
	pool := NewThreadPoolExecutor(10)

	futures := make([]*Future, 100, 100)
	for i := 0; i < 100; i++ {
		// ugh... closures
		func(i int) {
			futures[i] = pool.Submit(func() interface{} {
				time.Sleep(time.Millisecond * 10)
				return i
			})
		}(i)
	}

	pool.Shutdown(true)
	assert.Equal(t, len(pool.queue), 0)
	for i := 0; i < 100; i++ {
		r := futures[i].Result(time.Second)
		assert.Equal(t, i, (*r).(int))
		assert.True(t, futures[i].Done())
	}
}

func TestFutureDone(t *testing.T) {
	pool := NewThreadPoolExecutor(1)
	defer pool.Shutdown(false)

	f := pool.Submit(func() interface{} {
		return 1
	})

	time.Sleep(time.Millisecond)
	assert.True(t, f.Done())
}
