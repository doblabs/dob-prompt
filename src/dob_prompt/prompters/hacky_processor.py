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

from prompt_toolkit.layout.processors import Processor, Transformation

__all__ = (
    'HackyProcessor',
)


class HackyProcessor(Processor):
    """
    A `Processor` that kludges updating the bottom bar according to whether
    the completion list is showing. (lb): Because I couldn't figure out how
    else to hook the showing/hiding of the completion list.
    """

    def __init__(self, prompt):
        super(HackyProcessor, self).__init__()
        self.prompt = prompt
        self.start_completion = False

    def __repr__(self):
        return (
            '<{}.HackyProcessor at 0x{}'.format(
                self.__name__, hex(id(self)),
            )
        )

    def apply_transformation(self, transformation_input):
        self.mark_summoned(transformation_input)
        self.prompt.heartbeat()
        return Transformation(transformation_input.fragments)

    def mark_summoned(self, transformation_input):
        # (lb): This is such a hack! This is called on prompt startup,
        # and it's the only hook I've figured to use so far to do things
        # that I cannot otherwise do through the session construction, or
        # the prompt method.

        complete_state = self.prompt.session.app.current_buffer.complete_state

        # *** Optional: Show completions drop down on prompt startup.

        # HISTORIC: (lb): The act@gory prompt used to be called twice
        # successively, once to get the Activity name, and once to get
        # the Category name. Before the second prompt session, the code
        # would ask that the completion dropdown be shown immediately:
        #     processor.start_completion = True
        # I've since made the act@gory Awesome Prompt gather both the
        # Activity and Category names in the same prompt session, so
        # this behavior is no longer exhibited, but the code remains
        # right here to start with the completions dropdown visible.

        if not complete_state and self.start_completion:
            self.start_completion = False
            transformation_input.buffer_control.buffer.start_completion()

        # *** Optional: Hook completions drop down showing and hiding.

        # HACKTASTIC: (lb): Our prompter tracks the completions "signal edge".
        # Specifically, the prompter (more specifically, the validator) cares
        # when the completions dropdown is hidden, so that it can parse the
        # input text for the separator ('@') to fiddle with the input state
        # (which is either asking for the Activity name or asking for the
        # Category name).
        #
        # Within PPT itself, there's a callback, on_completions_changed, but
        # we cannot influence or access that feature via the PromptSession
        # interface that Awesome Prompt uses. So we report the state of the
        # completions dropdown to our prompter, and our prompter tracks the
        # signal edge (transitions from hiding to showing, and vice versa).
        # (Note that apply_transformation is called many times per input
        # character handled, so it's up to the prompter to only react when
        # the completions state changes, and not on every summoned() call.)

        # *** UX: Update Bottom Bar to accommodate completions drop down.

        # (lb): In addition to watching for completions dropdown state changes,
        # our prompter also rebuilds the PPT session's bottom_toolbar, whose
        # state also depends on whether completions are showing or not.

        showing_completions = complete_state is not None
        self.prompt.summoned(showing_completions=showing_completions)

