from typing import Any, Callable, Dict, Type, TypeVar

T = TypeVar("T")


def singleton(cls: Type[T]) -> Callable[..., T]:
    """Decorator to make a class a singleton.

    Ensures that only one instance of the class is created. Subsequent
    calls to the class will return the same instance.

    Args:
        cls (Type[T]): The class to be decorated.

    Returns:
        Callable[..., T]: A function that returns the singleton instance of the class.
    """
    instances: Dict[Type[T], T] = {}
    
    def get_instance(*args: Any, **kwargs: Any) -> T:
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance