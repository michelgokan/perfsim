from pathlib import Path
from pprint import pprint
from unittest import TestLoader, TestResult


# from perfsim.tests import BaseTest


def run_tests():
    test_loader = TestLoader()
    test_result = TestResult()

    test_directory = \
        str(Path(__file__).resolve().parent / 'test_single_service_chain/test_single_service/test_single_replica')
    # test_directory = str(Path(__file__).resolve().parent)
    test_suite = test_loader.discover(test_directory, pattern='test_*.py')
    test_suite.run(test_result)

    if test_result.wasSuccessful():
        exit(0)
    else:
        # Here you can either print or log your test errors and failures
        # test_result.errors or test_result.failures
        pprint(test_result.errors)
        pprint(test_result.failures)
        exit(-1)


if __name__ == '__main__':
    run_tests()
