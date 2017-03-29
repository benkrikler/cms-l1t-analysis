from __future__ import print_function
import time


def timerfunc(printer=print):
    """
    A timer decorator
    """
    def wrapper(func):
        def function_timer(*args, **kwargs):
            """
            A nested function for timing other functions
            """
            start = time.time()
            value = func(*args, **kwargs)
            end = time.time()
            runtime = end - start
            msg = "The runtime for {func} took {time} seconds to complete"
            printer(msg.format(func=func.__name__,
                               time=runtime))
            return value
        return function_timer
    return wrapper
