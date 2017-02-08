import time
import threading

import pytest

from threadpool import ThreadPoolExecutor


@pytest.mark.timeout(0.1)
def test_contextmanager():
    with ThreadPoolExecutor(5) as pool:
        assert len(pool.work) == 0
        assert len(pool.threads) == 5


@pytest.mark.timeout(0.4)
def test_basic_submit():
    event = threading.Event()
    def func():
        event.wait()
        return 5

    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(func)
        assert not future.done()

        event.set()

        assert future.result() == 5
        assert future.done()


@pytest.mark.timeout(0.1)
def test_submit_error():
    def func():
        raise RuntimeError()

    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(func)

        with pytest.raises(RuntimeError):
            future.result()
        assert future.done()


@pytest.mark.timeout(1.5)
def test_big_submit():
    # Deal w/ closure problems
    def func(i):
        return lambda: i

    with ThreadPoolExecutor(8) as pool:
        futures = [pool.submit(func(i)) for i in range(1000)]

        for i, future in enumerate(futures):
            assert future.result() == i
            assert future.done()


@pytest.mark.timeout(0.5)
def test_shutdown_now():
    pool = ThreadPoolExecutor(8)

    for i in range(100):
        pool.submit(lambda: time.sleep(0.1))

    pool.shutdown(False)
    time.sleep(0.1)

    assert all(not thread.is_alive() for thread in pool.threads)
    assert len(pool.work) > 0


@pytest.mark.timeout(0.5)
def test_shutdown_wait():
    pool = ThreadPoolExecutor(4)

    for i in range(8):
        pool.submit(lambda: time.sleep(0.1))

    pool.shutdown()
    assert all(not thread.is_alive() for thread in pool.threads)
    assert len(pool.work) == 0


@pytest.mark.timeout(0.5)
def test_future_done():
    event = threading.Event()

    with ThreadPoolExecutor(1) as pool:
        f = pool.submit(event.wait)
        assert not f.done()

        event.set()

    assert f.done()
    assert f.result()


@pytest.mark.timeout(0.5)
def test_future_cancel():
    e1 = threading.Event()
    e2 = threading.Event()
    def func():
        e1.set()
        e2.wait()

    with ThreadPoolExecutor(1) as pool:
        f1 = pool.submit(func)
        e1.wait()    # func is running
        assert not f1.cancel()

        f2 = pool.submit(lambda: 1)
        assert f2.cancel()

        e2.set()
