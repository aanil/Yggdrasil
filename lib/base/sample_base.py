
class SampleBase:
    @property
    def id(self):
        raise NotImplementedError("Subclasses must implement an 'id' property.")
    
    @property
    def status(self):
        raise NotImplementedError("Subclasses must implement a 'status' property.")
    
    @status.setter
    def status(self, value):
        raise NotImplementedError("Subclasses must implement a 'status' setter.")
    
    def post_process(self):
        raise NotImplementedError("Subclasses must implement a 'post_process' method.")