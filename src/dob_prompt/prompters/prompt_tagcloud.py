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

from prompt_toolkit.validation import Validator

from .colors_terrific import TerrificColors2
from .hacky_processor import HackyProcessor
from .interface_bonds import KeyBond
from .parts_suggester import FactPartCompleterSuggester
from .sophisti_prompt import SophisticatedPrompt
from .the_bottom_area import BottomBarArea

__all__ = (
    'PromptForMoreTags',
    # Private:
    #   'TagCloudBottomBarArea',
)


class PromptForMoreTags(SophisticatedPrompt):
    """
    """

    def __init__(self, controller):
        super(PromptForMoreTags, self).__init__(controller)
        self.activity = None
        # MAYBE/2019-11-24: (lb): Use OrderedDict? We could preserve tag ordering?? ha!
        self.tags_cache = {}

    @property
    def activity_name(self):
        if self.activity is None:
            return '<None>'
        else:
            return self.activity.name

    @property
    def category_name(self):
        if self.activity is None:
            return '<Act:None>'
        elif self.activity.category is None:
            return '<None>'
        else:
            return self.activity.category.name

    @property
    def colors(self):
        # FIXME: (lb): Replace hardcoded styles. Assign from styles.conf. #styling
        return TerrificColors2()

    @property
    def edit_part_type(self):
        return 'tag'

    @property
    def edit_part_text(self):
        return str(self.tags_cache)

    @property
    def history_topic(self):
        return 'meta_tag'

    @property
    def type_request(self):
        return _('Select <#tags> for “{}@{}”').format(
            self.activity_name, self.category_name,
        )

    @property
    def completion_hints(self):
        tags_hints = [
            _('Type tag or choose from dropdown, and press ENTER to add.'),
            _('To finish, press ENTER on a blank line (or press Ctrl-S).'),
            _('To remove tags, press F8 to view tags that can be removed...'),
            _('... and use arrow keys to choose a tag and ENTER to remove.'),
        ]
        tags_hints += super(PromptForMoreTags, self).completion_hints
        return tags_hints

    def init_completer(self):
        return FactPartCompleterSuggester(self.summoned)

    def init_processor(self):
        return HackyProcessor(self)

    def init_bottombar(self):
        return TagCloudBottomBarArea(self)

    def fetch_completions(self):
        if self.active_sort == self.bottombar.meta_sort_by_selected:
            results = self.refresh_completions_selected()
        else:
            results = super(PromptForMoreTags, self).fetch_completions()
        return results

    @property
    def no_completion(self):
        return self.no_completion_tag

    def refresh_completions_selected(self):
        results = []
        for tag_name in self.ordered_tags:
            result = SophisticatedPrompt.FakeUsageResult(tag_name, None, None)
            results.append(SophisticatedPrompt.FakeUsageWrapper(result, None, None))
        if self.sort_order == 'desc':
            results.reverse()
        return results

    def ask_for_tags(self, already_selected, activity, no_completion=None):
        self.selected_tags = set(tag.name for tag in already_selected)
        self.ordered_tags = list(self.selected_tags)
        self.ordered_tags.sort()

        self.activity = activity

        self.no_completion_tag = no_completion

        self.prepare_session()

        self.keep_prompting_until_satisfied()

        return self.selected_tags

    def keep_prompting_until_satisfied(self):
        try:
            self.prompt_for_tags()
        finally:
            self.clean_up_print_text_header()

    def prompt_for_tags(self):
        keep_asking = True
        while keep_asking:
            try:
                keep_asking = self.prompt_for_tag()
                # If we prompt again, start with suggestions showing.
                self.processor.start_completion = True
                self.reset_completer()
            except KeyboardInterrupt:
                self.ctrl_c_pressed = time.time()
                self.update_pending = True

    def prompt_for_tag(self):
        self.validator = TagCloudValidator(self)

        keep_asking = True
        text = self.session_prompt(validator=self.validator)
        if text:
            self.process_user_response(text)
        else:
            keep_asking = False
        return keep_asking

    def process_user_response(self, text):
        # Toggle: If not added, add tag; otherwise, remove.
        if text not in self.selected_tags:
            self.selected_tags.add(text)
            self.ordered_tags.append(text)
        else:
            self.selected_tags.remove(text)
            self.ordered_tags.remove(text)

    def refresh_completions_fact_part(self):
        activity = self.refresh_restrict_activity()
        category = self.refresh_restrict_category()
        results = self.tags_get_all(activity, category)
        results = self.remove_selected_from_completions(results)
        return results

    def tags_get_all(self, activity, category):
        # (lb): Using a tags cache makes the interface noticeably more
        # responsive for me (against my Hamster db with 10K+ entries).
        # I don't notice the activity and category cache, so much.
        cache_key = (activity, category, self.active_sort.action, self.sort_order)
        if cache_key in self.tags_cache:
            return self.tags_cache[cache_key]

        results = self.controller.tags.get_all(
            include_stats=True,
            raw=True,
            match_activities=[] if activity is False else [activity],
            match_categories=[] if category is False else [category],
            sort_cols=(self.active_sort.action,),
            sort_orders=(self.sort_order,),
        )
        self.tags_cache[cache_key] = results
        return results

    def refresh_restrict_activity(self):
        activity = False
        if not self.activity:
            assert False  # Need actegory before tags, eh?
            return activity
        act_restrict = TagCloudBottomBarArea.TOGGLE_TYPES[
            TagCloudBottomBarArea.RESTRICT_ACT
        ]
        if self.bottombar.restrict_type == act_restrict:
            activity = self.activity
        return activity

    def refresh_restrict_category(self):
        category = False
        if not self.activity:
            assert False  # Need actegory before tags, eh?
            return category
        cat_restrict = TagCloudBottomBarArea.TOGGLE_TYPES[
            TagCloudBottomBarArea.RESTRICT_CAT
        ]
        if self.bottombar.restrict_type == cat_restrict:
            category = self.activity.category
        return category

    def remove_selected_from_completions(self, results):
        culled = []
        for result in results:
            if result[0].name in self.selected_tags:
                continue
            culled.append(result)
        return culled

    # ***

    @property
    def changed_since_init(self):
        # The init text state is the empty string, so True if anything but.
        return bool(self.session.app.current_buffer.text)

    def approve_exit_request(self):
        """Awesome Prompt Ctrl-q handler."""
        exitable = super(PromptForMoreTags, self).approve_exit_request()
        if exitable:
            pass  # Get ready for exit?
        return exitable

    @property
    def prompt_header_hint(self):
        what_hint = super(PromptForMoreTags, self).prompt_header_hint
        if what_hint:
            return what_hint

        what_hint = _(
            'Type tag and ENTER to add / Use F8 to remove tags / Ctrl-s to finish'
        ).format()
        return what_hint

    def prompt_recreate_filled(self, max_col=0):
        fake_prompt = '{}{}'.format(
            self.session_prompt_prefix,
            self.session.layout.current_buffer.text,
        )
        self.debug('fake_prompt: {}'.format(fake_prompt))
        line_parts = [('', fake_prompt)]
        return line_parts

    # ***

    def handle_clear_screen(self, event):
        """Awesome Prompt Ctrl-l handler."""
        # (lb): IDGI: For TagCloud (which uses this method), I tried to DRY, and call:
        #   return self.handle_content_reset(event)
        # but I see a weird boxy character get inserted, or I see a character
        # in the one space between the prompt and the input field -- the reset
        # sets text='' but for some reason has to cursor_position=1. But not
        # here. Here the expectable cursor_position=0 works as expected. So
        # what gives, I don't understand.
        event.current_buffer.text = ''
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        return True

    def handle_content_reset(self, event):

        # Clear the input text.
        event.current_buffer.text = ''

        # (lb): 2020-04-10: Removed some logic here. Code use to mess around
        # with the cursor, I think to reset the hint text above the prompt
        # (similar to how Ctrl-c behaves). But ran into issues with the
        # prompt not getting repositioned correctly, or buffer input not
        # being completely overwritten. So just return now. Behavior on
        # Escape feels much better.
        # - To reproduce: Type one character in input, then press Escape
        #   and wait a brief moment for PTK's double-key binding timeout
        #   to fire our handler. On first Escape, completion dropdown is
        #   hidden. After that, press Escape again, and cursor being sent
        #   to leftmost column of line (and '> ' prompt not seen). If you
        #   type, then cursor might correct itself. Also, if you enter two
        #   characters in input, or three, etc. you'd see different behavior.
        #   - In lieu of forcing you to view git history, here was the old code:
        #       # (lb): Weird, setting position to 0 causes non printing character
        #       # to print (or whatever, a boxy character). So use at least 1.
        #       # (This does seem odd. We do not do this elsewhere in the code.)
        #       # - Note that event.current_buffer.cursor_position
        #       #    is still == len(event.current_buffer.text).
        #       buffer = event.current_buffer
        #       buffer.cursor_position = len(buffer.text) or 1
        #       self.update_input_hint(event)
        #   - I even tried `self.update_pending = True`, but did not help.


# ***

class TagCloudBottomBarArea(BottomBarArea):
    """
    """

    TOGGLE_TYPES = [_('all'), _('act'), _('cat')]
    RESTRICT_ALL = 0
    RESTRICT_ACT = 1
    RESTRICT_CAT = 2

    def __init__(self, prompt):
        super(TagCloudBottomBarArea, self).__init__(prompt)
        self.restrict_type = TagCloudBottomBarArea.TOGGLE_TYPES[0]

    @property
    def say_types(self):
        return _('Tags')

    @property
    def sort_binding_meta(self):
        sort_bindings = super(TagCloudBottomBarArea, self).sort_binding_meta
        sort_bindings.append(self.meta_sort_by_selected)
        return sort_bindings

    @property
    def meta_sort_by_selected(self):
        # NOTE: Need to specify 'action', or binding won't get applied
        #       (because parent class logic). So using dummy, 'selected'.
        #       (lb): We don't use action callback, but do special check in
        #       fetch_completions, which is sorta lame (coupling) but it works.
        return KeyBond(
            'f8',
            _('selected'),
            action='selected',
            highlight=self.meta_sort_highlight,
            briefs=[_('selected')],
            wordy=_('{types} you have selected'),
            sort_order='asc',
        )

    def init_hooks_filter(self):
        def brief_scope(binding):
            return self.restrict_type

        # Option to toggle between filtering tags by acts, cats, or neither.
        self.filter_bindings = [
            KeyBond(
                'f9',
                brief_scope,
                self.toggle_scope,
                briefs=TagCloudBottomBarArea.TOGGLE_TYPES,
                highlight=True,
            ),
        ]

    def toggle_scope(self, event):
        curr = TagCloudBottomBarArea.TOGGLE_TYPES.index(self.restrict_type)
        curr = (curr + 1) % len(TagCloudBottomBarArea.TOGGLE_TYPES)
        self.restrict_type = TagCloudBottomBarArea.TOGGLE_TYPES[curr]
        self.prompt.restart_completer(event)

    def extend_bottom(self, _builder, dummy_section):
        parts = []
        parts.append(('', '\n'))
        self.extend_bottom_tagged(parts, dummy_section)
        return parts

    def extend_bottom_tagged(self, parts, dummy_section):
        if not self.prompt.ordered_tags:
            return
        dummy_section.add_zinger(_('Selected: '))
        self.extend_bottom_tag_names(dummy_section)
        self.extend_bottom_truncate_names(dummy_section)
        parts += dummy_section.parts

    def extend_bottom_tag_names(self, dummy_section):
        for tag_name in self.prompt.ordered_tags:
            dummy_section.add_normal(_('#'))
            dummy_section.add_zinger(tag_name)
            dummy_section.add_normal(_(' '))

    def extend_bottom_truncate_names(self, dummy_section):
        term_width = self.prompt.get_size()[1]
        dummy_section.truncate(term_width, _(' <See all with [F8]>'))


class TagCloudValidator(Validator):
    """"""

    def __init__(self, prompt, *args, **kwargs):
        super(TagCloudValidator, self).__init__(*args, **kwargs)
        self.prompt = prompt

    def validate(self, document):
        # A little coupled. User is doing something, so hide Ctrl-q hint.
        self.prompt.reset_timeouts()

