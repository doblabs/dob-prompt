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

"""PPT WordCompleter subclass."""

from gettext import gettext as _

from inflector import English, Inflector
from pedantic_timedelta import PedanticTimedelta
from prompt_toolkit.auto_suggest import Suggestion
from prompt_toolkit.completion import WordCompleter

__all__ = (
    'FactPartCompleterSuggester',
)


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
            # (lb): Just curious; showing that each result has attributes.
            # - Because get_all(raw=True), each result is an SQLAlchemy result
            #   object, <class 'sqlalchemy.util._collections.result'>. But if
            #   we used raw=False, we'd covert to a namedtuple (FakeUsageWrapper).
            item, usage, span = result
            assert results[idx].uses is usage
            assert results[idx].span is span

            self.hydrate_result(result, words, metad, **kwargs)
        self.words = words
        self.meta_dict = metad

    def hydrate_result(self, result, words, metad, no_completion=None, **kwargs):
        item, usage, span = result

        if item is None:
            # The categories.get_all selects from facts and outer joins activities
            # and categories, which will pick up Activities with no Category.
            # (lb): Which might be an issue in and of itself, but doesn't matter;
            # exclude these (erroneous?) records.
            return

        name = self.hydrate_name(item, **kwargs)
        if not self.check_filter(name, no_completion):
            return

        words.append(name)

        self.hydrate_result_usage(name, usage, span, metad)

    def hydrate_result_usage(self, name, usage, span, metad):
        if not usage or not span:
            return

        (
            tm_fmttd, tm_scale, tm_units,
        ) = PedanticTimedelta(days=span).time_format_scaled()

        metad[name] = _(
            'Used on {usage} {facts} for {time}: “{name}”'
        ).format(
            name=name,
            usage=usage,
            facts=Inflector(English).conditional_plural(usage, _('fact')),
            time=tm_fmttd,
        )

    def hydrate_name(self, item, **kwargs):
        return item.name

    def check_filter(self, name, no_completion):
        if not name:
            return False
        return not no_completion.search(name)

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

