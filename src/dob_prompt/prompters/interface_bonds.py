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

""""""

__all__ = (
    'KeyBond',
    # Private:
    #   'KeyCodeBriefly',
)


class KeyCodeBriefly(object):
    """
    """

    def __init__(
        self,
        keycode,
        brief,
        briefs=None,
        highlight=False,
        **kwargs
    ):
        self.keycode = keycode
        self._brief = brief
        self._briefs = briefs
        self._highlight = highlight
        for kw, arg in kwargs.items():
            setattr(self, kw, arg)

    def __str__(self):
        return 'keycode: {} / _brief: {}'.format(self.keycode, self._brief)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.keycode == other.keycode
        return False

    @property
    def brief(self):
        if callable(self._brief):
            return self._brief(self)
        return self._brief

    @property
    def briefs(self):
        if callable(self._briefs):
            return self._briefs(self)
        elif self._briefs:
            return self._briefs
        return [self._brief]

    @property
    def highlight(self):
        if callable(self._highlight):
            return self._highlight(self)
        return bool(self._highlight)

    @property
    def key_hint(self):
        if isinstance(self.keycode, str):
            key_hint = self.keycode.upper()
        elif len(self.keycode) == 1:
            # E.g., 'm-h' → 'M-h'.
            key_hint = self.keycode[0].capitalize()
        else:
            assert len(self.keycode) == 2
            assert self.keycode[0] == 'escape'
            key_hint = 'M-{}'.format(self.keycode[1].lower())
        return key_hint


# ***

class KeyBond(KeyCodeBriefly):
    """
    """

    def __init__(
        self,
        keycode,
        brief=None,
        # NOTE/2018-08-25: (lb): action should really not be None, but I
        # wanted to make brief optional, and I didn't want to edit all the
        # callers yet (to rearrange parameters).
        #   FIXME/MAYBE: Fix callers and make action required param again.
        action=None,
        wordy='',
        **kwargs
    ):
        super(KeyBond, self).__init__(keycode, brief, **kwargs)
        self.action = action
        self.wordy = wordy

    def __str__(self):
        return 'keycode: {} / _brief: {} / action: {} / wordy: {}'.format(
            self.keycode,
            self._brief,
            self.action,
            self.wordy,
        )

