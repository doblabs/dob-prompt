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

import time
from collections import namedtuple
from gettext import gettext as _

from dob_bright.helpers.path import touch
from easy_as_pypi_appdirs import AppDirs
from easy_as_pypi_appdirs.expand_and_mkdirs import must_ensure_appdirs_path
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import CompleteStyle

from .. import __package_name__
from .prompter_common import PrompterCommon
from .the_banner_area import BannerBarArea

__all__ = (
    "SophisticatedPrompt",
    # Private:
    #  'HamsterPartAutoSuggest',
)


class HamsterPartAutoSuggest(AutoSuggest):
    """ """

    def __init__(self, completer):
        self.completer = completer

    def get_suggestion(self, buffer, document):
        return self.completer.get_suggestion(buffer, document)


class SophisticatedPrompt(PrompterCommon):
    """ """

    DIRTY_QUITER_THRESHOLD = 1.667

    SESSION_PROMPT_REFRESH_INTERVAL = 0.5

    def __init__(self, controller):
        self.controller = controller
        self.history = self.init_history()
        self.completer = self.init_completer()
        self.processor = self.init_processor()
        self.bannerbar = self.init_bannerbar()
        self.bottombar = self.init_bottombar()
        self.key_bindings = None
        self.session = None
        self.sort_order = None
        self.showing_completions = None
        # A little hack for cycle_hack: a derived class attribute.
        # Ideally, we should not have this here, but easier, why not.
        self.lock_act = False

        self.ctrl_c_pressed = None
        self.ctrl_q_pressed = None
        self.update_pending = False

        self._debug = self.controller.client_logger.debug

    # ***

    @property
    def bannerbar_title(self):
        return __package_name__

    @property
    def colors(self):
        raise NotImplementedError

    @property
    def edit_part_type(self):
        raise NotImplementedError

    @property
    def edit_part_text(self):
        raise NotImplementedError

    @property
    def history_topic(self):
        raise NotImplementedError

    @property
    def type_request(self):
        raise NotImplementedError

    # ***

    def init_history(self):
        file_path = self.history_path
        if file_path:
            # Make sure it exists, else "No such file or directory".
            touch(file_path)
            history = FileHistory(file_path)
        else:
            history = InMemoryHistory()
        return history

    def init_completer(self):
        raise NotImplementedError

    def init_processor(self):
        raise NotImplementedError

    def init_bannerbar(self):
        return BannerBarArea(self)

    def init_bottombar(self):
        raise NotImplementedError

    # ***

    @property
    def complete_while_typing(self):
        return self.bottombar.complete_while_typing

    @property
    def enable_history_search(self):
        return self.bottombar.enable_history_search

    @property
    def active_sort(self):
        return self.bottombar.active_sort

    @active_sort.setter
    def active_sort(self, value):
        self.bottombar.active_sort = value

    @property
    def default_sort(self):
        return self.bottombar.default_sort

    @property
    def sorting_by_history(self):
        return self.bottombar.sorting_by_history

    # ***

    def prepare_session(self):
        # Get the terminal size measure function.
        self.get_size = self.prompt_session.app.renderer.output.get_size

        self.stand_up_banner_and_bottom()

        # If caller is interrogating for more than one Fact, remember
        # the settings from the previous run (use self.active_sort).
        binding = self.active_sort or self.default_sort

        self.session = None
        self.showing_completions = False

        self.reset_completer(binding)

        self.session = self.prompt_session

        self.print_text_header()

    # ***

    @property
    def bottom_toolbar(self):
        return self.bottombar.builder.parts(self)

    def bottom_toolbar_reset(self):
        self.bottombar.builder.clear()
        self.session.bottom_toolbar = self.bottom_toolbar

    # ***

    def stand_up_banner_and_bottom(self):
        self.key_bindings = KeyBindings()
        # (lb): 2019-11-23: Just noticed reverse ordered here, not sure if matters
        # if bottombar stood_up first, or bannerbar, or if It Just Doesn't Matter.
        self.bottombar.stand_up(self.key_bindings)
        self.bannerbar.stand_up(self.key_bindings)

    # ***

    def reset_completer(self, binding=None, toggle_ok=False):
        self.bannerbar.builder.clear()
        self.bottombar.builder.clear()

        self.ensure_active(binding, toggle_ok)

        # Refresh the bottom toolbar.
        if self.session is not None:
            self.session.bottom_toolbar = self.bottom_toolbar

        # Refresh, well, duh, the completions.
        # (lb): We do this now, on startup, rather than lazy-loading later,
        # because we want to make suggestions as the user types. So we need
        # results now.
        self.refresh_completions()

    def ensure_active(self, binding=None, toggle_ok=False):
        if self.active_sort is None:
            self.sort_order = "desc"

        if binding is not None:
            if self.active_sort == binding:
                if toggle_ok:
                    if self.sort_order != binding.sort_order:
                        # Toggle: sort_order, !sort_order, hide-completions
                        # FIXME: (lb): I'm not sold on this behavior. Make cfgable?
                        self.showing_completions = False
                    self.sort_order = "asc" if self.sort_order == "desc" else "desc"
            else:
                self.active_sort = binding
                self.sort_order = binding.sort_order

    # ***

    FakeUsageResult = namedtuple("FakeUsageResult", ("name", "usage", "span"))

    FakeUsageWrapper = namedtuple("FakeUsageWrapper", ("item", "uses", "span"))

    def refresh_completions(self):
        results = self.fetch_completions()
        self.hydrate_completer(results)

    def fetch_completions(self):
        if self.sorting_by_history:
            results = self.refresh_completions_history()
        else:
            results = self.refresh_completions_fact_part()
            # The get_all() specified raw=True, which converts the result object,
            #   <class 'sqlalchemy.util._collections.result'>
            # into an (Item, *cols) tuple (where Item is Activity or Category,
            # and *cols is the 'uses' and 'span' columns). We use raw=True because
            # the result object is attribute-addressable, e.g., `results[0].uses`
            # works. If we specified raw=False instead, we'd want to convert the
            # tuple to a namedtuple, e.g.,
            #   results = [SophisticatedPrompt.FakeUsageWrapper(*it) for it in results]
        return results

    @property
    def no_completion(self):
        raise NotImplementedError

    def hydrate_completer(self, results):
        self.completer.hydrate(results, no_completion=self.no_completion)

    def refresh_completions_history(self):
        results = []
        names = set()
        # FIXME: (lb): Does this make any sense?
        for entry in list(self.history.load_history_strings()):
            entry_name = self.history_entry_name(entry)
            if entry_name is None or entry_name in names:
                continue
            names.add(entry_name)
            result = SophisticatedPrompt.FakeUsageResult(entry_name, None, None)
            results.append(SophisticatedPrompt.FakeUsageWrapper(result, None, None))
        if self.sort_order == "asc":
            results.reverse()
        return results

    def history_entry_name(self, entry):
        return entry

    # ***

    def print_text_header(self):
        term_width = self.get_size()[1]
        self.bannerbar.build_builder(term_width)
        parts = self.bannerbar.builder.parts(self)
        # (lb): Note that we just print the banner to the terminal and
        # forget about it, i.e., this text is not managed by the PPT.
        # (We do, however, edit the help text line if the user cycles
        # through the help pages, but we just hack the cursor with
        # carnal knowledge of the screen, rather than calling the builder
        # to regenerate its parts.) So the builder gets used once, here,
        # on startup, and later we just redraw the help line as needed.
        print_formatted_text(FormattedText(parts))

    @property
    def completion_hints(self):
        return [
            _("Press TAB to show a list of {part_type} suggestions."),
            _(
                "Use ARROW keys to navigate list of suggestions,"
                " and ENTER to choose one."
            ),
            _("As you type, the best match is shown. Use RIGHT → ARROW to accept it."),
            _("Press UP ↑ ARROW to cycle through previous values you have entered."),
            _("Use F-keys to change how the list of suggestions is sorted."),
            _(
                "You can also use your favorite Readline keys."
                " E.g., Ctrl-u deletes to start of line."
            ),
        ]

    @property
    def completion_hints_count(self):
        return len(self._completion_hints)

    def completion_hints_page(self, page):
        return self.completion_hints[page]

    # ***

    def clean_up_print_text_header(self):
        """
        Clear the banner manually, which was dumped to the terminal
        before the prompt ran, so erase_when_done did not clean it.
        """
        up_count = len(self.bannerbar.builder.sections) + 1
        self.session.app.renderer.output.cursor_up(up_count)
        # (lb): Without flush(), erase_down() erases from old position.
        self.session.app.renderer.output.flush()
        self.session.app.renderer.output.erase_down()
        self.session.app.renderer.output.flush()

    # ***

    @property
    def prompt_session(self):
        session = PromptSession(
            erase_when_done=True,
            history=self.history,
            enable_history_search=self.enable_history_search,
            auto_suggest=HamsterPartAutoSuggest(self.completer),
            # (lb): There are pros and cons to setting vi_mode.
            # - vi_mode pros: Reacting to single 'escape' keypress is faster!
            #   This is because PPT's default mode, emacs, wires a bunch of
            #   two-key 'escape' bindings (you know emacs!). As such, PPT has
            #   to wait a hot mo. after the user presses the escape key to see
            #   if the user presses another key that then makes a match against
            #   one of the registered two-key escape-key bindings.
            # - vi_mode mehs: The time between pressing 'escape' and the
            #   callback being invoked is a little faster with vi_mode than
            #   without (emacs). However, you can still sense a little delay
            #   with vi_mode that you do not sense with, say, a Ctrl-key combo,
            #   where the time between keypress and reaction feels immediate.
            # - vi_mode cons: It's missing some nice bindings, Ctrl-a, Ctrl-e, etc.
            # MAYBE/2019-11-25: Use no mode, but specify all the bindings
            #   explicitly that you want for the perfect User Xperience.
            # SKIP:
            #   vi_mode=True,
        )
        return session

    @property
    def session_prompt_prefix(self):
        return "> "

    # This is the blocking (not asyncio) PPT prompt call that runs the
    # act@gory and tags inputs. All the dob user interface interaction
    # is handled through callback'ish objects, like the validator, the
    # completer, and the input processor.
    def session_prompt(self, **kwargs):
        try:
            return self._session_prompt(**kwargs)
        except (EOFError, KeyboardInterrupt):
            # The PTK prompt() shortcut hooks and raises on Ctrl-D, but the
            # "Ctrl-D binding is only active when the default buffer is
            # selected and empty." This behavior is baked in, and EOD means
            # end-of-data, so it's like user cleared text and pressed Enter.
            return ""

    def _session_prompt(self, default="", validator=None):
        validate_while_typing = validator is not None
        text = self.session.prompt(
            self.session_prompt_prefix,
            # The initial input control text.
            default=default,
            # (lb): The super special bottom toolbar. Its state depends on the
            # state of the prompt. If I were to rebuild the Awesome Prompt, I'd
            # use PPT components (like the interactive editor uses) and not the
            # shortcut session.prompt, so that we could refresh individual parts
            # of the bottom toolbar; but specified as the bottom_toolbar of a
            # prompt, it instead is drawn as a sequence of lines each time. Not
            # a big deal, just not as elegant as it could be. (Also, we have to
            # explicitly nudge the bottom_toolbar to update it; the PPT prompt
            # doesn't otherwise do anything with it other than draw it once.)
            bottom_toolbar=self.bottom_toolbar,
            # 2020-01-28: The following comment was writ circa PPTv2 (PTK2) era.
            #             PTK3 is always-async.
            # (lb): When I added burnout messages that hide on their own
            # if the user doesn't trigger them to hide earlier (like the
            # Press-Ctrl-q-Twice-to-Quit-and-Discard-Changes message), I
            # briefly tried to use asyncio to wire timers. E.g.,
            #     refresh_interval=None,
            #     async_=True,
            # with an `await self.session_prompt()` and the whole shebang
            # (using an example at p-p-t/examples/prompts/asyncio-prompt.py),
            # but I ran into issues pretty much immediately. And I gave up
            # on asyncio immediately, too -- I know that I wired the interactive
            # editor (carousel.py) with asyncio when I built it, and even then
            # it was tricky. So I'd assume trying to jam asyncio into Awesome
            # Prompt well into its mature years is probably not a good use of
            # anyone's time. - So here we enable refresh_interval, which will
            # cause the apply_transformation method of Processor objects to
            # get tickled periodically (and which we can use to implement
            # crude "timers").
            refresh_interval=self.SESSION_PROMPT_REFRESH_INTERVAL,
            # Completer wiring. See, e.g., ActegoryCompleterSuggester.
            completer=self.completer,
            complete_in_thread=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
            complete_while_typing=self.complete_while_typing,
            # Processor wiring. See, e.g., ActegoryHackyProcessor.
            input_processors=[
                self.processor,
            ],
            # KeyBinding wiring.
            key_bindings=self.key_bindings,
            # Style: Twiddle to extend bg colors the full terminal width.
            style=self.bottombar.prompt_style,
            # Validator wiring, e.g., ActegoryValidator.
            validate_while_typing=validate_while_typing,
            validator=validator,
        )
        return text

    # ***

    def summoned(self, showing_completions):
        alert_changed = False
        if self.showing_completions != showing_completions:
            alert_changed = True
        self.showing_completions = showing_completions
        if alert_changed:
            self.completions_changed()

    def completions_changed(self):
        # Refresh the bottom toolbar, whose state reflects state of completions.
        self.bottombar.builder.clear()
        self.session.bottom_toolbar = self.bottom_toolbar

    # ***

    @property
    def changed_since_init(self):
        raise NotImplementedError

    def handle_exit_request(self, event):
        """Awesome Prompt Ctrl-q handler."""
        if self.approve_exit_request():
            self.ctrl_q_pressed = None
            event.app.exit()

    def approve_exit_request(self):
        latest_press = time.time()
        exitable = self.verify_second_exit_request(latest_press)
        self.ctrl_q_pressed = latest_press
        exitable = self.allow_exit_if_unchanged_else_hint(exitable)
        return exitable

    def allow_exit_if_unchanged_else_hint(self, exitable):
        if exitable:
            return exitable

        if not self.changed_since_init:
            # Just one Ctrl-q received, but no input changes, so okay to exit.
            exitable = True
        else:
            # Just one Ctrl-q, but input changed, so tell user to be forcefuller.
            # Super will have set self.ctrl_q_pressed to now time.
            self.update_input_hint_renderer()
        return exitable

    def verify_second_exit_request(self, latest_press):
        if self.ctrl_q_pressed is None:
            return False
        if (latest_press - self.ctrl_q_pressed) < self.DIRTY_QUITER_THRESHOLD:
            return True
        return False

    # ***

    def restart_completer(self, event=None, binding=None, toggle_ok=False):
        # (lb): Just curious: We do not really need 'event', do we?
        self.controller.affirm(
            self.session.app.current_buffer is self.session.layout.current_buffer
        )
        if event is not None:
            self.controller.affirm(
                self.session.app.current_buffer is event.app.current_buffer
            )
            inputbuf = event.app.current_buffer
        else:
            # Also at: self.session.layout.current_buffer
            inputbuf = self.session.app.current_buffer

        # (lb): Docs indicate set_completions is part of buffer, but not so:
        #   NOPE: event.app.current_buffer.set_completions(completions=...)
        # Docs also say start_completion part of CLI object, but it's in buffer?
        #  In any case, cancel the current completion, and start a new one.
        self.showing_completions = True

        if inputbuf.complete_state:
            inputbuf.cancel_completion()
        else:
            # Only happens first time user presses F-key,
            #  if they haven't already pressed <TAB>.
            toggle_ok = False
        self.reset_completer(binding=binding, toggle_ok=toggle_ok)
        if self.showing_completions:
            inputbuf.start_completion()

    # ***

    def debug(self, *args, **kwargs):
        # MAYBE/2019-11-26: (lb): Remove debug() code. Useful for now.
        # (It just clutters the code a bit, and your log, no biggie.)
        if not self._debug:
            return
        self._debug(*args, **kwargs)

    # ***

    DEFAULT_HIST_PATH_DIR = "history"

    @property
    def history_path(self):
        """
        Return the path to the history file for a specific topic.

        Args:
            topic (str): Topic name, to distinguish different histories.

        Returns:
            str: Fully qualified path to history file for specified topic.
        """
        hist_path = self.must_ensure_appdirs_path(
            file_basename=self.history_topic,
            dir_dirname=SophisticatedPrompt.DEFAULT_HIST_PATH_DIR,
            appdirs_dir=AppDirs().user_cache_dir,
        )
        return hist_path

    def must_ensure_appdirs_path(self, **kwargs):
        try:
            _hist_path = must_ensure_appdirs_path(**kwargs)  # noqa: F841
        except Exception as err:
            self.update_pending = str(err)

    # ***

    @property
    def prompt_header_hint(self):
        if self.ctrl_c_pressed:
            # Ctrl-c is blocked in the interactive editor Carousel so here as well.
            # - Well, sorta blocked. It'll clear the input and reset the completer!
            #   (By reset the completer, it goes back to, e.g., F2/sort-by-name.)
            hint = _("Try Ctrl-q if you want to quit!").format()
            # (lb): 2020-04-10: Trying this, too: reset completer state.
            binding = self.default_sort
            self.reset_completer(binding)
        elif self.ctrl_q_pressed:
            hint = _("Press Ctrl-q a second time to really quit!").format()
        elif self.update_pending and isinstance(self.update_pending, str):
            hint = self.update_pending
        else:
            hint = ""
        return hint

    def header_hint_parts(self, max_col=0):
        prefix = "  "
        what_hint = self.prompt_header_hint
        # BEWARE/2019-11-23: This is not ANSI-aware.
        colfill = max_col - len(what_hint)

        if max_col > 0 and colfill < 0:
            # (lb): 2019-11-23: Assuming this'll work... coverage prove it?
            what_hint = what_hint[:max_col]

        line_parts = []
        line_parts.append(("", prefix))
        line_parts.append(("italic underline", what_hint))
        if max_col > 0 and colfill > 0:
            line_parts.append(("", " " * colfill))

        self.debug("line_parts: {}".format(line_parts))

        return line_parts

    def update_input_hint(self, event):
        self.update_input_hint_renderer(event.app.renderer)

    # (lb): HACK!
    def update_input_hint_renderer(self, renderer=None):
        if renderer is None:
            renderer = self.session.app.renderer
        # - Note either event.app.current_buffer or event.current_buffer seem to work.
        # - The rendered cursor position should be same as if we calculated:
        #     restore_column = event.app.current_buffer.cursor_position
        #     restore_column += len(self.session_prompt_prefix)
        #     if was_lock_at:
        #         restore_column += len(self.activity)
        #         restore_column += len(self.sep)
        #     affirm(restore_column == event.app.renderer._cursor_pos.x)
        #   but less fragile/obtuse.
        cursor_x = renderer._cursor_pos.x
        #  self.debug('UIHR: cursor_x: {}'.format(cursor_x))

        relative_help_row = 1
        renderer.output.cursor_up(relative_help_row)
        renderer.output.cursor_backward(cursor_x)

        columns = renderer.output.get_size().columns
        max_col = columns - 2

        hint_parts = self.header_hint_parts(max_col)
        print_formatted_text(FormattedText(hint_parts))

        prompt_parts = self.prompt_recreate_filled(max_col)
        print_formatted_text(FormattedText(prompt_parts), end="")

        # (lb): "Inconceivable." Correct the cursor position: move the
        # cursor to the end of the recreated text ("where it belongs").
        # - I think that renderer._cursor_pos remains unchanged,
        # but in reality the cursor moved (because print_formatted_text),
        # so here we're moving it back to where PPT expects it to be. Or
        # something.
        fake_prompt = prompt_parts[0][1]
        # BEWARE: The len() is not ANSI-aware. So keep a clean prompt!
        cursor_adjust = len(fake_prompt) - cursor_x
        #  self.debug('UIHR: cursor_adjust/1: {}'.format(cursor_adjust))
        renderer.output.cursor_backward(cursor_adjust)

        self.debug("printed hint")

    # ***

    def heartbeat(self):
        if self.update_pending:
            self.update_input_hint_renderer()
            self.update_pending = False
        # We passed a refresh_interval to session.prompt(), which invalidates and
        # redraws the screen periodically, which triggers apply_transformation(),
        # which calls this heartbeat method. It's a roundabout, naive, non-event
        # driven, say, poll-driven, timer implementation.
        now = time.time()
        self.heartbeart_ctrl_c(now)
        self.heartbeart_ctrl_q(now)

    def heartbeart_ctrl_c(self, now):
        if self.ctrl_c_pressed is None:
            return
        if (now - self.ctrl_c_pressed) <= self.DIRTY_QUITER_THRESHOLD:
            return
        self.debug("reset Ctrl-c timeout")
        self.ctrl_c_forget()

    def ctrl_c_forget(self):
        if self.ctrl_c_pressed is None:
            return
        self.ctrl_c_pressed = None
        self.update_input_hint_renderer()

    def heartbeart_ctrl_q(self, now):
        if self.ctrl_q_pressed is None:
            return
        if self.verify_second_exit_request(now):
            # Still in threshold because exit request approved, so bail.
            return
        # Window to press Ctrl-q twice closed without receiving second Ctrl-q,
        # so reset the hint.
        self.debug("reset Ctrl-q timeout")
        self.ctrl_q_forget()

    def ctrl_q_forget(self):
        if self.ctrl_q_pressed is None:
            return
        self.ctrl_q_pressed = None
        self.update_input_hint_renderer()

    def reset_timeouts(self):
        self.debug("reset_timeouts/1")
        self.ctrl_c_forget()
        self.ctrl_q_forget()
        self.debug("reset_timeouts!!!!!!!!!!!")

    # ***

    @property
    def sep(self):
        # A little derived class knowledge bleed. (SophisticatedPrompt should
        # not know about this value used by a derived class, PromptForActegory,
        # but not by the other derived class, PromptForMoreTags. But it makes
        # some magic easier to do this.)
        return ""

    # ***

    def handle_backspace_delete_char(self, event):
        """Awesome Prompt Backspace handler."""
        return False

    def handle_backspace_delete_more(self, event):
        """Awesome Prompt Ctrl-BS/Ctrl-h handler."""
        return False

    def handle_clear_screen(self, event):
        """Awesome Prompt Ctrl-l handler."""
        return False

    def handle_word_rubout(self, event):
        """Awesome Prompt Ctrl-w handler."""
        return False

    def handle_content_reset(self, event):
        """Awesome Prompt Dramatic Undo handler."""
        return False

    def handle_escape_dismiss(self, event):
        if self.showing_completions:
            # Hide completions on escape.
            self.session.layout.current_buffer.cancel_completion()
        else:
            # (lb): Experimental behavior: Reset input on escape if no dropdown.
            # Reset input instead of completions dropdown not visible.
            self.handle_content_reset(event)
        return True

    def handle_accept_line(self, event):
        """Awesome Prompt ENTER, etc., handler."""
        return False

    def handle_menu_complete(self, event):
        """Awesome Prompt TAB handler."""
        # PPT's tab complete using the first completion, not the suggestion.
        # Here we fix that.
        # - I.e., if the completion dropdown is open, but you see a suggestion
        # in the input and press TAB thinking that'll finish the suggestion in
        # the input text, you'd be wrong, and the first completion would get
        # selected and also set to the input field.
        # - You can use Ctrl-right arrow to accept the suggestion.
        # But using Ctrl-right arrow is not very intuitive.
        # Whereas using TAB seems legit.

        suggestion = event.current_buffer.suggestion
        if suggestion and suggestion.text:
            # Pretty much exactly what load_auto_suggest_bindings does.
            cb = event.current_buffer
            cb.insert_text(suggestion.text)
            return True

        # Else, default to normal TAB behavior, which cycles through
        # list of completions ('menu-complete').
        return False

    def handle_backward_char(self, event):
        """Awesome Prompt LEFT handler."""
        return False

    def handle_forward_char(self, event):
        """Awesome Prompt RIGHT handler."""
        return False
