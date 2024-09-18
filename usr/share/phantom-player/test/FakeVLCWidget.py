#!/usr/bin/python3

#
#  Copyright (C) 2024 Rafael Senties Martinelli.
#
#  This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License 3 as published by
#   the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.en.html>.
#
import math
from gi.repository import Gtk


class FakePlayer:

    def __init__(self):

        self.__media = False

    @staticmethod
    def event_manager():

        class EM:
            def connect(self, *_):
                pass

            def event_attach(self, *_):
                pass

        return EM()

    def get_state(self, *_):
        pass

    def set_time(self, *_):
        pass

    def set_media(self, *_):
        self.__media = True

    def stop(self, *_):
        pass

    def play(self, *_):
        pass

    def audio_set_volume(self, *_):
        pass

    def video_set_spu(self, *_):
        pass

    def will_play(self, *_):
        if not self.__media:
            return 0

        return 1


class FakeVLCWidget(Gtk.DrawingArea):
    __gtype_name__ = 'FakeVLCWidget'

    def __init__(self):
        super().__init__()

        self._player = FakePlayer()
        self.set_draw_func(self.__on_draw)

    @staticmethod
    def __on_draw(_drawing_area, cairo_ctx, width, height):
        cairo_ctx.set_source_rgb(.5, .6, .8)
        cairo_ctx.paint()

        cairo_ctx.set_line_width(9)
        cairo_ctx.set_source_rgb(0.7, 0.2, 0.0)

        cairo_ctx.translate(width / 2, height / 2)
        cairo_ctx.arc(0, 0, 50, 0, 2 * math.pi)
        cairo_ctx.stroke_preserve()

        cairo_ctx.set_source_rgb(0.3, 0.4, 0.6)
        cairo_ctx.fill()
