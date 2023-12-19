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

from contextlib import closing

import pytest
from prompt_toolkit.application.current import create_app_session
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.output import DummyOutput

# Import 'activity' fixture, etc.
from nark.tests.item_factories import *  # noqa: F401, F403

from dob_prompt import prompters

# FIXME/2020-01-31: (lb): Change all the key_sequence lists below!
# - I copied this from dob-viewer/dob_viewer/tests/test_carousel.py
#   and only swapped out the Carousel for the Awesome Prompts; I did
#   not change the input! Still, dob-prompt went from 0% coverage all
#   the way to 73%, so, whatever, good ROI for a quick hack job!


class TestBasicCarousel(object):
    """Non-interactive Interactive Carousel tests."""

    # ***

    def _feed_cli_with_input(
        self,
        controller_with_logging,
        input_text,
        activity,
        mocker,
    ):
        inp_gen = create_pipe_input()
        with closing(next(inp_gen.gen)) as inp:
            inp.send_text(input_text)
            with create_app_session(input=inp, output=DummyOutput()):
                prompter = prompters.path.AwesomePrompt(controller_with_logging)
                #
                # (lb): Not sure why the linter doesn't flag F841 on these
                #       two return vars, maybe because it's a list?
                act_name, cat_name = prompter.ask_act_cat(
                    filter_activity="",
                    filter_category="",
                    no_completion_act=None,
                    no_completion_cat=None,
                )
                #
                chosen_tags = prompter.ask_for_tags(  # noqa: F841 local never used
                    already_selected=[],
                    activity=activity,
                    no_completion=None,
                )

    # ***

    @pytest.mark.parametrize(
        ("key_sequence"),
        [
            # Test left-arrowing and first (early Life) gap fact.
            # Left arrow three times.
            # - First time creates and jumps to gap fact.
            # - Second time causes at-first-fact message.
            # - Third time's a charm.
            [
                "\x1bOD",  # Left arrow ←.
                "\x1bOD",  # Left arrow ←.
                "\x1bOD",  # Left arrow ←.
                "\x11",  # Ctrl-Q.
                "\x11",  # Ctrl-Q.
                "\x11",  # Ctrl-Q.
            ],
        ],
    )
    def test_basic_import4_left_arrow_three_time(
        self,
        controller_with_logging,
        key_sequence,
        activity,
        mocker,
    ):
        input_text = "".join(key_sequence)
        self._feed_cli_with_input(
            controller_with_logging,
            input_text,
            activity,
            mocker,
        )

    # ***

    @pytest.mark.parametrize(
        ("key_sequence"),
        [
            [
                # Arrow right, arrow left.
                "\x1bOD",
                "\x1bOC",
                # Three Cancels don't make a Right.
                "\x11",
                "\x11",
                "\x11",
                # FIXME/2019-02-20: Because, what, arrowing left goes to
                #                   Previous Big Bang Gap Fact,
                #                   so extra Ctrl-Q needed?
                #                   Oddly, in log, I still only see 2 exit_command's!
                #                   But apparently we need 4 strokes to exit.
                "\x11",
            ],
        ],
    )
    def test_basic_import4_right_arrow_left_arrow(
        self,
        controller_with_logging,
        key_sequence,
        activity,
        mocker,
    ):
        input_text = "".join(key_sequence)
        self._feed_cli_with_input(
            controller_with_logging,
            input_text,
            activity,
            mocker,
        )

    # ***

    @pytest.mark.parametrize(
        ("key_sequence"),
        [
            [
                # Jump to final fact.
                "G",
                "\x11",
                "\x11",
                "\x11",
            ],
        ],
    )
    def test_basic_import4_G_go_last(
        self,
        controller_with_logging,
        key_sequence,
        activity,
        mocker,
    ):
        input_text = "".join(key_sequence)
        self._feed_cli_with_input(
            controller_with_logging,
            input_text,
            activity,
            mocker,
        )
