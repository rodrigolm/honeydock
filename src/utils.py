import logging
import netifaces
import time

from subprocess import Popen, PIPE, CalledProcessError
from typing import List

from .docker import docker_cleaner

logger = logging.getLogger(__name__)


def banner():
    """Clears the terminal and prints the banner"""

    command("clear")
    print(
        ""
        "  _                                _            _     "
        " | |                              | |          | |    "
        " | |__   ___  _ __   ___ _   _  __| | ___   ___| | __ "
        " | '_ \ / _ \| '_ \ / _ \ | | |/ _` |/ _ \ / __| |/ / "
        " | | | | (_) | | | |  __/ |_| | (_| | (_) | (__|   <  "
        " |_| |_|\___/|_| |_|\___|\__, |\__,_|\___/ \___|_|\_\ "
        "                          __/ |                       "
        "                         |___/                   v0.1 "
        ""
    )


def command(cmd: str or List[str]) -> str or bool:
    """Calls a shell command

    :param cmd: command
    :return:
    """

    date = time.strftime("%d/%m/%Y - %H:%M:%S")
    if isinstance(cmd, str):
        cmd = cmd.split()

    try:
        out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    except CalledProcessError as err:
        logger.exception("[{date}] {err}".format(date=date, err=err))

    if err:
        logger.error("[{date}] {err}".format(err=err))
        return False
    return out.decode('utf-8') or True


def interfaces() -> List[str]:
    """Queries the network interfaces and returns an interface list

    :return: network interface list
    """
    return netifaces.interfaces()


def iptables_cleaner() -> None:
    """Remove all rules"""

    print("Cleaning iptables rules...")
    command("iptables -P INPUT ACCEPT")
    command("iptables -P OUTPUT ACCEPT")
    command("iptables -t nat -F")
    command("iptables -F")
    command("iptables -X")
    print("Rules cleared!")


def get_local_ip(interface: str) -> str:
    """Queries the network interface and returns local IP

    :param interface: network interface
    :return: local IP
    """
    addresses = netifaces.ifaddresses(interface)
    address = addresses[netifaces.AF_INET][0]
    local_ip = address.get('addr')
    return local_ip


def honeydock_cleaner(interface: str) -> None:
    banner()
    print("Cleaning process has started.")
    docker_cleaner()
    iptables_cleaner()
    print("Done!")
