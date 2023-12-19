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

__all__ = (
    'InterfaceBuilder',
    'InterfaceSection',
    'InterfaceStyle',
)


class InterfaceStyle(object):
    """
    """

    @property
    def color_1(self):
        raise NotImplementedError

    @property
    def color_2(self):
        raise NotImplementedError

    @property
    def color_3(self):
        raise NotImplementedError


class InterfaceSection(object):
    """
    """

    def __init__(self, colors=None):
        self.colors = colors
        self.prev_section = None
        self.next_section = None
        self.parts = None
        self.unfmt = None
        self.reset()

    def reset(self, parts=None, unfmt=None):
        parts_unfmt = (self.parts, self.unfmt)
        self.parts = parts or []
        self.unfmt = unfmt or ''
        self._max_width = None
        return parts_unfmt

    # ***

    @property
    def color_1(self):
        return self.colors.color_1

    @property
    def color_2(self):
        return self.colors.color_2

    @property
    def color_3(self):
        return self.colors.color_3

    # ***

    @property
    def first(self):
        return self.prev_section is None

    @property
    def last(self):
        return self.next_section is None

    # ***

    def __str__(self):
        return (
            'parts: {} / unfmt: {} / col: {} / max_w: {}'
            .format(
                self.parts, self.unfmt, self.colors, self._max_width,
            )
        )

    # ***

    def add_normal(
        self,
        text,
        bg=None,
        fg=None,
        prefix=False,
        bold=False,
        italic=False,
        underline=False,
    ):
        if not text:
            return
        if callable(text):
            text = text()
        bg = bg or self.color_1
        fg = fg or self.color_2
        bold = ' bold' if bold else ''
        italic = ' italic' if italic else ''
        underline = ' underline' if underline else ''
        part = (
            'bg:#{bg} fg:#{fg}{bold}{italic}{underline}'.format(
                bg=bg, fg=fg, bold=bold, italic=italic, underline=underline,
            ), text,
        )
        self.add_part(part, text, prefix)

    def add_part(self, part, text, prefix):
        if not prefix:
            self.parts.append(part)
            self.unfmt += text
        else:
            self.parts.insert(0, part)
            self.unfmt = text + self.unfmt

    def add_zinger(self, zinger, bg=None, fg=None, **kwargs):
        if not zinger:
            return
        bg = bg or self.color_3
        fg = fg or self.color_2
        self.add_normal(zinger, bg=bg, fg=fg, **kwargs)

    def add_lamron(self, text, bg=None, fg=None, **kwargs):
        if not text:
            return
        bg = bg or self.color_2
        fg = fg or self.color_1
        self.add_normal(text, bg=bg, fg=fg, **kwargs)

    # ***

    def render_edges_banner(self):
        head = '┏━' if self.first else '┳━'
        tail = '━┓' if self.last else '━'
        self.justify_content(head, tail, '━')

    def render_edges_bottom(self):
        head = '┗━' if self.first else '┻━'
        tail = '━┛' if self.last else '━'
        self.justify_content(head, tail, '━')

    def render_edges_middle(self):
        head = '┃ '
        tail = ' ┃' if self.last else ' '
        return self.justify_content(head, tail, ' ')

    def render_deadspace(self, term_width):
        avail = term_width - len(self.unfmt)
        if avail < 1:
            return
        self.add_lamron(' ' * avail)

    # ***

    def justify_content(self, head, tail, fill):
        headed, tailed = self.stretch_borders(head, tail, fill)
        self.add_zinger(headed, prefix=True)
        self.add_zinger(tailed)

    def stretch_borders(self, head, tail, fill):
        avail = self.avail_width
        headed = head
        headed += fill * int(avail / 2.)
        tailed = fill * (avail - int(avail / 2.))
        tailed += tail
        return headed, tailed

    @property
    def avail_width(self):
        taken = len(self.unfmt)
        avail = self.max_width - taken
        avail = avail if avail > 0 else 0
        return avail

    @property
    def max_width(self):
        if self._max_width is not None:
            return self._max_width

        parts, unfmt = self.reset()
        self.render()
        self._max_width = len(self.unfmt)
        self.reset(parts, unfmt)
        return self._max_width

    # ***

    # (lb): A weird little bit of code. Rather than building parts
    # only up to some width (e.g., the terminal width), build all
    # parts, and then remove those longer than the desired width.
    # The benefit of the latter approach is that, once assembled,
    # the parts are homogeneous, in that we only care about the
    # text part of the tuple, and not the style; if we wanted to
    # code the builder to stop building at a certain width, we'd
    # have to muck with the render functions -- add_normal(), etc. --
    # which I think we make those methods a lot less readable. It
    # seems easier to keep the logic separate, but running truncate
    # as a post-processing operation. (Did I really need to explain
    # all this?)
    def truncate(self, max_width, notice=''):
        if not self.parts:
            return
        max_width_idx = self.idx_at_width(max_width)
        if max_width_idx < 0:
            return
        self.truncate_parts(notice, max_width, max_width_idx)

    def idx_at_width(self, max_width):
        idx_at_width = -1
        cur_width = 0
        for idx, part in enumerate(self.parts):
            cur_width += len(part[1])
            if cur_width > max_width:
                idx_at_width = idx
                break
        return idx_at_width

    def truncate_parts(self, notice, max_width, max_width_idx):
        new_ending = '...{}'.format(notice)
        width_ending = len(new_ending)
        trun_width = max_width - width_ending
        self.truncate_parts_from(max_width_idx, trun_width, new_ending)

    def truncate_parts_from(self, max_width_idx, trun_width, new_ending):
        unfmt_to_idx = ''.join([part[1] for part in self.parts[:max_width_idx + 1]])
        rest = len(unfmt_to_idx) - trun_width
        assert rest > 0
        self.parts = self.truncate_parts_whittle(idx=max_width_idx, rest=rest)
        self.unfmt = ''.join([part[1] for part in self.parts])
        self.add_normal(new_ending, italic=True)

    def truncate_parts_whittle(self, idx, rest):
        parts = []
        while idx >= 0:
            part = self.parts[idx]
            if rest <= 0:
                parts.append(part)
            elif rest >= len(part[1]):
                rest -= len(part[1])
            else:
                parts.append((part[0], part[1][:-rest]))
                rest = 0
            idx -= 1
        parts.reverse()
        return parts

    # ***

    def render(self):
        return self.parts


class InterfaceBuilder(object):
    """
    """

    def __init__(self, colors):
        self.colors = colors
        # Lookup of nested arrays.
        self.sections = []
        self.clear()

    def clear(self):
        self._parts = []

    def wire_linked_list(self, section):
        if not self.sections:
            return
        prev_section = self.sections[-1]
        section.prev_section = prev_section
        prev_section.next_section = section

