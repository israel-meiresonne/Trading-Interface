from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature


class Strategy(ModelFeature):
    @abstractmethod
    def __init__(self):
        pass
