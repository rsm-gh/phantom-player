#!/usr/bin/python3
#

#  Copyright (C) 2014-2015, 2024 Rafael Senties Martinelli.
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
# You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software Foundation,
#   Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from view.gtk_utils import get_default_color

_, _FONT_DEFAULT_COLOR = get_default_color('theme_text_color', on_error="#000000")
_, _FONT_NEW_COLOR = get_default_color('success_color', on_error="#009933")
_, _FONT_HIDE_COLOR = get_default_color('warning_color', on_error="#ff9900")
_, _FONT_ERROR_COLOR = get_default_color('error_color', on_error="#ff0000")
