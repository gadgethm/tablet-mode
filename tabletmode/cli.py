"""Sets the system mode."""

from argparse import ArgumentParser, Namespace
from subprocess import DEVNULL
from subprocess import CalledProcessError
from subprocess import CompletedProcess
from subprocess import check_call
from subprocess import run
from sys import stderr
from typing import Optional

from tabletmode.config import load_config


DESCRIPTION = 'Sets or toggles the system mode.'
LAPTOP_MODE_SERVICE = 'laptop-mode.service'
TABLET_MODE_SERVICE = 'tablet-mode.service'
SUDO = '/usr/bin/sudo'


def get_args() -> Namespace:
    """Returns the CLI arguments."""

    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument(
        '-n', '--notify', action='store_true',
        help='display an on-screen notification')
    subparsers = parser.add_subparsers(dest='mode')
    subparsers.add_parser('toggle', help='toggles the system mode')
    subparsers.add_parser('laptop', help='switch to laptop mode')
    subparsers.add_parser('tablet', help='switch to tablet mode')
    subparsers.add_parser('default', help='do not disable any input devices')
    return parser.parse_args()


def systemctl(action: str, unit: str, *, root: bool = False,
              sudo: str = SUDO) -> bool:
    """Runs systemctl."""

    command = [sudo] if root else []
    command += ['systemctl', action, unit]

    try:
        check_call(command, stdout=DEVNULL)     # Return 0 on success.
    except CalledProcessError:
        return False

    return True

def set_osk_state(state: bool) -> bool:
    command = ['/usr/bin/gsettings', 'set', 'org.gnome.desktop.a11y.applications', 'screen-keyboard-enabled', str(state).lower()]
    try:
        check_call(command, stdout=DEVNULL)
    except CalledProcessError:
        return False
    
    return True

def notify_send(summary: str, body: Optional[str] = None) -> CompletedProcess:
    """Sends the respective message."""

    command = ['/usr/bin/notify-send', summary]

    if body is not None:
        command.append(body)

    return run(command, stdout=DEVNULL, check=False)


def notify_laptop_mode() -> CompletedProcess:
    """Notifies about laptop mode."""

    return notify_send('Laptop mode.', 'The system is now in laptop mode.')


def notify_tablet_mode() -> CompletedProcess:
    """Notifies about tablet mode."""

    return notify_send('Tablet mode.', 'The system is now in tablet mode.')


def default_mode(notify: bool = False, *, sudo: str = SUDO) -> None:
    """Restores all blocked input devices."""

    systemctl('stop', LAPTOP_MODE_SERVICE, root=True, sudo=sudo)
    systemctl('stop', TABLET_MODE_SERVICE, root=True, sudo=sudo)
    set_osk_state(False)

    if notify:
        notify_send('Default mode.', 'The system is now in default mode.')


def laptop_mode(notify: bool = False, *, sudo: str = SUDO) -> None:
    """Starts the laptop mode."""

    systemctl('stop', TABLET_MODE_SERVICE, root=True, sudo=sudo)
    systemctl('start', LAPTOP_MODE_SERVICE, root=True, sudo=sudo)
    set_osk_state(False)

    if notify:
        notify_laptop_mode()


def tablet_mode(notify: bool = False, *, sudo: str = SUDO) -> None:
    """Starts the tablet mode."""

    systemctl('stop', LAPTOP_MODE_SERVICE, root=True, sudo=sudo)
    systemctl('start', TABLET_MODE_SERVICE, root=True, sudo=sudo)
    set_osk_state(True)

    if notify:
        notify_tablet_mode()


def toggle_mode(notify: bool = False, *, sudo: str = SUDO) -> None:
    """Toggles between laptop and tablet mode."""

    if systemctl('status', TABLET_MODE_SERVICE):
        laptop_mode(notify=notify, sudo=sudo)
    else:
        tablet_mode(notify=notify, sudo=sudo)


def main() -> None:
    """Runs the main program."""

    args = get_args()
    config = load_config()
    notify = config.get('notify', False) or args.notify
    sudo = config.get('sudo', SUDO)

    if args.mode == 'toggle':
        toggle_mode(notify=notify, sudo=sudo)
    elif args.mode == 'default':
        default_mode(notify=notify, sudo=sudo)
    elif args.mode == 'laptop':
        laptop_mode(notify=notify, sudo=sudo)
    elif args.mode == 'tablet':
        tablet_mode(notify=notify, sudo=sudo)
    else:
        print('Must specify a mode.', file=stderr, flush=True)
