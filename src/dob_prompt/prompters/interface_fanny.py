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

from .interface_bases import InterfaceBuilder, InterfaceSection

__all__ = (
    'BindingsBarBuilder',
    # Private:
    #   'BindingsSection',
)


# ***

class BindingsSection(InterfaceSection):
    """
    """

    def __init__(self, bindings, plinth, colors=None, reserve_width=0):
        super(BindingsSection, self).__init__(colors=colors)
        self.bindings = bindings
        self._plinth = plinth
        self.reserve_width = reserve_width

    # ***

    @property
    def plinth(self):
        if callable(self._plinth):
            return self._plinth()
        return self._plinth

    def __str__(self):
        return (
            '{} / # bindngs: {} / # plinth: {} / reserve_w: {} / max_w: {}'
            .format(
                super(BindingsSection, self).__str__(),
                len(self.bindings),
                len(self._plinth),
                self.reserve_width,
                self.max_width,
            )
        )

    # ***

    @property
    def max_width(self):
        if self._max_width is not None:
            return self._max_width

        parts, unfmt = self.reset()
        max_width = max(
            self.max_width_row_0,
            self.max_width_row_1,
        )
        self.reset(parts, unfmt)
        self._max_width = max_width
        return self._max_width

    @property
    def max_width_row_0(self):
        self.reset()
        for idx, binding in enumerate(self.bindings):
            self.add_key_hint(idx, binding)
            briefs = binding.briefs
            if callable(briefs):
                briefs = briefs()
            lenest_binding = max(briefs, key=len)
            self.add_brief_hint(lenest_binding)
        max_width = len(self.unfmt) + self.reserve_width
        return max_width

    @property
    def max_width_row_1(self):
        self.reset()
        self.render_pedestal_hint()
        return len(self.unfmt)

    # ***

    def render(self, row):
        getattr(self, 'render_row_{}'.format(row))()
        return self.parts

    def render_row_0(self):
        self.reset()
        self.render_binding_hints()
        self.render_edges_middle()

    def render_row_1(self):
        self.reset()
        self.render_pedestal_hint()
        self.render_edges_bottom()

    # ***

    def render_binding_hints(self):
        for idx, binding in enumerate(self.bindings):
            self.render_binding_hint(idx, binding)

    def render_binding_hint(self, idx, binding):
        highlight = binding.highlight
        self.add_key_hint(idx, binding, highlight)
        self.add_brief_hint(binding, highlight)

    def add_key_hint(self, idx, binding, highlight=False):
        if not binding.keycode:
            return

        prefix = ' ' if idx > 0 else ''
        self.add_normal(prefix)
        self.add_key_hint_parts(binding.key_hint, highlight)
        self.add_normal(' ')

    def add_key_hint_parts(self, key_hint, highlight):
        if highlight:
            self.add_zinger('[')
            self.add_lamron(key_hint)
            self.add_zinger(']')
        else:
            keycode = '[{}]'.format(key_hint)
            self.add_lamron(keycode)

    def add_brief_hint(self, binding_or_brief, highlight=False):
        try:
            brief_hint = binding_or_brief.brief
        except AttributeError:
            brief_hint = binding_or_brief
        if not highlight:
            self.add_normal(brief_hint)
        else:
            self.add_zinger(brief_hint)

    # ***

    def render_pedestal_hint(self):
        padded = ' {} '.format(self.plinth)
        self.add_zinger(padded)


# ***

class BindingsBarBuilder(InterfaceBuilder):
    """
    """

    def __init__(self, colors):
        super(BindingsBarBuilder, self).__init__(colors=colors)
        self.footers = []

    # ***

    def add_bindings(self, bindings, plinth, reserve_width=0):
        section = BindingsSection(
            bindings, plinth, reserve_width=reserve_width, colors=self.colors,
        )
        self.wire_linked_list(section)
        self.sections.append(section)

    def add_footer(self, footer):
        self.footers.append(footer)

    # ***

    def parts(self, prompt=None):
        if self._parts:
            return self._parts
        self.assemble_parts_rows()
        self.assemble_parts_footers()
        return self._parts

    def assemble_parts_rows(self):
        nrows = 2
        for row in range(nrows):
            for section in self.sections:
                self._parts += section.render(row)
            if row < (nrows - 1):
                self._parts.append(('', '\n'))

    def assemble_parts_footers(self):
        for footer in self.footers:
            dummy = InterfaceSection(colors=self.colors)
            if callable(footer):
                footer = footer(self, dummy)

            if isinstance(footer, str):
                dummy.add_normal(footer)
                parts = dummy.parts
            else:
                parts = footer
            self._parts += parts

    # ***

    @property
    def first_line_len(self):
        line_width = 0
        for part in self.parts():
            lines = part[1].split('\n', 2)
            line_width += len(lines[0])
            if len(lines) == 2:
                break
        return line_width

    def max_width(self):
        max_width = sum([section.max_width for section in self.sections])
        return max_width

