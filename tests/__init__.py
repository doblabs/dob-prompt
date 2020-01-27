# This file is part of 'dob_prompt'.
#
# 'dob_prompt' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'dob_prompt' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'dob_prompt'.  If not, see <http://www.gnu.org/licenses/>.

"""Testsuite for ``dob_prompt``."""

import datetime

__all__ = (
    'truncate_to_whole_seconds',
)


def truncate_to_whole_seconds(time):
    time_fmt = '%Y-%m-%d %H:%M'
    return datetime.datetime.strptime(time.strftime(time_fmt), time_fmt)

