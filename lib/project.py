class Project:
    def __init__(self, ilabs_id, main_pi, main_contact):
        self.ilabs_id = ilabs_id
        self.ngi_projects = {}
        self.main_pi = main_pi
        self.additional_pis = []
        self.main_contact = main_contact
        self.additional_contacts = []
        self.samples = []

    def add_sample(self, sample):
        self.samples.append(sample)

    def remove_sample(self, sample_id):
        self.samples = [s for s in self.samples if s.sample_id != sample_id]

    def update_sample(self, sample):
        for i, s in enumerate(self.samples):
            if s.sample_id == sample.sample_id:
                self.samples[i] = sample
                break

    def add_additional_pi(self, pi):
        self.additional_pis.append(pi)

    def remove_additional_pi(self, pi):
        self.additional_pis.remove(pi)

    def add_additional_contact(self, contact):
        self.additional_contacts.append(contact)

    def remove_additional_contact(self, contact):
        self.additional_contacts.remove(contact)

    def add_ngi_project(self, ngi_project_id, ngi_subproject_id, flowcell_id):
        if ngi_project_id not in self.ngi_projects:
            self.ngi_projects[ngi_project_id] = {}
        if ngi_subproject_id not in self.ngi_projects[ngi_project_id]:
            self.ngi_projects[ngi_project_id][ngi_subproject_id] = []
        self.ngi_projects[ngi_project_id][ngi_subproject_id].append(flowcell_id)