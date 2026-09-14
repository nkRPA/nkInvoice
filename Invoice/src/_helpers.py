import functools
import inspect

def _exception_helper(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise RuntimeError(f"Error in function '{func.__name__}': {e}") from e
        return async_wrapper

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Error in function '{func.__name__}': {e}") from e

    return wrapper