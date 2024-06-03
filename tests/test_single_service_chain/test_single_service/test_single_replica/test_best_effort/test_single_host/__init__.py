import os
import sys

path2add = os.path.normpath(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            os.path.pardir,
            '../../../../../tests')))

if not (path2add in sys.path):
    sys.path.append(path2add)

sys.path.append(
    os.path.normpath(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                os.path.pardir,
                '../../../../../tests/helpers'))))
