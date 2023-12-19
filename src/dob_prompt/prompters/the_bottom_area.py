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

from gettext import gettext as _

from prompt_toolkit.styles import Style

from .interface_bonds import KeyBond
from .interface_fanny import BindingsBarBuilder

__all__ = (
    'BottomBarArea',
)


# ***


class BottomBarArea(object):
    """
    """

    def __init__(self, prompt):
        self.prompt = prompt
        self.active_sort = None

    def stand_up(self, key_bindings):
        self.wire_hooks(key_bindings)
        self.build_builder()

    # ***

    @property
    def say_types(self):
        raise NotImplementedError

    # ***

    @property
    def complete_while_typing(self):
        return (self.active_sort is None) or (self.active_sort.action != 'order')

    @property
    def enable_history_search(self):
        # When using completions, do not hook up up arrow to browsing
        # through history. Otherwise, do.
        return self.active_sort and self.active_sort.action == 'order'

    @property
    def default_sort(self):
        return self.meta_sort_by_name

    @property
    def sorting_by_history(self):
        return self.active_sort == self.meta_sort_by_history

    # ***

    def init_hooks(self):
        self.init_hooks_sort()
        self.init_hooks_filter()
        self.init_hooks_settings()

        self.init_binding_meta()

    def init_hooks_sort(self):
        self.sort_bindings = self.sort_binding_meta

    def init_hooks_filter(self):
        self.filter_bindings = self.filter_binding_meta

    def init_hooks_settings(self):
        self.settings_bindings = self.settings_binding_meta

    def init_binding_meta(self):
        self.all_bindings = (
            self.sort_bindings
            + self.filter_bindings
            + self.settings_bindings
        )
        self.binding_meta = {}
        for binding in self.all_bindings:
            if binding.keycode:
                self.binding_meta[binding.keycode] = binding

    # ***

    @property
    def sort_binding_meta(self):
        sort_bindings = [
            self.meta_sort_by_name,
            self.meta_sort_by_start,
            self.meta_sort_by_usage,
            self.meta_sort_by_time,
            self.meta_sort_by_history,
        ]
        return sort_bindings

    # ***

    def meta_sort_briefly(self, brief):
        def briefly(binding, highlight=None, sort_order=None):
            if highlight is None:
                highlight = self.meta_sort_highlight(binding)
            if not highlight:
                return brief
            if sort_order is None:
                sort_order = self.prompt.sort_order
            marker = '↑' if sort_order == 'asc' else '↓'
            briefed = '{} {}'.format(brief, marker)
            return briefed
        return briefly

    def meta_sort_briefs(self, brief):
        briefly = self.meta_sort_briefly(brief)
        briefs = []
        for sort_order in ['asc', 'desc']:
            briefs.append(
                briefly(None, highlight=False, sort_order=sort_order)
            )
        return briefs

    def meta_sort_reserve_width(self):
        return len('↑') + len(' ')

    def meta_sort_highlight(self, binding):
        if not self.prompt.showing_completions or binding != self.active_sort:
            return False
        return True

    # ***

    @property
    def meta_sort_by_name(self):
        return KeyBond(
            'f2',
            self.meta_sort_briefly(_('name')),
            action='name',
            briefs=self.meta_sort_briefs(_('name')),
            highlight=self.meta_sort_highlight,
            wordy=_('All {types} sorted alphabetically'),
            sort_order='asc',
        )

    @property
    def meta_sort_by_start(self):
        return KeyBond(
            # (lb): I kinda like 'latest' to not confuse 'start' with 'time',
            # but 'start' is technically the most correct, as this options
            # sorts suggestions by Fact.start.
            'f3',
            self.meta_sort_briefly(_('start')),
            action='start',
            briefs=self.meta_sort_briefs(_('start')),
            highlight=self.meta_sort_highlight,
            wordy=_('{types} you have applied to recent facts'),
            sort_order='desc',
        )

    @property
    def meta_sort_by_usage(self):
        return KeyBond(
            # (lb): 'usage'? 'count'? Does it matter?
            'f4',
            self.meta_sort_briefly(_('count')),
            action='usage',
            briefs=self.meta_sort_briefs(_('count')),
            highlight=self.meta_sort_highlight,
            wordy=_('{types} which you have used on the most facts'),
            sort_order='desc',
        )

    @property
    def meta_sort_by_time(self):
        return KeyBond(
            'f5',
            self.meta_sort_briefly(_('time')),
            action='time',
            briefs=self.meta_sort_briefs(_('time')),
            highlight=self.meta_sort_highlight,
            wordy=_('{types} on which you have spent the most time'),
            sort_order='desc',
        )

    @property
    def meta_sort_by_history(self):
        return KeyBond(
            # (lb): I like 'history', but it's a long word.
            #       I tried 'typed' for a while as the UX name, but it's
            #        a mental stretch ("Oh! things I *typed* in the past").
            #       So let's try 'hist', which is nice and terse.
            'f6',
            self.meta_sort_briefly(_('hist')),
            action='history',
            briefs=self.meta_sort_briefs(_('hist')),
            highlight=self.meta_sort_highlight,
            wordy=_('{types} you have recently entered'),
            sort_order='desc',
        )

    # ***

    @property
    def filter_binding_meta(self):
        filter_bindings = []
        return filter_bindings

    # ***

    @property
    def settings_binding_meta(self):
        settings_bindings = [
            self.meta_settings_ignore_case,
            self.meta_settings_match_middle,
        ]
        return settings_bindings

    @property
    def meta_settings_ignore_case(self):
        def handle_ignore_case(event):
            self.prompt.completer.toggle_ignore_case()
            self.prompt.bottom_toolbar_reset()

        def brief_ignore_case(binding):
            if self.prompt.completer.ignore_case:
                brief = _('case')
            else:
                brief = _('Case')
            return brief

        # NOTE: (lb): A lot of the Ctrl key bindings are taken, at least in Vi mode,
        #       so I've chosen to use Meta key combos instead. E.g., Ctrl-y is yank!
        #       Note, too, that Python Prompt Toolkit has some magic bindings. For
        #       instance, the keycode 'c-i' is used to specify Ctrl-i, but it's also
        #       doubly mapped to <Tab>. Hence, it's less trouble binding M-i.
        #       (Also, Alt-c is mapped to opening the completion dropdown.)

        return KeyBond(
            # # (lb): Used to use escape code, not sure why/when stopped working:
            # #  ('escape', 'i'),
            # ('m-i',),
            # 2020-03-30: Trying escape-i again, m-i is a fork feature,
            # and I'd rather not have to publish yet another forked project.
            ('escape', 'i'),
            brief_ignore_case,
            handle_ignore_case,
            briefs=[_('case'), _('Case')],
            highlight=True,
        )

    @property
    def meta_settings_match_middle(self):
        def handle_match_middle(event):
            self.prompt.completer.toggle_match_middle()
            self.prompt.bottom_toolbar_reset()

        def brief_match_middle(binding):
            if self.prompt.completer.match_middle:
                brief = _('middle')
            else:
                brief = _('start')
            return brief

        return KeyBond(
            # # (lb): Used to use escape code, not sure why/when stopped working:
            # #  ('escape', 'm'),
            # ('m-m',),
            # 2020-03-30: Trying again, against nascent upstream and not HOTH:
            ('escape', 'm'),
            brief_match_middle,
            handle_match_middle,
            briefs=[_('middle'), _('start')],
            highlight=True,
        )

    # ***

    def wire_hooks(self, key_bindings):
        self.init_hooks()

        def make_filter_handler(keycode):
            def handler(event):
                # FIDDLING: You can insert text into the buffer, e.g.,
                #  event.app.current_buffer.insert_text('{}!'.format(keycode))
                self.prompt.restart_completer(
                    event, self.binding_meta[keycode], toggle_ok=True,
                )

            return handler

        for binding in self.all_bindings:
            if isinstance(binding.action, str):
                handler = make_filter_handler(binding.keycode)
            elif callable(binding.action):
                handler = binding.action
            else:
                assert False  # (lb): Code path never travelled.
                assert binding.action is None
                handler = None
            if handler is not None:
                # NOTE: (lb): key_bindings.add is normally used as a @decorator.
                #       But here we just wire the higher order component directly
                #       (there might be another way to do this, but I'm not sure).
                if isinstance(binding.keycode, str):
                    key_bindings.add(binding.keycode)(handler)
                else:
                    # An iterable, e.g., escape sequence (for meta-key combos).
                    key_bindings.add(*binding.keycode)(handler)

    # ***

    @property
    def prompt_style(self):
        # Set a prompt style so background colors extends full terminal width.
        # (Otherwise, to get same effect, so could pad each line with spaces
        # to the terminal width using the background color we wanted; but this
        # is a lot easier.)
        style = Style.from_dict({
            'bottom-toolbar': '#{} bg:#{}'.format(
                # FIXME/2019-12-01: Move hardcoded values to styling config. #styling
                self.prompt.colors.color_2,
                self.prompt.colors.color_1,
            ),
            # We could specify the text color here, e.g.,
            #  'bottom-toolbar.text': '#FCA5A5 bg:#AA3939',
            # but we instead use (color, text) tuples in
            # bottom_toolbar renderer for finer-grained control.
        })
        return style

    # ***

    # Bottom toolbar usage: See:
    #   examples/prompts/bottom-toolbar.py
    def build_builder(self):
        def build_bottom_toolbar():
            builder = BindingsBarBuilder(
                colors=self.prompt.colors,
            )
            add_bindings_sort(builder)
            add_bindings_filter(builder)
            add_bindings_settings(builder)
            builder.add_footer(self.extend_bottom)
            return builder

        # ***

        def add_bindings_sort(builder):
            builder.add_bindings(
                self.sort_bindings,
                sort_bindings_plinth,
                reserve_width=self.meta_sort_reserve_width(),
            )

        def add_bindings_filter(builder):
            builder.add_bindings(
                self.filter_bindings,
                _('Scope'),
            )

        def add_bindings_settings(builder):
            builder.add_bindings(
                self.settings_bindings,
                _('Match'),
            )

        # ***

        def sort_bindings_plinth():
            if not self.prompt.showing_completions:
                description = '▲ Choose a sort order to see hints ▲'
            else:
                description = self.active_sort.wordy.format(types=self.say_types)
            return description

        # ***

        self.builder = build_bottom_toolbar()

    def extend_bottom(self, builder):
        raise NotImplementedError

