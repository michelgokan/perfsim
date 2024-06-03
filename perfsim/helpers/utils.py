#  Copyright (C) 2020 Michel Gokan Khan
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#  This file is a part of the PerfSim project, which is now open source and available under the GPLv2.
#  Written by Michel Gokan Khan, February 2020

import json
import os
from typing import Any, TextIO, Union

from IPython.display import Image, display


class Utils:
    @staticmethod
    def mkdir_p(dir_path: str):
        """
        Creates a directory. equivalent to using mkdir -p on the command line

        :param dir_path: path to the directory
        """

        if '.' in dir_path:
            dir_path = os.path.dirname(dir_path)

        from errno import EEXIST
        from os import makedirs, path
        try:
            makedirs(dir_path)
        except OSError as exc:  # Python >2.5
            if exc.errno == EEXIST and path.isdir(dir_path):
                pass
            else:
                raise

    @staticmethod
    def save_file(file_path: str, content: Any):
        """
        Save a file with the given content

        :param file_path:
        :param content:
        :return:
        """

        with open(file_path, 'w') as f:
            f.write(content)

    @staticmethod
    def view_pydot(pdot):
        """
        View a pydot object in Jupyter notebook

        :param pdot:
        :return:
        """

        plt = Image(pdot.create_png())
        display(plt)

    @staticmethod
    def save_results_json(result, save_dir) -> str:
        """
        Save the results in a JSON file and return the file path

        :param result: Results to save
        :param save_dir: The directory to save the file
        :return: Returns the file path
        """

        file_path = save_dir + ".json"
        Utils.mkdir_p(file_path)

        with open(file_path, 'w') as fp:
            json.dump(result, fp, indent=2)

        return file_path

    @staticmethod
    def write_a_line_to_a_log_file_static(log_file: TextIO, time: Union[str, int], txt: str):
        """
        Write a line to a log file

        :param log_file: The log file
        :param time: The time
        :param txt: The text to write
        :return: Returns None
        """

        log_file.write(f"{time},{txt}\n")
        log_file.close()
