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

from .prompt_actegory import PromptForActegory
from .prompt_tagcloud import PromptForMoreTags
from .prompter_common import PrompterCommon

__all__ = (
    'AwesomePrompt',
)


class AwesomePrompt(PrompterCommon):
    """
    """

    def __init__(self, controller):
        super(AwesomePrompt, self).__init__()
        self.prompt_actegory = PromptForActegory(controller)
        self.prompt_for_tags = PromptForMoreTags(controller)

    def ask_act_cat(self, *args, **kwargs):
        return self.prompt_actegory.ask_act_cat(*args, **kwargs)

    def ask_for_tags(self, *args, **kwargs):
        return self.prompt_for_tags.ask_for_tags(*args, **kwargs)

