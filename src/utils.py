import logging
import netifaces
import time

from subprocess import Popen, PIPE, CalledProcessError
from typing import List, Tuple, Union

# Logging
logger = logging.getLogger(__name__)


def banner():
    """Clears the terminal and prints the banner"""

    command("clear")
    print(
        "\n"
        "  _                                _            _     \n"
        " | |                              | |          | |    \n"
        " | |__   ___  _ __   ___ _   _  __| | ___   ___| | __ \n"
        " | '_ \ / _ \| '_ \ / _ \ | | |/ _` |/ _ \ / __| |/ / \n"
        " | | | | (_) | | | |  __/ |_| | (_| | (_) | (__|   <  \n"
        " |_| |_|\___/|_| |_|\___|\__, |\__,_|\___/ \___|_|\_\ \n"
        "                          __/ |                       \n"
        "                         |___/                   v0.1 \n"
        "\n"
    )


def command(
    cmd: Union[str, List[str]],
    cmd_list: List[str]=list()
) -> Tuple[str, bool]:
    """Calls a shell command

    :param cmd: command
    :param cmd_list: extra command list
    :return:
    """

    date = time.strftime("%d/%m/%Y - %H:%M:%S")
    if isinstance(cmd, str):
        cmd = cmd.split()
    cmd += cmd_list
    print(f"cmd: { cmd }")
    try:
        out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    except CalledProcessError as e:
        logger.exception(f"[{ date }] { e }")

    if err:
        logger.error(f"[{ date }] { err }")
        return "", False
    return out.decode('utf-8'), True


def interfaces() -> List[str]:
    """Queries the network interfaces and returns an interface list

    :return: network interface list
    """
    return netifaces.interfaces()


def iptables_cleaner() -> None:
    """Remove all rules"""

    logger.info("Cleaning iptables rules...")
    command("iptables -F")
    command("iptables -t nat -F")
    command("systemctl restart docker.service")
    logger.info("Rules cleared!")


def get_local_ip(interface: str) -> str:
    """Queries the network interface and returns local IP

    :param interface: network interface
    :return: local IP
    """
    addresses = netifaces.ifaddresses(interface)
    address = addresses[netifaces.AF_INET][0]
    local_ip = address.get('addr')
    return local_ip
