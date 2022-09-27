# This file exists within 'dob-prompt':
#
#   https://github.com/tallybark/dob-prompt

"""
Packaging instruction for setup tools.

Refs:

  https://setuptools.readthedocs.io/

  https://packaging.python.org/en/latest/distributing.html

  https://github.com/pypa/sampleproject
"""

from setuptools import find_packages, setup

# *** Package requirements.

requirements = [
    # https://github.com/pytest-dev/apipkg
    'apipkg >= 1.5, < 2',
    # Vocabulary word pluralizer.
    #  https://github.com/ixmatus/inflector
    'Inflector >= 3.0.1, < 4',
    # Amazing prompt library.
    # - Imports as prompt_toolkit.
    # https://github.com/prompt-toolkit/python-prompt-toolkit
    'prompt-toolkit >= 3.0.5, < 4',

    # *** HOTH packages.

    # ActiveState/appdirs + Singleton (app-wide access w/out appname) + `mkdir -p`.
    #  https://github.com/doblabs/easy-as-pypi-appdirs#🛣
    'easy-as-pypi-appdirs',
    # Get-package-or-Git-version helper.
    #  https://github.com/tallybark/easy-as-pypi-getver
    'easy-as-pypi-getver',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    # - Imports as `pedantic_timedelta`.
    # https://github.com/hotoffthehamster/human-friendly_pedantic-timedelta
    'human-friendly_pedantic-timedelta > 2.0.11, < 2.0.13',

    # The heart of Hamster. (Ye olde `hamster-lib`).
    #  https://github.com/tallybark/nark
    'nark > 3.2.3, < 3.2.5',  # I.e., release 3.2.4, or whatever dev's running.
    # The controller, config, and common output and error tossing code.
    #  https://github.com/tallybark/dob-bright
    'dob-bright > 1.2.4, < 1.2.6',  # I.e., release 1.2.5, or dev's intermediate.
]

# *** Minimal setup() function -- Prefer using config where possible.

# (lb): Most settings are in setup.cfg, except identifying packages.
# (We could find-packages from within setup.cfg, but it's convoluted.)

setup(
    # Run-time dependencies installed on `pip install`. To learn more
    # about "install_requires" vs pip's requirements files, see:
    #   https://packaging.python.org/en/latest/requirements.html
    install_requires=requirements,

    # Specify which package(s) to install.
    # - Without any rules, find_packages returns, e.g.,
    #     ['dob_prompt', 'tests', 'tests.dob_prompt']
    # - With the 'exclude*' rule, this call is essentially:
    #     packages=['dob_prompt']
    packages=find_packages(exclude=['tests*']),

    # Tell setuptools to determine the version
    # from the latest SCM (git) version tag.
    #
    # Note that if the latest commit is not tagged with a version,
    # or if your working tree or index is dirty, then the version
    # from git will be appended with the commit hash that has the
    # version tag, as well as some sort of 'distance' identifier.
    # E.g., if a project has a '3.0.0a21' version tag but it's not
    # on HEAD, or if the tree or index is dirty, the version might
    # be:
    #   $ python setup.py --version
    #   3.0.0a22.dev3+g6f93d8c.d20190221
    # But if you clean up your working directory and move the tag
    # to the latest commit, you'll get the plain version, e.g.,
    #   $ python setup.py --version
    #   3.0.0a31
    # Ref:
    #   https://github.com/pypa/setuptools_scm
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
)

