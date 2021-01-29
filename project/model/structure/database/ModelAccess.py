from abc import abstractmethod
from model.structure.database.Model import Model


class ModelAccess(Model):
    @abstractmethod
    def __init__(self):
        pass
