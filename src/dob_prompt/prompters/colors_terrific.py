# This file exists within 'dob-prompt':
#
#   https://github.com/tallybark/dob-prompt
#
# Copyright © 2019-2020 Landon Bouma. All rights reserved.
#
# This program is free software:  you can redistribute it  and/or  modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any later version  (GPLv3+).
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY;  without even the implied warranty of MERCHANTABILITY or  FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU  General  Public  License  for  more  details.
#
# If you lost the GNU General Public License that ships with this software
# repository (read the 'LICENSE' file), see <http://www.gnu.org/licenses/>.

from .interface_bases import InterfaceStyle

__all__ = (
    'TerrificColors1',
    'TerrificColors2',
    'TerrificColors3',
)


class TerrificColors1(InterfaceStyle):
    """
    """

    # (lb): I used colors from a palette I made, with no particular
    # goal other than being light and anti-distracting to the viewer.
    # They ended up kinda lightish redish brownish pinkish.
    #   http://paletton.com/#uid=1000u0kg0qB6pHIb0vBljljq+fD
    #
    # FIXME: Adjust colors based on terminal palette, i.e., support light backgrounds.
    #        (I've chosen colors that look good to me (I have no colorblindness)
    #        in a terminal configured how I like, which is white text on true black.)
    #

    @property
    def color_1(self):
        return 'AA3939'

    @property
    def color_2(self):
        return 'FCA5A5'

    @property
    def color_3(self):
        return '7D1313'


class TerrificColors2(InterfaceStyle):
    """
    """

    # http://paletton.com/#uid=5000u0kg0qB6pHIb0vBljljq+fD

    @property
    def color_1(self):
        return '882E61'

    @property
    def color_2(self):
        return 'CA85AC'  # 'D49A6A'

    @property
    def color_3(self):
        return '641040'


class TerrificColors3(InterfaceStyle):
    """
    """

    # http://paletton.com/#uid=5000u0kg0qB6pHIb0vBljljq+fD

    @property
    def color_1(self):
        return 'AA6C39'

    @property
    def color_2(self):
        return 'FCCCA5'  # 'AA5585'

    @property
    def color_3(self):
        return '7D4313'

