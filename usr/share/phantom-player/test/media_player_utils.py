#!/usr/bin/python3

#
#   This file is part of Phantom Player.
#
# Copyright (c) 2014-2016, 2024-2025 Rafael Senties Martinelli.
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of either:
#
#   - the GNU Lesser General Public License as published by
#     the Free Software Foundation, version 2.1 only, or
#
#   - the GNU General Public License as published by
#     the Free Software Foundation, version 3 only.
#
# This file is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the applicable licenses for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# version 2.1 and the GNU General Public License version 3
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: LGPL-2.1-only OR GPL-3.0-only

"""To create unittary tests..."""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from env import *
from view.GtkPlayer import milliseconds_to_str

for input_value, expected_output in ((-1, "00:00"),
                                     (0, "00:00"),
                                     (1, "00:00"),
                                     (1000, "00:01"),
                                     (1000*59, "00:59"),
                                     (1000*60, "01:00"),
                                     (1000*60*60, "1:00:00"),
                                     (1000*60*60*3, "3:00:00"),
                                     (1000*60*60*24, "1 day, 0:00:00")):

    output = milliseconds_to_str(input_value)
    if output != expected_output:
        raise ValueError(f"input={input_value}, expected output={expected_output}, output={output}")