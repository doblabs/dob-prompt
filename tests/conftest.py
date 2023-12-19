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

"""Packaged conftest shim."""

# (lb): When I split dob into multiple projects, I moved the fixtures to
# the furthest class upstream (dob-bright) which we glob back in to
# conftest like they were originally. This is at the expense of violating
# best practices, and the linter's good graces. But then we also don't
# have to class out all the fixtures in the import statement, which for
# some reason seems like an anti-pattern in pytest (import? just put it
# all in conftest.py, we'll import that silently for you, why not).

from dob_bright.tests.conftest import *  # noqa: F401, F403

pytest_plugins = (
    # Set KeyChainedValue._envvar_prefix.
    "tests.config.envvar_prefix",
    # Call app_dirs.register_application.
    "tests.config.init_app_dirs",
)
