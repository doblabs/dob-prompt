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

"""``hamster``, ``hamster``, ``hamster``!!! a cuddly, furry time tracker."""

import os
import sys

from easy_as_pypi_getver import get_version as _get_version

__all__ = (
    "get_version",
    "__arg0name__",
    "__package_name__",
)

# Note that this package is a library, so __arg0name__ likely, e.g., 'dob'.
__arg0name__ = os.path.basename(sys.argv[0])

__package_name__ = "dob-prompt"

# This version is substituted on poetry-build by poetry-dynamic-versioning.
# - Consequently, __version__ remains empty when installed in 'editable' mode.
__version__ = ""


def get_version(include_head=False):
    return _get_version(
        package_name=__package_name__,
        reference_file=__file__,
        include_head=include_head,
    )
