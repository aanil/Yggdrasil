class YggMode:
    """
    Manages the development mode for the application.

    This class maintains and provides read-only access to whether the application
    should run in development mode. Once set, the development mode cannot be
    changed mid-run.
    """

    __dev_mode = False  # Development mode flag
    __already_set = False  # Flag to prevent changing the mode mid-run

    @classmethod
    def init(cls, dev: bool):
        """
        Sets the development mode if it has not been set before.
        Raises a RuntimeError when the mode is already set.
        """
        if cls.__already_set:
            # raise an exception or ignore repeated calls
            raise RuntimeError("YggMode already set. Cannot change mid-run.")
        cls.__dev_mode = dev
        cls.__already_set = True

    @classmethod
    def is_dev(cls) -> bool:
        """
        Returns True if the application is in development mode, otherwise False.
        """
        return cls.__dev_mode
