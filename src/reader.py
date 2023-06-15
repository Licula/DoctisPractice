import ast
from abc import ABC, abstractmethod

import pandas as pd

from src.logger import logger


# Базовый класс чтения
class BaseReader(ABC):
    @abstractmethod
    def read(self, filename):
        pass


# Класс чтения КТГ из формата словаря
class DictReader(BaseReader):
    def read(self, filename: str) -> pd.DataFrame:
        with open(filename) as file:
            logger.info('File %s open', filename)

            graph_list = ast.literal_eval(file.read())

            x_coords = [coords.get('Key') for coords in graph_list]
            y_coords = [coords.get('Value') for coords in graph_list]
            coords = pd.DataFrame.from_dict(
                {
                    'x': x_coords,
                    'y': y_coords,
                },
            )
            logger.info('File %s readed', filename)

            return coords
