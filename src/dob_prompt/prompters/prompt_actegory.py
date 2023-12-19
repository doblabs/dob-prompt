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

from gettext import gettext as _

from prompt_toolkit.layout.processors import AfterInput, BeforeInput, Transformation
from prompt_toolkit.validation import Validator, ValidationError

from dob_bright.crud.enc_actegory_re import RegExpActegory

from .colors_terrific import TerrificColors1
from .hacky_processor import HackyProcessor
from .interface_bonds import KeyBond
from .parts_suggester import FactPartCompleterSuggester
from .sophisti_prompt import SophisticatedPrompt
from .the_bottom_area import BottomBarArea

__all__ = (
    'PromptForActegory',
    # Private:
    #   'ActegoryCompleterSuggester',
    #   'ActegoryHackyProcessor',
    #   'ActegoryBottomBarArea',
)


class PromptForActegory(SophisticatedPrompt):
    """
    """

    def __init__(self, controller):
        super(PromptForActegory, self).__init__(controller)
        self.activities_cache = {}
        self.categories_cache = {}

        self.activity = ''
        self.category = ''
        self.lock_act = False

        self.re_actegory = RegExpActegory(self.sep)

    # ***

    @property
    def sep(self):
        return '@'

    # ***

    # BOIL-DRY handlers: When user deletes backwards, double-deleting the
    # empty string can switch the prompt from Category input back to
    # Activity input (which affects what the prompt looks like, what
    # suggestions it gives, what the hint above the prompt reads, what
    # the bottom bar displays, etc.).

    def boil_dry_on_backspace_if_text_empty(self, event):
        boiling_dry = not event.current_buffer.text
        self.debug('boiling_dry: {}'.format(boiling_dry))
        if boiling_dry:
            # PPT does not trigger validator unless text changes,
            # and text *is* empty -- before event consumed by PPT
            # -- so we're not expecting a callback. So do things now.
            if self.lock_act:
                self.forget_category(event)
        return boiling_dry

    def handle_backspace_delete_char(self, event):
        def _handle_backspace_delete_char():
            boiling_dry = self.boil_dry_on_backspace_if_text_empty(event)
            self.debug('boiling_dry: {}'.format(boiling_dry))
            if boiling_dry:
                # The text is empty, so by pressing backspace, the user
                # triggered a switch from Category input to Activity input.
                return True
            return delete_before_cursor_with_magic_wrap_left()

        def delete_before_cursor_with_magic_wrap_left():
            # Check if cursor is all the way to the left, then always switch
            # input context (Category → Activity → Category, etc.), regardless
            # of if text is empty of not.
            # (lb): I may change this behavior in the future, if it doesn't stick.
            self.debug('posit: {}'.format(event.current_buffer.cursor_position))
            if event.current_buffer.cursor_position == 0:
                # Cursor is all the way left... do it do it do it
                # [switch from category mode to activity mode;
                # or from start of activity to end of category].
                # MAYBE/2019-11-25: (lb): Depending on how this feature feels in
                #                   actual usage, we might want to disable this.
                self.toggle_lock_act(event)
                return True
            return delete_before_cursor_with_restore_completions_right()

        def delete_before_cursor_with_restore_completions_right():
            delete_before_cursor_for_real()
            if event.current_buffer.cursor_position == len(event.current_buffer.text):
                # The delete_before_cursor disabled the completion dropdown.
                # If the cursor is at the end of the input, show completions again.
                # (lb): I like this behavior. It matches typing forward, which shows
                # the completions. And we don't show completions unless the cursor is
                # farthest to the right, otherwise if the user were to see and accept
                # a completion, it would push what's to the right of the cursor more
                # to the right... unless if the user accepted a completion in the
                # middle of existing text and we coded it to remove what was to the
                # right of the cursor. Which seems like more work than it's worth.
                self.session.layout.current_buffer.start_completion()
            return True

        def delete_before_cursor_for_real():
            # CXPX: backward_delete_char [calls delete_before_cursor and bell].
            deleted = event.current_buffer.delete_before_cursor(count=event.arg)
            # - PPT then calls `event.app.output.bell()` if not deleted,
            #   but we know nothing not deleted because not boiling_dry.
            self.controller.affirm(deleted)

        return _handle_backspace_delete_char()

    def reset_completer(self, binding=None, toggle_ok=False):
        super(PromptForActegory, self).reset_completer(binding, toggle_ok)

    def handle_backspace_delete_more(self, event):
        if self.boil_dry_on_backspace_if_text_empty(event):
            return True

        # Our wire_hook_backspace callback does not call the PPT basic binding
        # for Ctrl-Backspace/Ctrl-h (which is 'backward-delete-char', the
        # same as for normal Backspace). Instead delete either the category,
        # or the activity. I.e., Ctrl-Backspace is a quick way to delete just
        # the category, but leave the activity.
        if self.lock_act:
            self.forget_category(event)
            return True

        self.activity = ''
        self.forget_category(event)
        return True

    def handle_clear_screen(self, event):
        self.activity = ''
        self.forget_category(event, '')
        return True

    def handle_word_rubout(self, event):
        return self.boil_dry_on_backspace_if_text_empty(event)

    def handle_accept_line(self, event):
        if not self.lock_act:
            text = event.current_buffer.text
            self.debug('dissemble: text: {}'.format(text))
            set_act_cat = self.try_disassemble_parts(text)
            if set_act_cat:
                # Bail now. Because false, our code will trigger PPT's
                # accept-line, and session_prompt will finish. We're done!
                return False
            if not set_act_cat:
                # TESTME/2019-11-27: (lb): I believe validator will have run
                # and decoded the text... but I'm not 💯.
                activity = text
                self.lock_activity(activity, lock_act=True)
                # (lb): While we don't show the completions drop down when the
                # prompt is first started (i.e., when prompting for Activity
                # name), I think it's nice to show the drop down automatically
                # for the latter Category half of the prompt session. There are
                # generally fewer Categories than Activities, and once the user
                # puts in a few, they're unlikely to add more, so it makes sense
                # to just show the list without waiting for user to trigger it.
                # Also, the user is more familiar with the prompt now, which is
                # one reason we don't want to show the completions drop down
                # immediately on prompt, because it can make the interface look
                # daunting.
                self.session.layout.current_buffer.start_completion()
            if self.category:
                # If the category is already set, user would have had to switch
                # state back to the Activity, and now they're hitting ENTER.
                # (lb): So I'd guess the user is ready for ENTER to mean, I'm done
                # with the input dialog. Return False and have PPT finish prompting.
                return False
            return True
        # Let PPT process the call, which will spit out in
        # prompt_for_actegory, but we can set the category
        # here, so it's near lock_activity which set activity.
        self.category = event.current_buffer.text
        return False

    def handle_backward_char(self, event):
        """Awesome Prompt LEFT handler."""
        if event.current_buffer.cursor_position == 0:
            self.toggle_lock_act(event)
            return True
        return False

    def handle_forward_char(self, event):
        """Awesome Prompt RIGHT handler."""
        if event.current_buffer.cursor_position == len(event.current_buffer.text):
            self.toggle_lock_act(event)
            # toggle_lock_act puts cursor to right of input, but user pressed
            # right arrow, so put cursor back to the left instead.
            event.current_buffer.cursor_position = 0
            return True
        return False

    def handle_content_reset(self, event):
        self.update_state(self.activity0, self.category0)
        reset_text = self.lock_act and self.category or self.activity
        event.current_buffer.text = reset_text
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        self.update_input_hint(event)
        return True

    # ***

    def forget_category(self, event, new_text=None):
        self.category = ''
        self.reset_lock_act(event, new_text)

    def reset_lock_act(self, event, new_text=None):
        was_lock_act = self.lock_act
        self.lock_act = False
        self.update_input_hint(event)
        if new_text is None:
            new_text = self.activity
        # (lb): I tested insert_text and it seems to work the same,
        # or at least it seems to update the text, e.g.,
        #   event.current_buffer.insert_text(new_text, overwrite=True)
        # but I'm not sure about the cursor_position, so being deliberate
        # and setting text, then cursor_position explicitly. (And a lot of
        # this is trial and error -- we're messing with both PPT and directly
        # with the renderer.output, which is all hacky, or at least fragile.)
        event.current_buffer.text = new_text
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        if was_lock_act != self.lock_act:
            self.restart_completer(event)

    @property
    def prompt_header_hint(self):
        what_hint = super(PromptForActegory, self).prompt_header_hint
        if what_hint:
            return what_hint

        what = self.edit_part_type.capitalize()
        # (lb): In addition to keys hinted, you can also Ctrl-SPACE. For now.
        if not self.lock_act:
            what_hint = _('Enter the {} then hit ENTER or `@`').format(what)
        else:
            what_hint = _('Enter the {} then hit ENTER or Ctrl-s').format(what)
        return what_hint

    def prompt_recreate_filled(self, max_col=0):
        fake_prompt = '{}{}{}{}'.format(
            self.session_prompt_prefix,
            self.activity,
            self.sep,
            self.category,
        )
        self.debug('fake_prompt: {}'.format(fake_prompt))
        line_parts = [('', fake_prompt)]
        return line_parts

    # ***

    @property
    def colors(self):
        # FIXME: (lb): Replace hardcoded styles. Assign from styles.conf. #styling
        return TerrificColors1()

    @property
    def edit_part_type(self):
        if not self.lock_act:
            # (lb): Just say 'activity', and not
            # the more-correct 'activity@category'.
            part_meta = _('activity')
        else:
            part_meta = _('category')
        return part_meta

    @property
    def edit_part_text(self):
        if not self.lock_act:
            part_text = self.activity
        else:
            part_text = self.category
        return part_text

    @property
    def history_topic(self):
        return 'actegory'

    @property
    def type_request(self):
        return _('Enter an Activity{}Category').format(self.sep)

    @property
    def completion_hints(self):
        tags_hints = [
            _('Type the Activity name or choose an Act{}Gory from the dropdown.'
              ).format(self.sep),
            _('Press ENTER to set the Activity (or type ‘{}’, or press Ctrl-s).'
              ).format(self.sep),
            _('Next, type the Category name, and then press ENTER or Ctrl-s.'),
            _('Use arrow keys or press F9 to jump between Activity and Category.'),
        ]
        tags_hints += super(PromptForActegory, self).completion_hints
        return tags_hints

    def init_completer(self):
        return ActegoryCompleterSuggester(self, self.summoned)

    def init_processor(self):
        return ActegoryHackyProcessor(self)

    def init_bottombar(self):
        return ActegoryBottomBarArea(self)

    def toggle_lock_act(self, event):
        if not self.lock_act:
            activity = event.current_buffer.text
            self.lock_activity(activity)
        else:
            self.category = event.current_buffer.text
            self.reset_lock_act(event)

    # ***

    def update_state(self, activity, category, lock_act=False, startup=False):
        self.activity = activity
        self.category = category

        was_lock_act = self.lock_act

        self.lock_act = False
        if self.activity or lock_act:
            self.lock_act = True

        if (
            (not startup)
            and (self.session is not None)
            and (was_lock_act != self.lock_act)
        ):
            self.update_input_hint_renderer()
            self.restart_completer(event=None)

    def lock_activity(self, activity, lock_act=False):
        self.session.layout.current_buffer.text = self.category
        self.session.layout.current_buffer.cursor_position = (
            len(self.session.layout.current_buffer.text)
        )
        self.update_state(activity, self.category, lock_act=lock_act)

    # ***

    def ask_act_cat(
        self,
        filter_activity,
        filter_category,
        no_completion_act=None,
        no_completion_cat=None,
    ):
        self.activity0 = filter_activity
        self.category0 = filter_category

        self.no_completion_act = no_completion_act
        self.no_completion_cat = no_completion_cat

        self.update_state(filter_activity, filter_category, startup=True)

        self.prepare_session()

        self.keep_prompting_until_satisfied()

        return self.activity, self.category

    def keep_prompting_until_satisfied(self):
        blocking_ctrl_c = True
        while blocking_ctrl_c:
            try:
                self.prompt_for_actegory()
                blocking_ctrl_c = False
            # (lb): We shouldn't expect to see EOFError here (an I/O error),
            # but the user pressing Ctrl-c raises KeyboardInterrupt. (Which
            # we could prevent by wiring a PPT KeyBinding on 'c-c', but don't.)
            # The Awesome Prompt is run from the interactive editor (Carousel),
            # which maps Ctrl-c to Copy. So don't die on Ctrl-c here, so that
            # users have a more consistent experience (albeit in lieu of Copy,
            # in Awesome Prompt, a Ctrl-c just does nothing... well, it does
            # something, but it's innocuous, it shows a message telling the
            # user to try Ctrl-q if they really want to exit-quit).
            except KeyboardInterrupt:
                # Ye olde Ctrl-c, and not an Exception.
                # Note that we'll just re-run the prompt. The only thing
                # the user will see is that the cursor goes to the end of
                # the input (either the Activity or the Category). We could
                # fix this by recording the cursor position, and then restoring
                # it. But it's also nice to have a little reaction to a Ctrl-c,
                # especially when the user might be expecting it to cancel the
                # whole show. Instead, it just nudges the cursor to the end, like
                # a little burp.
                self.ctrl_c_pressed = time.time()
                # Because prompt died, cannot (perform a kludgey) print right now.
                # So wait for prompt to be regenerated, then move cursor and print.
                self.update_pending = True
            finally:
                if not blocking_ctrl_c:
                    self.clean_up_print_text_header()

    def prompt_for_actegory(self):
        self.debug(_('{}@{}').format(self.activity, self.category))

        if not self.lock_act:
            default = self.activity
        else:
            default = self.category

        self.validator = ActegoryValidator(self)
        self.validator.update_last_seen()

        # Call PPT's PromptSession.session to handle user interaction.
        # Our completer, validator, and key bindings will craft the experience.
        # The prompt returns the final input field text, which will be either a
        # complete (@-escaped) act@gory, or just the category, depending on how
        # the user interacted with the prompt. But we don't care at this point.
        # Our prompt class captures the text in handle_accept_line, just before
        # PPT's accept-line is called (which causes session_prompt to return).
        # If the last prompt state was setting the category, the buffer text
        # was used to set self.category; otherwise, the user entered an act@gory
        # into the activity input (i.e., selected an entry from the completion
        # dropdown and pressed ENTER), and handle_accept_line parsed both the
        # activity and the category from the text. (So the text returned here
        # is either the category, or it's the act@gory (possibly escaped, too,
        # e.g., _text could be 'act\\@still the activity name@category name').

        _result = self.session_prompt(
            default=default,
            validator=self.validator,
        )

        self.debug('prompt done! / _result: {}'.format(_result))

    # ***

    def refresh_completions_fact_part(self):
        if self.lock_act:
            results = self.refresh_completions_categories()
        else:
            results = self.refresh_completions_activities()
        return results

    def refresh_completions_categories(self):
        cache_key = (None, self.active_sort.action, self.sort_order)
        if cache_key in self.categories_cache:
            return self.categories_cache[cache_key]

        results = self.controller.categories.get_all(
            include_stats=True,
            named_tuples=True,
            raw=True,
            sort_cols=(self.active_sort.action,),
            sort_orders=(self.sort_order,),
        )
        self.categories_cache[cache_key] = results
        return results

    def refresh_completions_activities(self):
        # Called on not self.lock_act.
        category = self.refresh_restrict_category()
        cache_key = (category, self.active_sort.action, self.sort_order)
        if cache_key in self.activities_cache:
            return self.activities_cache[cache_key]

        results = self.controller.activities.get_all(
            include_stats=True,
            named_tuples=True,
            raw=True,
            match_categories=[category] if category is not False else [],
            sort_cols=(self.active_sort.action,),
            sort_orders=(self.sort_order,),
        )
        self.activities_cache[cache_key] = results
        return results

    def refresh_restrict_category(self):
        # Called on not self.lock_act.
        category = False
        if self.category:
            try:
                category = self.controller.categories.get_by_name(self.category)
            except KeyError:
                category = self.category
        return category

    @property
    def no_completion(self):
        if not self.lock_act:
            no_completion = self.no_completion_act
        else:
            no_completion = self.no_completion_cat
        return no_completion

    def hydrate_completer(self, results):
        self.completer.hydrate(
            results,
            skip_category_name=bool(self.category),
            no_completion=self.no_completion,
        )

    def history_entry_name(self, entry):
        entry_name = entry
        if self.lock_act and self.re_actegory.re_unescaped_sep.search(entry):
            # In Category mode, but history lists act@gories, so split apart
            # and discard the Activity name.
            _activity_name, category_name = self.re_actegory.split_parts(entry)
            return category_name
        return entry_name

    # ***

    def completions_changed(self):
        super(PromptForActegory, self).completions_changed()

        if self.showing_completions:
            return

        text = self.session.app.current_buffer.text
        self.debug('dissemble: text: {}'.format(text))
        _set_act_cat = self.try_disassemble_parts(text)  # noqa: F841

    def try_disassemble_parts(self, text):
        act_or_cat, category = self.re_actegory.split_parts(text)

        if category is not None:
            self.category = category
            self.lock_activity(act_or_cat)
            return True

        self.debug('!dissemble: lock? {} / act_or_cat: {}'.format(
            self.lock_act, act_or_cat,
        ))

        # Be sure to always consume the input, even if the user has not
        # finished (hit ENTER), so that a command like Ctrl-q can reliably
        # check if the inputs were changed since prompt inception.
        if not self.lock_act:
            self.activity = act_or_cat
        else:
            self.category = act_or_cat

        return False

    @property
    def changed_since_init(self):
        return (
            (self.activity != self.activity0)
            or (self.category != self.category0)
        )

    def approve_exit_request(self):
        """Awesome Prompt Ctrl-q handler."""
        exitable = super(PromptForActegory, self).approve_exit_request()
        if exitable:
            self.activity = self.activity0
            self.category = self.category0
        return exitable

    # ***


class ActegoryCompleterSuggester(FactPartCompleterSuggester):
    """
    """

    def __init__(self, prompt, *args, **kwargs):
        super(ActegoryCompleterSuggester, self).__init__(*args, **kwargs)
        self.prompt = prompt

    def hydrate_name(self, item, skip_category_name=False, **kwargs):
        name = item.name
        if not skip_category_name:
            try:
                name = '{}{}{}'.format(
                    self.escape_text(item.name),
                    self.prompt.sep,
                    self.escape_text(item.category.name),
                )
            except AttributeError:
                # item is AlchemyCategory, and we already set name = item.name. Pass!
                pass
        return name

    def escape_text(self, text):
        return self.prompt.re_actegory.escape(text)


class ActegoryHackyProcessor(HackyProcessor):
    """
    """

    def __init__(self, prompt):
        super(ActegoryHackyProcessor, self).__init__(prompt)
        self.before_input = BeforeInput(text=self.prompt.sep)
        self.after_input = AfterInput(text=self.prompt.sep)

    def __repr__(self):
        return 'ActegoryHackyProcessor(%r)' % (self.prompt)

    def apply_transformation(self, transformation_input):
        # Note that this method completely shadows the parent's
        # so there's a little duplication herein (the prefix and
        # postfix around the if-elif branch are not DRY).
        self.mark_summoned(transformation_input)
        self.prompt.heartbeat()

        if self.prompt.lock_act:
            # Prefix the input with the Activity, e.g., "act@".
            text = '{}{}'.format(self.prompt.activity, self.prompt.sep)
            self.before_input.text = text
            return self.before_input.apply_transformation(transformation_input)

        elif self.prompt.category:
            # Follow the input with the Category, e.g., "@cat".
            text = '{}{}'.format(self.prompt.sep, self.prompt.category)
            self.after_input.text = text
            return self.after_input.apply_transformation(transformation_input)

        return Transformation(transformation_input.fragments)


class ActegoryBottomBarArea(BottomBarArea):
    """
    """

    def __init__(self, prompt):
        super(ActegoryBottomBarArea, self).__init__(prompt)

    @property
    def say_types(self):
        if not self.prompt.lock_act:
            return _('Activities')
        else:
            return _('Categories')

    def init_hooks_filter(self):
        def brief_scope(binding):
            return self.prompt.edit_part_type

        # Option to switch between cats and acts.
        self.filter_bindings = [
            KeyBond(
                'f9',
                brief_scope,
                action=self.toggle_scope,
                briefs=[_('category'), _('activity')],
                highlight=True,
            ),
        ]

    def toggle_scope(self, event):
        self.prompt.toggle_lock_act(event)

    def extend_bottom(self, _builder, _dummy_section):
        # The Tag prompt adds a line, so add a blank one now,
        # so prompt height does not grow later.
        return '\n'


class ActegoryValidator(Validator):
    """"""

    def __init__(self, prompt, *args, **kwargs):
        super(ActegoryValidator, self).__init__(*args, **kwargs)
        self.prompt = prompt
        self.update_last_seen()

    def update_last_seen(self):
        # The validator is called with every change to text -- and
        # then once on ENTER/'accept-line' where the text will be
        # the same as we just saw it.
        self.last_text = self.prompt.edit_part_text

    def validate(self, document):
        text = document.text
        last_text = self.last_text

        self.prompt.debug('text: {} / last_text: {}'.format(text, last_text))

        if self.last_text == text:
            # The text has not changed, which can happen when the user
            # types control characters, so just bail now; we already
            # know the score.
            return
        self.last_text = text

        # A little coupled. User is doing something, so hide Ctrl-q hint.
        self.prompt.reset_timeouts()

        # tl;dr: When the state is Activity input, the text is either an
        #   Activity name, or it's an encoded "act@gory". So look for an
        #   un-escaped separator ('@') in text. If found, split the text
        #   apart, lock the activity name, and switch to Category input.
        #
        # (lb): I had originally only had the code react if the user typed
        #   the separator character to the end of the input, e.g.,
        #
        #     last_char_is_sep = ((len(last_text) == len(text) - 1)
        #                         and (text.startswith(last_text))
        #                         and (text.endswith(self.prompt.sep)))
        #
        #   but we also check for the separator in completions_changed,
        #   and completions_changed is called pretty much a lot of the
        #   time (even when the completions dropdown does not appear to
        #   change state).
        #
        #   So we'll pretty much always look for the separator character
        #   in the input.
        #
        #   To avoid this magic, the user can escape the separator ('\\@').
        #
        #   Note also that this validator is not only triggered by the user
        #   typing single key presses, but also but changes caused by the
        #   user accepting a suggestion or by selecting a completion from
        #   the dropdown.

        # Because the completions list contains encoded act@gories, do not
        # process anything while the user is moving the completions selection
        # around. (lb): I have not tested what happens without this guard,
        # but I'd imagine chaos.
        if self.prompt.showing_completions:
            self.prompt.debug('showing completions')
            return

        self.prompt.debug('dissemble: text: {}'.format(text))
        _set_act_cat = self.prompt.try_disassemble_parts(text)  # noqa: F841

        # Use ValidationError to show message in bottom-left of prompt
        # (just above our the_bottom_area footer).
        # Not so fast: (lb): I think it's a useful message (it makes the prompt
        # less intimidating, I'd argue), but raising an error on every character
        # typed causes the suggestion list to flicker! So just do this for the
        # very first character the user types, then don't bother any more.
        if not last_text:
            if not self.prompt.lock_act:
                message = _('Type `{}` or press ENTER to finish {} name').format(
                    self.prompt.sep, self.prompt.edit_part_type.capitalize()
                )
            else:
                message = _('Type Ctrl-s or press ENTER to finish {} name').format(
                    self.prompt.edit_part_type.capitalize()
                )
            raise ValidationError(message=message, cursor_position=0)

