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

    def __init__(self, prompt):
        self.prompt = prompt
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
        # Make LEFT and RIGHT transition Activity ↔ Category input state.
        self.wire_hook_left(key_bindings)
        self.wire_hook_right(key_bindings)
        # In lieu of hooking Ctrl-c ('c-c') to prevent prompt from exiting,
        # the prompt runner catches KeyboardInterrupt. Either way is
        # appropriate, but the side effect of catching KeyboardInterrupt
        # is that the cursor jumps to the right side of the input, because
        # the prompt is actually restarted. (In the least, this offers a
        # novel way of re-running session.prompt() -- just send Ctrl-c.)
        #  N/A: self.wire_hook_ctrl_c(key_bindings)
        # Use Ctrl-q for exiting. Make it take two if edits, Tap tap exit.
        self.wire_hook_ctrl_q(key_bindings)

    def wire_hook_help(self, key_bindings):
        # Note that Alt-bindings are wired by their 2-key escape equivalents.
        # - So ('escape', 'h') might be thought of as ('m-h').
        # MAYBE/2020-04-10: (lb): Alt-h is awkward to press. I like Ctrl-\.
        #                           keycode = ('c-\\',)
        #                         But I'll worry about that when I revisit
        #                         mappings more generally. (There might be
        #                         a better use for Ctrl-\, or perhaps we'll
        #                         make key codes user-configurable.)
        keycode = ('escape', 'h')

        def handler(event):
            self.cycle_help(event)
        key_bindings.add(*keycode)(handler)

    # ***

    class Decorators(object):
        # This is a little layered: Use the basic binding name to create
        # the decorator, which executes the basic binding after running
        # our middleware method.
        @classmethod
        def bubble_binding(cls, named_command):
            # cls is Decorators
            def _bubble_basic_decorator(func, *args, **kwargs):
                def _bubble_binding(event, *args, **kwargs):
                    handled = func(event, *args, **kwargs)
                    if not handled:
                        basic_binding = get_by_name(named_command)
                        basic_binding.call(event)
                    return handled
                return update_wrapper(_bubble_binding, func)
            return _bubble_basic_decorator

        @classmethod
        def reset_timeouts(cls, prompt):
            # cls is Decorators
            def _reset_timeouts_decorator(func, *args, **kwargs):
                def _reset_timeouts_binding(event, *args, **kwargs):
                    prompt.debug('_reset_timeouts_binding')
                    prompt.reset_timeouts()
                    handled = func(event, *args, **kwargs)
                    prompt.debug('_reset_timeouts_binding/handled: {}'.format(handled))
                    return handled
                return update_wrapper(_reset_timeouts_binding, func)
            return _reset_timeouts_decorator

    def wire_hook_ctrl_z(self, key_bindings):
        keycode = ('c-z',)

        # (lb): A purist might suggest that a Ctrl-z literally be echoed,
        # but I think frantic persons will appreciate an obvious recovery
        # mechanism.
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            self.prompt.handle_content_reset(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_escape(self, key_bindings):
        # (lb): There's a lag after user presses Escape, because underlying
        # 2-character emacs escape-combo bindings. Surprisingly, hooking two
        # Escape presses did not solve it, e.g., keycode = ('escape', 'escape',).
        # - But if user presses *three* Escapes in a row, then this is called
        #   before the timeout.
        keycode = ('escape',)

        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            self.prompt.handle_escape_dismiss(event)
        key_bindings.add(*keycode)(handler)

    # Wire all three related Backspace bindings: Backspace, Ctrl-Backspace, Ctrl-h.
    def wire_hook_backspace(self, key_bindings):
        # Note that POSIX reports Ctrl-Backspace as '\x08', just like Ctrl-h.
        # And a lone Backspace is '\x7f', but PPT says key 'c-h', like C-BS and C-h.
        keycode = ('c-h',)  # Aka ('backspace',)

        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            # Backspace (aka rubout) is ASCII 127/DEL. Ctrl-Backspace and C-h are 8.
            # (lb): I think it's a terminal issue, and not something we can change.
            # - Backspace: KeyPress(key='c-h', data='\x7f')
            # - C-BS, C-h: KeyPress(key='c-h', data='\x08')
            if event.data == '\x7f':
                # Backspace
                handled = self.prompt.handle_backspace_delete_char(event)
                # Kick basic binding.
                decor = BannerBarArea.Decorators.bubble_binding('backward-delete-char')
                decor(lambda event: handled)(event)
            elif event.data == '\x08':
                # MAYBE: (lb): Would there ever be a case where someone absolutely
                # must use Ctrl-h to delete single characters? If not, I'd like to
                # make use Ctrl-Backspace/Ctrl-h for delete all, because I never
                # use Ctrl-h, and because I want a way to clear the whole input
                # like.
                # Skip basic binding.
                self.prompt.handle_backspace_delete_more(event)
            else:
                self.prompt.controller.affirm(False)

        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_w(self, key_bindings):
        keycode = ('c-w',)

        @BannerBarArea.Decorators.bubble_binding('unix-word-rubout')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_word_rubout(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_l(self, key_bindings):
        keycode = ('c-l',)

        # The basic binding clears the screen, including our banner!
        # - So override to just clear the input line.
        # SKIP:
        #   @BannerBarArea.Decorators.bubble_binding('clear-screen')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            self.prompt.handle_clear_screen(event)
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
        @BannerBarArea.Decorators.bubble_binding('accept-line')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_accept_line(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_space(self, key_bindings):
        keycode = ('c-space',)

        # (lb): Redundant? Both Ctrl-space and Ctrl-s are left-hand
        # accessible. Do we really need 2 left-hand accessible ENTERs?
        @BannerBarArea.Decorators.bubble_binding('accept-line')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_accept_line(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_enter(self, key_bindings):
        keycode = ('enter',)

        # The basic PPT 'enter' calls 'accept-line', which is mostly
        # already wired in our code to be what we want, except we use
        # a Validator gatekeeper that likes to raise ValidationError
        # hints. So we need to handle this situation ourselves, to get
        # around the validator.
        @BannerBarArea.Decorators.bubble_binding('accept-line')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_accept_line(event)
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
        @BannerBarArea.Decorators.bubble_binding('menu-complete')
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_menu_complete(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_left(self, key_bindings):
        keycode = ('left',)

        @BannerBarArea.Decorators.bubble_binding('backward-char')
        # Note that when the completion dropdown is showing, this handler
        # does not fire at all, so we use a Validator as a hacky way to
        # be sure to call reset_timeouts (because as the user left/right/
        # up/down arrows around the completion dropdown, each selected
        # entry is sent to the validator, which then calls reset_timeouts).
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_backward_char(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_right(self, key_bindings):
        keycode = ('right',)

        @BannerBarArea.Decorators.bubble_binding('forward-char')
        # See commend in wire_hook_left: 'right' not triggered when completions
        # dropdown showing, so separate wiring in place to call reset_timeouts
        # when the 'right' event is masked from us.
        @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        def handler(event):
            return self.prompt.handle_forward_char(event)
        key_bindings.add(*keycode)(handler)

    def wire_hook_ctrl_q(self, key_bindings):
        keycode = ('c-q',)

        # NO: @BannerBarArea.Decorators.reset_timeouts(self.prompt)
        # (Do not wrap with reset_timeouts because handle_exit_request
        # might set one of those timeouts, which we wouldn't want reset.)
        def handler(event):
            return self.prompt.handle_exit_request(event)
        key_bindings.add(*keycode)(handler)

    # ***

    def build_builder(self, term_width=0):
        stretch_width = self.prompt.bottombar.builder.first_line_len
        self.builder = BannerBarBuilder(
            colors=self.prompt.colors,
            term_width=term_width,
        )
        self.content = (
            self.prompt.bannerbar_title,
            self.prompt.type_request,
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
            + self.prompt.completion_hints
            + ['']  # Cycle through to blank line.
        )

    def help_section_text(self):
        help_text = self.help_pages[self.help_page_number].format(
            part_type=self.prompt.edit_part_type,
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
        restore_column += len(self.prompt.session_prompt_prefix)

        # The hack gets hackier: Add one for the '@' if BeforeInput set.
        if self.prompt.lock_act:
            restore_column += len(self.prompt.activity)
            restore_column += len(self.prompt.sep)

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

