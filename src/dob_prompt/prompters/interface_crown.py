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
    'BannerBarBuilder',
    # Private:
    #   'BannerSection',
)


class BannerSection(InterfaceSection):
    """
    """

    def __init__(self, content, max_width, term_width=0, colors=None):
        super(BannerSection, self).__init__(colors=colors)
        self.content = content
        gutter_width = 4  # I.e., len('┃ ' ... ' ┃')
        self.stretch_width = max_width - gutter_width
        self.term_width = term_width

    @property
    def max_width(self):
        # Ignoring base's self._max_width.
        return self.stretch_width

    def render(self, idx):
        self.reset()
        content = self.content
        if callable(content):
            content = content()
        self.render_content_at_idx(content, idx)
        self.render_deadspace(self.term_width)
        return self.parts

    def render_content_at_idx(self, content, idx):
        if idx == 0:
            self.italicize_and_underline(content, clean_spaces=True)
            self.render_edges_banner()
        else:
            padded = ' {} '.format(content)
            if idx == 1:
                self.add_zinger(padded, bold=True)
            else:
                self.add_zinger(padded)
            self.render_edges_middle()

    def add_zinger(self, zinger, bg=None, fg=None, **kwargs):
        super(BannerSection, self).add_zinger(
            zinger, bg=self.color_2, fg=self.color_3, **kwargs
        )

    def italicize_and_underline(self, content, clean_spaces=False):
        if not clean_spaces:
            self.italicize_and_underline_dirty(content)
        else:
            self.italicize_and_underline_clean(content)

    def italicize_and_underline_dirty(self, content):
        self.add_zinger(' ')
        self.add_zinger(self.content, italic=True, underline=True)
        self.add_zinger(' ')

    # (lb): Not sure what I like: underlined spaces in the title, or not.
    def italicize_and_underline_clean(self, content, noline_whitespace=False):
        self.add_zinger(' ')
        if noline_whitespace:
            for part in content.split(' '):
                self.add_zinger(part, italic=True, underline=True)
                self.add_zinger(' ')
        else:
            self.add_zinger(content, italic=True, underline=True)
            self.add_zinger(' ')


class BannerBarBuilder(InterfaceBuilder):
    """
    """

    def __init__(self, colors, term_width=0):
        super(BannerBarBuilder, self).__init__(colors=colors)
        # FIXME: Adjust term_width if user resizes terminal.
        self.term_width = term_width

    def add_content(self, *args, width=0):
        for text in args:
            section = BannerSection(
                text,
                width,
                term_width=self.term_width,
                colors=self.colors,
            )
            # (lb): Not calling, self.wire_linked_list(section),
            # because separate lines.
            self.sections.append(section)

    def parts(self, prompt):
        if self._parts:
            return self._parts
        for idx, section in enumerate(self.sections):
            self._parts += section.render(idx)
            self._parts.append(('', '\n'))
        if self._parts:
            # Instead of a blank line between the banner and the prompt,
            # show a hint or whatever message is pertinent.
            _dont_want_last_newline = self._parts.pop()  # noqa: F841 local never used
            self._parts.extend(prompt.header_hint_parts())
        return self._parts

    # (lb): This is a <hack> for updating the banner inline (without me
    # resorting to learning PPT better and making our code use layouts
    # rather than a simple prompt). See: BannerBarArea::cycle_help.
    def render_one(self, idx):
        return self.sections[idx].render(idx)

