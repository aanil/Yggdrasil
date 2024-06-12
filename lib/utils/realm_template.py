
from abc import ABC, abstractmethod
from lib.utils.sjob_manager import SlurmJobManager

class RealmTemplate(ABC):
    """
    RealmTemplate serves as a foundational framework for the diverse realms connected by Yggdrasil in the Yggdrasil application.
    Each realm (processing module) extends this template, defining its unique processing logic while adhering to 
    the core structure laid out by this class. It's akin to the various realms that Yggdrasil connects, 
    each with its own distinct characteristics.

    This template outlines the common steps and sequences, while allowing flexibility for specific realm implementations. 
    It ensures that while each realm follows its own internal rules, they are all integral parts of the greater 
    world tree, contributing to the overarching narrative and functionality of the application.
    """

    def __init__(self):
        self.sjob_manager = SlurmJobManager()

    @abstractmethod
    def pre_process(self, doc):
        """
        Pre-process the document. This method should be implemented by each realm to handle 
        preliminary processing specific to its requirements.

        :param doc: The document to be pre-processed.
        """
        pass

    @abstractmethod
    def process(self, doc):
        """
        Process the document. This method needs to be implemented by each concrete realm class,
        defining how each document's journey unfolds.

        :param doc: The document to be processed.
        """
        pass

    @abstractmethod
    def create_slurm_job(self, data):
        """
        Create a Slurm job for the given data. This method should be implemented to define 
        how each branch creates its specific Slurm job.

        :param data: The data to create a Slurm job for.
        """
        pass

    def submit_job(self, script):
        """
        Submit a job to the Slurm scheduler using the JobManager. This method standardizes
        job submission across different branches.

        :param script: The script or command to be submitted as a job.
        """
        # Assume self.job_manager is an instance of JobManager, initialized in the constructor
        return self.sjob_manager.submit_job(script)

    def monitor_job(self, job_id):
        """
        Monitor the status of a submitted Slurm job using the JobManager. This method provides
        a standardized way of monitoring jobs across different branches.

        :param job_id: The identifier of the submitted job to be monitored.
        """
        # Again, assuming self.job_manager is available
        return self.sjob_manager.monitor_job(job_id)

    @abstractmethod
    def post_process(self, result):
        """
        Post-process the results from the Slurm job. Each realm should implement this method 
        to handle post-processing specific to its outcome.

        :param result: The result from the Slurm job to be post-processed.
        """
        pass

