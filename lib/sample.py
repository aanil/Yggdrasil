from lib.technology import Multiome

class Sample:
    def __init__(self, sample_id, original_name, species, is_nuclei, project, technology):
        self.sample_id = sample_id
        self.original_name = original_name
        self.species = species
        self.is_nuclei = is_nuclei
        self.project = project
        self.past_projects = []
        self.technology = technology
        self.flowcells = []

        # Validate is_nuclei for Multiome samples
        if isinstance(self.technology, Multiome) and not self.is_nuclei:
            raise ValueError("Multiome samples must have is_nuclei set to True")

    def add_flowcell(self, flowcell):
        self.flowcells.append(flowcell)

    def add_project(self, new_project):
        if self.project is not None:
            self.past_projects.append(self.project)
        self.project = new_project

    # Other methods for managing metadata, sequencing status, etc.


