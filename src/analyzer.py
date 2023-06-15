import datetime
import multiprocessing
import os
import queue
from abc import ABC, abstractmethod
from math import ceil

from src.logger import logger
from src.reader import BaseReader


# Базовый анализатор
class CTGBaseAnalyzer(ABC):
    def __init__(
        self,
        directory: str,
        reader: BaseReader,
        processes_count: int = 8,
    ):
        self.directory = directory
        self.reader = reader
        self.processes_count = processes_count
        self.data_queue = multiprocessing.Queue()
        self.event = multiprocessing.Event()

    # Заполнение очереди задач
    def filling_queue(self):
        files = os.listdir(self.directory)
        files_count = len(files)
        process_files = ceil(files_count / self.processes_count)

        processes = [
            multiprocessing.Process(
                target=self.read_file,
                args=[
                    files[
                        border
                        * process_files: min(files_count, (border + 1) * process_files)
                    ],
                ],
                daemon=True,
            )
            for border in range(self.processes_count)
        ]

        for process in processes:
            process.start()
        logger.info('File reading processes started')

        for process in processes:
            process.join()
        logger.info('File read processes have finished executing')

        self.data_queue.put({'file': 'end_of_files'})

    # Считывание данных с одного файла
    def read_file(self, files):
        reader = self.reader()

        for file in files:
            _file = os.path.join(self.directory, file)

            if not os.path.isfile(_file):
                logger.warning('%s is not а file', _file)
                break

            data = reader.read(_file)

            if data is not None:
                self.data_queue.put({'file': file, 'ctg': data})
            else:
                logger.warning('Data of file: %s is None', _file)

            logger.debug('File: %s read', _file)

    # Запуск обработки данных
    def work(self):
        parent_conn, child_conn = multiprocessing.Pipe()

        processes = [
            multiprocessing.Process(
                target=self.analyze,
                args=[
                    child_conn,
                ],
                daemon=True,
            )
            for _ in range(self.processes_count)
        ]

        start = datetime.datetime.now()

        for process in processes:
            process.start()
        logger.info('Working processes started')

        self.filling_queue()

        for process in processes:
            process.join()
        logger.info('Working processes have finished executing')

        result_dict = {}

        count_end_processes = 0

        while True:
            if count_end_processes == self.processes_count:
                logger.info('All processes completed')
                break

            result = parent_conn.recv()

            if result == 'end_process':
                count_end_processes += 1
            else:
                result = result.split(':')
                result_dict[result[0]] = result[1]

        end = datetime.datetime.now()
        print(
            f'Время обработки одного файла {((end - start) / 100).microseconds} ms.',
        )

        return result_dict

    # Анализ КТГ
    @abstractmethod
    def analyze(self, pipe: multiprocessing.Pipe):
        pass


# Анализатор по шкале Фишера
class CTGFisherAnalyzer(CTGBaseAnalyzer):
    def __init__(
        self,
        directory: str,
        reader: BaseReader,
        processes_count: int = 8,
    ):
        super().__init__(directory, reader, processes_count)

        self.ctg_data = None
        self.basal_area = None

        self.basal_rhythm = None
        self.amplitude = None
        self.variability = None
        self.accelerations = None
        self.decelerations = None

    # Очистка КТГ от погрешности измерений
    def clear_ctg(self):
        error_data = self.ctg_data.loc[
            ((self.ctg_data['y'] < 80) | (self.ctg_data['y'] > 180))
        ]
        self.ctg_data.drop(error_data.index)

    # Вычисление базального ритма и амплитуды
    def get_basal_rhythm_and_amplitude(self):
        result = {'start': 0, 'end': 0, 'dist': 0, 'mean': 0, 'amplitude': 0}
        _min, _max = self.ctg_data['y'][0], self.ctg_data['y'][0]
        dist = 1
        start, end = 0, 0

        sum_values = 0

        for idx, curr in enumerate(self.ctg_data['y']):
            tmp_min, tmp_max = _min, _max
            if curr < _min:
                tmp_min = curr
            if curr > _max:
                tmp_max = curr

            if tmp_max - tmp_min < 25:
                sum_values += curr
                dist += 1
                end = idx
                _min, _max = tmp_min, tmp_max
            else:
                if result['dist'] < dist:
                    result = {
                        'start': start,
                        'end': end,
                        'dist': dist,
                        'mean': sum_values / dist,
                        'amplitude': _max - _min,
                    }

                _min, _max = curr, curr
                dist = 1
                start = idx
                sum_values = 0

        self.basal_area = (result['start'], result['end'])

        self.basal_rhythm = result['mean']
        self.amplitude = result['amplitude']

    # Вычисление вариабельности
    def get_variability(self):
        start, end = self.basal_area
        end = min(start + 180, end)

        if start == end:
            self.variability = 0

            return

        data = self.ctg_data['y'][start:end]

        unique_seq = [data.iloc[0]]

        pred = [data.iloc[0]]

        for curr in data:
            if pred != curr:
                pred = curr
                unique_seq.append(curr)

        count = 0

        for idx in range(1, len(unique_seq) - 1):
            if (
                unique_seq[idx] > unique_seq[idx - 1]
                and unique_seq[idx] < unique_seq[idx + 1]
            ) or (
                unique_seq[idx] < unique_seq[idx - 1]
                and unique_seq[idx] > unique_seq[idx + 1]
            ):
                count += 1

        self.variability = count

    # Вычисление акцелераций
    def get_acceleration(self):
        bool_array = self.ctg_data['y'] > self.basal_rhythm + 20

        pred = False
        pred_idx = -1
        dist = 0

        count = 0

        for idx, curr in bool_array.items():
            if curr and pred and idx == pred_idx + 1:
                dist += 1
                pred_idx = idx
            elif curr and not (pred):
                dist = 1
                pred = True
                pred_idx = idx
            elif pred and dist > 30:
                count += 1
                pred = False
                dist = 0
            else:
                pred = False
                dist = 0

        self.accelerations = count

    # Вычисление децелераций
    def get_decelerations(self):
        bool_array = self.ctg_data['y'] < self.basal_rhythm - 20

        pred = False
        pred_idx = -1
        dist = 0

        count = 0

        for idx, curr in bool_array.items():
            if curr and pred and idx == pred_idx + 1:
                dist += 1
                pred_idx = idx
            elif curr and not (pred):
                dist = 1
                pred = True
                pred_idx = idx
            elif pred and dist > 30:
                count += 1
                pred = False
                dist = 0
            else:
                pred = False
                dist = 0

        self.decelerations = count

    # Оценка полученных значений
    def performance_evaluation(self) -> str:
        basal_rhytm_grade = 0
        amplitude_grade = 0
        variability_grade = 0
        accelerations_grade = 0
        decelerations_grade = 0

        if 120 <= self.basal_rhythm <= 160:
            basal_rhytm_grade = 2
        elif self.basal_rhythm >= 100 and self.basal_rhythm <= 180:
            basal_rhytm_grade = 1

        if 6 <= self.amplitude <= 25:
            amplitude_grade = 2
        elif 3 <= self.amplitude <= 5:
            amplitude_grade = 1

        if self.variability > 6:
            variability_grade = 2
        elif 3 <= self.variability <= 6:
            variability_grade = 1

        if self.accelerations > 5:
            accelerations_grade = 2
        elif self.accelerations != 0:
            accelerations_grade = 1

        if self.decelerations == 0:
            decelerations_grade = 2
        elif self.decelerations == 1:
            decelerations_grade = 1

        if (
            sum(
                [
                    basal_rhytm_grade,
                    amplitude_grade,
                    variability_grade,
                    accelerations_grade,
                    decelerations_grade,
                ],
            )
            < 8
        ):
            return 'плохое'

        return 'хорошее'

    # Анализ КТГ
    def analyze(self, pipe: multiprocessing.Pipe):
        while not self.event.is_set():
            try:
                data = self.data_queue.get(timeout=1)
            except queue.Empty:
                logger.warning("Received an exception 'queue.Empty'")
                continue

            if data['file'] == 'end_of_files':
                logger.info("'end_of_files' line read from queue")

                self.event.set()
                logger.info('self.event is set')

                pipe.send('end_process')

                break

            self.ctg_data = data['ctg']

            self.clear_ctg()

            self.get_basal_rhythm_and_amplitude()
            self.get_variability()
            self.get_acceleration()
            self.get_decelerations()

            result = self.performance_evaluation()

            pipe.send(f"{data['file']}:{result}")

            logger.debug('processed %s', data['file'])
        else:
            pipe.send('end_process')
