# -*- coding: utf-8 -*-

# This file is part of 'dob'.
#
# 'dob' is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 'dob' is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 'dob'.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, unicode_literals

from functools import update_wrapper

from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
# We override some basic bindings below to detect not standard event,
# like the user pressing backspace on an already empty text field,
# an event which PPT does not bother the validator with.
# - To see where get_by_name() calls are mimicked from, open:
#   python-prompt-toolkit/prompt_toolkit/key_binding/bindings/basic.py
from prompt_toolkit.key_binding.bindings.named_commands import get_by_name

from .interface_crown import BannerBarBuilder

__all__ = (
    'BannerBarArea',
)


class BannerBarArea(object):
    """
    """

    def __init__(self, prompter):
        self.prompter = prompter
        self.help_page_number = 0
        self.assemble_hints()

    def stand_up(self, key_bindings):
        self.wire_hooks(key_bindings)
        self.build_builder()

    def wire_hooks(self, key_bindings):
        """Hook backspace methods, for magic"""
        # Press 'Alt-h' to cycle through help lines.
        self.wire_hook_help(key_bindings)
        # Press ESCAPE or 'Ctrl-z' to hard-undo (all) edits
        # (restore initial Activity and Category prompt).
        self.wire_hook_ctrl_z(key_bindings)
        self.wire_hook_escape(key_bindings)
        # Press Backspace, Ctrl-w, Ctrl-Backspace, to delete a
        # single character, a single character, or the whole
        # Activity or Category (but not both), respectively.
        self.wire_hook_backspace(key_bindings)
        self.wire_hook_ctrl_w(key_bindings)
        self.wire_hook_ctrl_l(key_bindings)
        # Use ENTER, Ctrl-s, Ctrl-space to save/lock/commit Activity or Category
        # (i.e., save Activity and prompt will move on to editing Category;
        # save Category, and prompt will complete).
        self.wire_hook_ctrl_s(key_bindings)
        self.wire_hook_ctrl_space(key_bindings)
        self.wire_hook_enter(key_bindings)
        # Hook TAB to honor suggestion ahead of completion, Weird PPT!
        self.wire_hook_tab(key_bindings)
        # Use Ctrl-q for ...
        self.wire_hook_ctrl_q(key_bindings)

    def wire_hook_help(self, key_bindings):
        # HEH!/2019-11-23: (lb): The old code stopped working, not sure
        # when because I was away from dob for half the year and away
        # from the Awesome Prompt for the year prior because building
        # the Carousel. Life story short, for the record, here's old code:
        #
        #   keycode = ('escape', 'h')
        #
        # which is weird because PPT library is the dob fork, so pinned.
        # Or maybe the 'escape' is a Vim mode thing? Though I tried ESC, m.
        # In any case, the following code is what does work. At least for now.
        # And note that a simple 'm-h' does not work; stick with tuple.
        keycode = ('m-h',)

        def handler(event):
            self.cycle_help(event)
        key_bindings.add(*keycode)(handler)

    # ***

    class Decorators(object):
        # This is a little layered: Use the basic binding name to create
        # the decorator, which executes the basic binding after running
        # our middleware method.
        @classmethod
        def bubble_basic_binding(cls, named_command):
            # cls is Decorators
            def _bubble_basic_decorator(func, *args, **kwargs):
                def _bubble_basic_binding(event, *args, **kwargs):
                    handled = func(event, *args, **kwargs)
                    if not handled:
                        basic_binding = get_by_name(named_command)
                        basic_binding(event)
                return update_wrapper(_bubble_basic_binding, func)
            return _bubble_basic_decorator

    def wire_hook_ctrl_z(self, key_bindings):
        keycode = ('c-z',)

        # (lb): A purist might suggest that a Ctrl-z literally be echoed,
        # but I think frantic persons will appreciate an obvious recovery
        # mechanism.
        def handler(event):
            self.prompter.handle_content_reset(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_escape(self, key_bindings):
        keycode = ('escape',)

        def handler(event):
            self.prompter.handle_escape_dismiss(event)
        key_bindings.add(*keycode)(handler)

    # Wire all three related Backspace bindings: Backspace, Ctrl-Backspace, Ctrl-h.
    def wire_hook_backspace(self, key_bindings):
        # Note that POSIX reports Ctrl-Backspace as '\x08', just like Ctrl-h.
        # And a lone Backspace is '\x7f', but PPT says key 'c-h', like C-BS and C-h.
        keycode = ('c-h',)  # Aka ('backspace',)

        def handler(event):
            # Backspace (aka rubout) is ASCII 127/DEL. Ctrl-Backspace and C-h are 8.
            # (lb): I think it's a terminal issue, and not something we can change.
            # - Backspace: KeyPress(key='c-h', data='\x7f')
            # - C-BS, C-h: KeyPress(key='c-h', data='\x08')
            if event.data == '\x7f':
                # Backspace
                handled = self.prompter.handle_backspace_delete_char(event)
                # Kick basic binding.
                decor = BannerBarArea.Decorators.bubble_basic_binding('backward-delete-char')
                decor(lambda event: handled)(event)
            elif event.data == '\x08':
                # MAYBE: (lb): Would there ever be a case where someone absolutely
                # must use Ctrl-h to delete single characters? If not, I'd like to
                # make use Ctrl-Backspace/Ctrl-h for delete all, because I never
                # use Ctrl-h, and because I want a way to clear the whole input
                # like.
                # Skip basic binding.
                self.prompter.handle_backspace_delete_more(event)
            else:
                self.prompter.controller.affirm(False)

        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_w(self, key_bindings):
        keycode = ('c-w',)

        @BannerBarArea.Decorators.bubble_basic_binding('unix-word-rubout')
        def handler(event):
            return self.prompter.handle_word_rubout(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_l(self, key_bindings):
        keycode = ('c-l',)

        # The basic binding clears the screen, including our banner!
        # - So override to just clear the input line.
        # SKIP:
        #   @BannerBarArea.Decorators.bubble_basic_binding('clear-screen')
        def handler(event):
            self.prompter.handle_clear_screen(event)
        key_bindings.add(*keycode)(handler)

    # SKIP: ('delete',), ('c-delete',), and ('c-d',).
    # - Both call 'delete-char' basic binding, which deletes next character,
    # and is not interesting to us.

    def wire_hook_ctrl_s(self, key_bindings):
        keycode = ('c-s',)

        # The basic binding performs same action in emacs or vi mode,
        # search.start_forward_incremental_search, but that feature
        # seems not as useful as provider left-handed (per QWERTY)
        # method to save (to complement right-handed ENTER option).
        @BannerBarArea.Decorators.bubble_basic_binding('accept-line')
        def handler(event):
            return self.prompter.handle_accept_line(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_space(self, key_bindings):
        keycode = ('c-space',)

        # (lb): Redundant? Both Ctrl-space and Ctrl-s are left-hand
        # accessible. Do we really need 2 left-hand accessible ENTERs?
        @BannerBarArea.Decorators.bubble_basic_binding('accept-line')
        def handler(event):
            return self.prompter.handle_accept_line(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_enter(self, key_bindings):
        keycode = ('enter',)

        # The basic PPT 'enter' calls 'accept-line', which is mostly
        # already wired in our code to be what we want, except we use
        # a Validator gatekeeper that likes to raise ValidationError
        # hints. So we need to handle this situation ourselves, to get
        # around the validator.
        @BannerBarArea.Decorators.bubble_basic_binding('accept-line')
        def handler(event):
            return self.prompter.handle_accept_line(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_tab(self, key_bindings):
        keycode = ('c-i',)  # Aka 'tab'.

        # (lb): First, I had considered hooking 'tab' (and calling the
        # 'menu-complete' basic binding if necessary) but I sometimes
        # double-TAB so triggering ENTER on second TAB could be AWKWARD.
        #
        # (lb): Second, on TAB, PPT uses the next item in the completion
        # list, and *not* the actual suggestion that appears in the input!
        # Which might be something I'm doing wrong, i.e., I haven't wired
        # the PPT controls in dob correctly. But it also might not be my
        # fault. In whatever case, we can at least take ownership here:
        # - Intercept TAB and prefer using suggestion, not first completion.
        # - E.g., for me, typing "Po" suggests "ol Time" in gray after the
        # cursor, but in the completions dropdown below the prompt, the first
        # entry is "Appointments". Hitting TAB, PPT defaults to completing
        # with "Appointments" and not "Pool Time", like one would expect!
        @BannerBarArea.Decorators.bubble_basic_binding('menu-complete')
        def handler(event):
            return self.prompter.handle_menu_complete(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_q(self, key_bindings):
        keycode = ('c-q',)

        def handler(event):
            self.prompter.controller.client_logger.debug('FIXME: c-q')
        key_bindings.add(*keycode)(handler)

    # ***

    def build_builder(self, term_width=0):
        stretch_width = self.prompter.bottombar.builder.first_line_len
        self.builder = BannerBarBuilder(
            colors=self.prompter.colors,
            term_width=term_width,
        )
        self.content = (
            self.prompter.bannerbar_title,
            self.prompter.type_request,
            self.help_section_text,
        )
        self.help_section_idx = 2
        self.builder.add_content(*self.content, width=stretch_width)

    @property
    def completion_hints(self):
        return [
            'Press <Alt-h> for help.',
        ]

    def assemble_hints(self):
        self.help_pages = (
            self.completion_hints
            + self.prompter.completion_hints
            + ['']  # Cycle through to blank line.
        )

    def help_section_text(self):
        help_text = self.help_pages[self.help_page_number].format(
            part_type=self.prompter.edit_part_type,
        )
        return help_text

    def cycle_help(self, event):
        self.help_page_number = (self.help_page_number + 1) % len(self.help_pages)

        # (lb): This is a hack to overwrite the banner, which is not part
        # of the PPT app -- we wrote the banner first, before starting the
        # prompt. (I could learn PPT layouts and rewrite our code to manage
        # the banner from within the PPT app context... but I won't; not now.)
        restore_column = event.app.current_buffer.cursor_position
        # The cursor position is relative to the PPT buffer which starts
        # after the prefix we told the prompt to draw.
        restore_column += len(self.prompter.session_prompt_prefix)

        # The hack gets hackier: Add one for the '@' if BeforeInput set.
        if self.prompter.lock_act:
            restore_column += len(self.prompter.activity)
            restore_column += len(self.prompter.sep)

        # The help row is this many rows above the prompt: As many rows as
        # the banner, minus the row that the help is on, plus one row for
        # the blank line between the banner and the prompt.
        relative_help_row = 1 + (len(self.content) - self.help_section_idx)
        # "Up, up, up, up, up, up raises
        #  The stakes of the game."
        event.app.renderer.output.cursor_up(relative_help_row)
        event.app.renderer.output.cursor_backward(restore_column)
        # Hack-within-a-hack. Ask our banner builder to build us just the
        # row in question, and tell PPT to dump it where the cursor's at.
        print_formatted_text(FormattedText(
            self.builder.render_one(self.help_section_idx)
        ))
        # Finally, restore the cursor. The print added a newline, so
        # the row is down one less than we moved up.
        relative_prompt_row = relative_help_row - 1
        event.app.renderer.output.cursor_down(relative_prompt_row)
        event.app.renderer.output.cursor_forward(restore_column)

