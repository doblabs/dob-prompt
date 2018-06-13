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

"""Hamster CLI ``hamster list`` commands."""

from __future__ import absolute_import, unicode_literals

from gettext import gettext as _

# FIXME: RENAME and release pyoiler* libraries
from pyoiler_inflector import Inflector
from pyoiler_timedelta import timedelta_wrap
from prompt_toolkit.auto_suggest import Suggestion
from prompt_toolkit.completion import WordCompleter

__all__ = [
    'FactPartCompleterSuggester',
]


class FactPartCompleterSuggester(WordCompleter):
    """
    """

    def __init__(self, summoned):
        self.summoned = summoned
        super(FactPartCompleterSuggester, self).__init__(
            words=[], ignore_case=True, match_middle=True, sentence=True,
        )

    def hydrate(self, results, **kwargs):
        words = []
        metad = {}
        for idx, result in enumerate(results):
            # (lb): I'm just curious; showing that this is a namedtuple.
            item, usage, span = result
            assert results[idx].uses is usage
            assert results[idx].span is span

            self.hydrate_result(result, words, metad, **kwargs)
        self.words = words
        self.meta_dict = metad

    def hydrate_result(self, result, words, metad, **kwargs):
        item, usage, span = result

        name = self.hydrate_name(item, **kwargs)
        words.append(name)

        self.hydrate_result_usage(name, usage, span, metad)

    def hydrate_result_usage(self, name, usage, span, metad):
        if not usage or not span:
            return

        (
            tm_fmttd, tm_scale, tm_units,
        ) = timedelta_wrap(days=span).time_format_scaled()

        metad[name] = _(
            'Used on {usage} {facts} for {time}: “{name}”'
        ).format(
            name=name,
            usage=usage,
            facts=Inflector.pluralize(_('fact'), usage != 1),
            time=tm_fmttd,
        )

    def hydrate_name(self, item, **kwargs):
        return item.name

    def get_completions(self, document, complete_event):
        self.summoned(showing_completions=True)
        return super(FactPartCompleterSuggester, self).get_completions(
            document, complete_event,
        )

    def get_suggestion(self, _buffer, document):
        text = document.text.lower()
        suggestion = self.get_suggestion_for(text)
        return suggestion

    def get_suggestion_for(self, text):
        if not text:
            return None  # No suggestion

        suggestion = ''
        for word in self.words:
            if word.lower().startswith(text):
                suggestion = word
                break
        suggestion = Suggestion(suggestion[len(text):])
        return suggestion

    def toggle_ignore_case(self):
        self.ignore_case = not self.ignore_case

    def toggle_match_middle(self):
        self.match_middle = not self.match_middle
