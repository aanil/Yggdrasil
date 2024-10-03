from abc import ABC, abstractmethod


class AbstractSample(ABC):
    """Abstract base class representing a sample in the Yggdrasil application.

    The `AbstractSample` class serves as a template for all sample classes within
    different modules of the application. It defines the essential properties and
    methods that every sample should have, ensuring consistency and enforcing the
    implementation of required functionalities in subclasses.

    Attributes:
        id (str): Unique identifier for the sample.
        status (str): Current processing status of the sample.

    Methods:
        post_process(): Define post-processing actions for the sample after processing
            is complete.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for the sample.

        Returns:
            str: The unique ID of the sample.
        """
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """Current processing status of the sample.

        Returns:
            str: The current status of the sample.
        """
        pass

    @status.setter
    @abstractmethod
    def status(self, value: str) -> None:
        """Set the current processing status of the sample.

        Args:
            value (str): The new status to set for the sample.
        """
        pass

    @abstractmethod
    def post_process(self) -> None:
        """Define post-processing actions for the sample.

        This method should be implemented by subclasses to handle any required
        post-processing after the sample's main processing is complete.
        """
        pass
