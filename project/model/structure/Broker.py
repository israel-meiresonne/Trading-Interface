from abc import abstractmethod
from model.structure.database.ModelFeature import ModelFeature


class Broker(ModelFeature):
    @abstractmethod
    def __init__(self):
        pass
