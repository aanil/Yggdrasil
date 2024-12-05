from typing import Any, Dict, Type


class SingletonMeta(type):
    """
    A metaclass that creates a singleton instance of a class.
    """

    _instances: Dict[type, Any] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def singleton(cls: Type[Any]) -> Type[Any]:
    """
    Decorator to make a class a singleton by setting its metaclass to SingletonMeta.

    Args:
        cls (Type[Any]): The class to be decorated.

    Returns:
        Type[Any]: The singleton class with SingletonMeta as its metaclass.
    """

    # Create a new class with SingletonMeta as its metaclass
    class SingletonClass(cls, metaclass=SingletonMeta):
        pass

    # Preserve class metadata
    SingletonClass.__name__ = cls.__name__
    SingletonClass.__doc__ = cls.__doc__
    SingletonClass.__module__ = cls.__module__
    SingletonClass.__annotations__ = getattr(cls, "__annotations__", {})

    return SingletonClass
