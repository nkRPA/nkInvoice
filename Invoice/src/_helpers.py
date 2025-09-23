import functools
import inspect

def _exception_helper(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            func_name = func.__name__  # same as inspect.currentframe().f_code.co_name
            raise RuntimeError(f"Error in function '{func_name}': {e}") from e
            
    return wrapper