"""System mode daemon."""
from argparse import ArgumentParser, Namespace
from logging import DEBUG, INFO, basicConfig, getLogger
from subprocess import Popen
from typing import Iterable

from tabletmode.config import load_config


DESCRIPTION = 'Setup system for laptop or tablet mode.'
EVTEST = '/usr/bin/evtest'
GSETTINGS = '/usr/bin/gsettings'
GNOME_OSK =  'set org.gnome.desktop.a11y.applications screen-keyboard-enabled'
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger('sysmoded')


def get_args() -> Namespace:
    """Parses the CLI arguments."""

    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='turn on verbose logging')
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.add_parser('laptop', help='enable laptop mode')
    subparsers.add_parser('tablet', help='enable tablet mode')
    return parser.parse_args()


def set_osk_state(mode: str) -> None:
    """Toggles on-screen keyboard for gnome"""

    return Popen((GSETTINGS, f"{GNOME_OSK} {str(mode == 'tablet').lower()}"))


def disable_device(device: str) -> Popen:
    """Disables the respective device via evtest."""

    return Popen((EVTEST, '--grab', device))


def set_mode(mode: str) -> None:
    """Disables the given devices."""

    devices = get_devices(mode)
    subprocesses = []
    subprocesses.append(set_osk_state(mode))

    for device in devices:
        subprocess = disable_device(device)
        subprocesses.append(subprocess)

    for subprocess in subprocesses:
        subprocess.wait()


def get_devices(mode: str) -> Iterable[str]:
    """Reads the device from the config file."""

    config = load_config()
    devices = config.get(mode) or ()

    if not devices:
        LOGGER.info('No devices configured to disable.')

    return devices


def main():
    """Runs the main program."""

    arguments = get_args()
    level = DEBUG if arguments.verbose else INFO
    basicConfig(level=level, format=LOG_FORMAT)

    set_mode(arguments.mode)
