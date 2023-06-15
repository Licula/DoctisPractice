import argparse
import pickle

from src.analyzer import CTGFisherAnalyzer
from src.compare_results import compare_results
from src.reader import DictReader
from src.vizualizer import CTGVisualizer

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--dir', default='./ctg_files')
    parser.add_argument('-p', '--processes', default=8)
    parser.add_argument('-visualize', action='store_const', const=True)

    args = parser.parse_args()

    if args.visualize:
        visualizer = CTGVisualizer(
            directory=args.dir,
            reader=DictReader,
            processes_count=int(
                args.processes,
            ),
        )

        visualizer.work()
    else:
        analyzer = CTGFisherAnalyzer(
            directory=args.dir,
            reader=DictReader,
            processes_count=int(
                args.processes,
            ),
        )

        expected_result = None

        with open('expected_result.txt', 'rb') as file:
            expected_result = pickle.load(file)

        calculated_result = analyzer.work()

        compare_results(expected_result, calculated_result)
