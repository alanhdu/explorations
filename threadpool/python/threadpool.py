from collections import deque
import enum
import threading


@enum.unique
class State(enum.Enum):
    CANCELLED = enum.auto()
    DONE = enum.auto()
    RUNNING = enum.auto()
    WAITING = enum.auto()


class Future(object):
    def __init__(self, lock):
        self.state = State.WAITING
        self.event = threading.Event()

        self.lock = lock

        self._result = None
        self._exception = None

    def done(self):
        return self.state in {State.DONE, State.CANCELLED}

    def result(self, timeout=None):
        self.event.wait(timeout)
        if self.event.is_set():
            if self._exception is not None:
                raise self._exception
            return self._result
        raise RuntimeError("Time Out")

    def cancel(self) -> bool:
        with self.lock:
            if self.state == State.WAITING:
                self.state = State.CANCELLED
                return True
            return False


class ThreadPoolExecutor(object):
    def __init__(self, n: int):
        self._shutdown = False
        self.empty = threading.Event()
        self.empty.set()

        self.available = threading.Condition()
        self.threads = [threading.Thread(target=self._run) for __ in range(n)]
        self.work = deque()

        for thread in self.threads:
            thread.start()

    def _get_work(self):
        with self.available:
            while self.work:
                future, func, args, kwargs = self.work.popleft()

                assert future.state in {State.CANCELLED, State.WAITING}
                if future.state == State.WAITING:
                    future.state = State.RUNNING
                    return future, func, args, kwargs

            # No work to be done, so wait
            if len(self.work) == 0:
                self.empty.set()
                self.available.wait()

            return None, None, None, None

    def _run(self):
        while not self._shutdown:
            future, func, args, kwargs = self._get_work()
            if future is not None:
                future.state = State.RUNNING
                try:
                    future._result = func(*args, **kwargs)
                except Exception as e:
                    future._exception = e
                future.state = State.DONE
                future.event.set()

    def submit(self, func, *args, **kwargs) -> Future:
        f = Future(self.available)

        with self.available:
            self.work.append((f, func, args, kwargs))
            # Clear *before* notifying to avoid race
            self.empty.clear()
            self.available.notify()
        return f

    def shutdown(self, wait=True):
        assert all(thread.is_alive() for thread in self.threads)

        if wait:
            self.empty.wait()

        self._shutdown = True
        with self.available:
            self.available.notify_all()

        if wait:
            for thread in self.threads:
                thread.join()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.shutdown()
