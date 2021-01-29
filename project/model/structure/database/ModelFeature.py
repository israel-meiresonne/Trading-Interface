from abc import abstractmethod
from model.structure.database.ModelAccess import ModelAccess


class ModelFeature(ModelAccess):
    @abstractmethod
    def __init__(self):
        pass
