import concurrent.futures
from functools import wraps

import requests

__all__ = ["delete", "get", "head", "options", "patch", "post", "put",
           "map", "imap"]

def async_wrap(func):
    @wraps(func)
    def async(*args, **kwargs):
        return (func, args, kwargs)

    return async

delete = async_wrap(requests.delete)
get = async_wrap(requests.get)
head = async_wrap(requests.head)
options = async_wrap(requests.options)
patch = async_wrap(requests.patch)
post = async_wrap(requests.post)
put = async_wrap(requests.put)

def execute(stuff):
    func, args, kwargs = stuff
    return func(*args, **kwargs)

def map(fs, workers=4, timeout=None):
    with concurrent.futures.ThreadPoolExecutor(workers) as executor:
        return executor.map(execute, fs, timeout=timeout)

def imap(fs, workers=4, timeout=None):
    with concurrent.futures.ThreadPoolExecutor(workers) as executor:
        futures = {executor.submit(execute, f) for f in fs}
        for future in concurrent.futures.as_completed(futures, timeout):
            yield future.result()
