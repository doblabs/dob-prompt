############
Installation
############

.. vim:tw=0:ts=3:sw=3:et:norl:nospell:ft=rst

.. |virtualenv| replace:: ``virtualenv``
.. _virtualenv: https://virtualenv.pypa.io/en/latest/

.. |workon| replace:: ``workon``
.. _workon: https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html?highlight=workon#workon

To install system-wide, run as superuser::

    $ pip3 install dob-prompt

To install user-local, simply run::

    $ pip3 install -U dob-prompt

To install within a |virtualenv|_, try::

    $ cd "$(mktemp -d)"

    $ python3 -m venv .venv

    $ . ./.venv/bin/activate

    (dob-prompt) $ pip install dob-prompt

To develop on the project, link to the source files instead::

    (dob-prompt) $ deactivate
    $ git clone git@github.com:doblabs/dob-prompt.git
    $ cd dob-prompt
    $ python3 -m venv dob-prompt
    $ . ./.venv/bin/activate
    (dob-prompt) $ make develop

After creating the virtual environment, it's easy to start
developing from a fresh terminal::

    $ cd dob-prompt
    $ . ./.venv/bin/activate
    (dob-prompt) $ ...

