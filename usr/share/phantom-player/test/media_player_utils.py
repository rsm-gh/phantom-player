#!/usr/bin/python3

#
# MIT License
#
# Copyright (c) 2014-2016, 2024 Rafael Senties Martinelli.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""To create unittary tests..."""

from view.MediaPlayerWidget import milliseconds_to_str, format_track

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