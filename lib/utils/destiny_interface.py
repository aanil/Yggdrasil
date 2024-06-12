
from abc import ABC, abstractmethod
import warnings

class DestinyInterface(ABC):
    """
    DestinyInterface serves as an abstract base for different 'destiny' strategies in the Yggdrasil application.
    It defines the interface for processing documents, where each destiny encapsulates a unique pathway
    or processing logic, akin to the diverse fates woven by the Norns under Yggdrasil.
    """
    def __init__(self):
        warnings.warn("DestinyInterface is deprecated and will be removed in future releases, use RealmTemplate instead.", DeprecationWarning)

    @abstractmethod
    def process(self, doc):
        """
        Process a document according to the specific destiny (strategy). This method needs to be implemented 
        by each concrete destiny class, defining how each document's journey unfolds.

        :param doc: The document to be processed.
        """
        pass
