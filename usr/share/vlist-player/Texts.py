#!/usr/bin/python3
#

#  Copyright (C) 2014-2016, 2024 Rafael Senties Martinelli
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


class Texts:

    class GUI:
        title = "Video List Player"

    class MenuItemSeries:
        delete = "Delete"
        rename = "Rename"
        reset = "Reset"
        search = "Search"
        open_dir = "Open Directory"
        add_pic = "Add Image"

    class DialogSeries:
        confirm_delete = 'Are you sure that you want to delete "{0}"?\n\nThe files will not be deleted from your hard drive.'
        confirm_reset = 'Are you sure that you want to reset "{0}"?.'
        is_missing='The series can not be reproduced because the episodes are missing!\n\nUse the search button to find them.'
        already_exist='The series "{}" already exists.\n\nPlease rename the other series before adding this one.'
        name_exist='The series "{}" already exists.\n\nPlease choose a different name.'
        all_episodes_played = 'All the episodes of the series have been reproduced.'

    class MenuItemEpisodes:

        open_dir = "Open Directory"
        ignore = "Ignore"
        dont_ignore = "Don't Ignore"
        search = "Search"
        reproduce = "Play"
        o_played = "O-Played"
        r_played = "R-Played"

    class DialogEpisodes:
        delete = '''Are you sure that you want to delete the selected episodes?\n\nThey wont be removed from your hard drive.'''
        missing = 'The episode can not be reproduced because the file is missing. Use the search button to find it.'
        found_x = '{0} videos have been found.'
        other_found = '{0} other videos have been found.'