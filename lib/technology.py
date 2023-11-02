from abc import ABC

class Technology(ABC):
    pass

class SS3(Technology):
    def __init__(self, barcode_set):
        self.barcode_set = barcode_set

class Chromium(Technology, ABC):
    pass

class GeneExpression(Chromium):
    def __init__(self, metadata):
        # Metadata attributes specific to GeneExpression
        self.metadata = metadata

class VDJ(Chromium):
    def __init__(self, metadata, enrichment_types):
        # Metadata attributes specific to VDJ
        self.metadata = metadata
        self.enrichment_types = enrichment_types

class Multiome(Chromium):
    def __init__(self, metadata):
        # Metadata attributes specific to Multiome
        self.metadata = metadata
