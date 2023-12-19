# This file exists within 'dob-prompt':
#
#   https://github.com/tallybark/dob-prompt
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

from nark.items.activity import Activity

from dob_bright.crud.interrogate import ask_edit_with_editor

# Lazy-load AwesomePrompt to save ~0.1 seconds when not needed.
from dob_prompt import prompters

__all__ = (
    'ask_user_for_edits',
)


# ***

def ask_user_for_edits(
    controller,
    fact,
    always_ask=False,
    prompt_agent=None,
    restrict_edit='',
    no_completion=None,
):
    """
    """

    def _ask_user_for_edits():
        verify_always_ask()

        prompter = get_prompter()

        ask_act_cat(prompter, fact)

        ask_for_tags(prompter, fact)

        fact_ask_description(fact)

        return prompter

    # ***

    def verify_always_ask():
        assert always_ask in [
            True, False, 'actegory', 'tags', 'description',
        ]

    # ***

    def get_prompter():
        if prompt_agent is None:
            return prompters.path.AwesomePrompt(controller)
        else:
            assert isinstance(prompt_agent, prompters.path.PrompterCommon)
            return prompt_agent

    # ***

    def ask_act_cat(prompter, fact):
        filter_activity, filter_category = prepare_ask_act_cat(fact)
        if (
            (filter_activity and filter_category and always_ask is False)
            or ('' != restrict_edit and 'actegory' != restrict_edit)
        ):
            return

        no_completion_act = None
        no_completion_cat = None
        if no_completion is not None:
            no_completion_act = no_completion.re_act
            no_completion_cat = no_completion.re_cat

        act_name, cat_name = prompter.ask_act_cat(
            filter_activity,
            filter_category,
            no_completion_act=no_completion_act,
            no_completion_cat=no_completion_cat,
        )
        set_actegory(fact, act_name, cat_name)

    def prepare_ask_act_cat(fact):
        filter_activity = ''
        if fact.activity and fact.activity.name:
            filter_activity = fact.activity.name

        filter_category = ''
        if fact.activity and fact.activity.category and fact.activity.category.name:
            filter_category = fact.activity.category.name

        return filter_activity, filter_category

    def set_actegory(fact, act_name, cat_name):
        fact.activity = Activity.create_from_composite(act_name, cat_name)
        try:
            fact.activity = controller.activities.get_by_composite(
                fact.activity.name, fact.activity.category, raw=False,
            )
        except KeyError:
            pass

    # ***

    def ask_for_tags(prompter, fact):
        if (
            (fact.tags and always_ask is False)
            or ('' != restrict_edit and 'tags' != restrict_edit)
        ):
            return

        no_complete_tag = None
        if no_completion is not None:
            no_complete_tag = no_completion.re_tag

        chosen_tags = prompter.ask_for_tags(
            already_selected=fact.tags,
            activity=fact.activity,
            no_completion=no_complete_tag,
        )
        fact.tags_replace(chosen_tags)

    # ***

    def fact_ask_description(fact):
        if (
            (fact.description and always_ask is False)
            or ('' != restrict_edit and 'description' != restrict_edit)
        ):
            return

        # (lb): Strip whitespace from the description. This is how `git` works.
        # Not that we have to be like git. But it makes parsed results match
        # the input, i.e., it we didn't strip() and then re-parsed the non-
        # stripped description, the parser would strip, and we'd see a difference
        # between the pre-parsed and post-parsed description, albeit only
        # leading and/or trailing whitespace. (If we wanted to preserve whitespace,
        # we'd have to make the parser a little more intelligent, but currently
        # the parser strip()s while it parses, to simplify the parsing algorithm.)
        raw_description = ask_edit_with_editor(controller, fact, fact.description)
        if raw_description is not None:
            fact.description = raw_description.strip()

    # ***

    return _ask_user_for_edits()

