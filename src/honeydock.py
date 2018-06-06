#!/usr/bin/env python3

# TODO import argparse  #  https://docs.python.org/3/library/argparse.html
import logging
import re
import sqlite3

from pyinotify import (
    IN_MODIFY,
    Notifier,
    ProcessEvent,
    WatchManager
)
from typing import Union

from .docker import docker_host_port, docker_run
from .utils import banner, command, get_local_ip


# Honeypot Config
HONEYPOT_DOCKER_IMAGE = "cowrie/cowrie"
HONEYPOT_DOCKER_IMAGE_CMD = ""
HONEYPOT_DOCKER_OPTIONS = \
    "-e 'DOCKER=yes' -v $(HOME)/honeydock/honeypot/cowrie/cowrie.cfg:/cowrie/cowrie-git/cowrie.cfg"
HONEYPOT_DOCKER_SERVICE_PORT = "2222"
HONEYPOT_SERVICE_PORT = "22"


# Global Variables
CURRENT_CONTAINER = None
INTERFACE = "enp0s3"
KERN_LOG_PATH = "/var/log/kern.log"
KERN_LOG_CONTENT = open(KERN_LOG_PATH, 'r').readlines()
KERN_LOG_LEN = len(KERN_LOG_CONTENT)


# Open database connection
DB = sqlite3.connect("honeydock.db")
CONN = DB.cursor()


# Logging
logging.config.fileConfig(filename='honeydock.log')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to console
console.setFormatter(formatter)

# add console to logger
logger.addHandler(console)


# Database

def attacker_exists(ip: str) -> bool:
    """Check if a attacker exists

    :param ip: attacker ip
    :return: if the attacker is registered
    """

    CONN.execute(f"SELECT ip FROM attacker WHERE ip='{ ip }' LIMIT 1")
    rows = CONN.fetchall()
    return len(rows) == 1


def create_attacker(ip: str, container: str) -> bool:
    """Create a attacker

    :param ip: attacker ip
    :param container: docker container id
    :return: if the attacker was successfully registered
    """

    CONN.execute(f"INSERT INTO attacker (ip, container) VALUES ('{ ip }', '{ container }')")
    return db_commit()


def create_table() -> bool:
    """Create a table attacker

    :return: if the table was created successfully
    """

    CONN.execute('''
        CREATE TABLE attacker (
            ip text,
            container text
        )
    ''')
    return db_commit()


def db_commit() -> bool:
    """Commit operation in database

    :return: if the transaction in the database was made successfully
    """

    try:
        DB.commit()
        return True
    except sqlite3.Error:
        DB.rollback()
        return False


# Container

def create_container() -> Union[str, bool]:
    """Create a container with a honeypot docker image

    :return: get container id or false
    """
    global CURRENT_CONTAINER

    container, created = docker_run(
        image=HONEYPOT_DOCKER_IMAGE,
        image_cmd=HONEYPOT_DOCKER_IMAGE_CMD,
        options=HONEYPOT_DOCKER_OPTIONS
    )
    CURRENT_CONTAINER = container
    return container if created else created


class EventHandler(ProcessEvent):

    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self._last_position = 0
        logpats = r'I2G\(JV\)'
        self._logpat = re.compile(logpats)

    def process_IN_MODIFY(self, event):
        global KERN_LOG_CONTENT
        global KERN_LOG_LEN

        if not CURRENT_CONTAINER:
            return

        local_ip = get_local_ip(INTERFACE)
        loglines = open(self.file_path, 'r').readlines()
        loglines_len = len(loglines)
        diff = loglines_len - KERN_LOG_LEN
        changes = loglines[-diff:]

        KERN_LOG_CONTENT = open(KERN_LOG_PATH, 'r').readlines()
        KERN_LOG_LEN = len(KERN_LOG_CONTENT)

        for log in changes:
            if "Connection established:" not in log:
                continue

            attacker_ip = (re.search(r'DST=(.*?) ', log)).group(1)

            logger.debug("New connection was established!")
            logger.debug(f"Connection detail: { log }")
            logger.debug(f"Attacker ({ attacker_ip })")
            if not attacker_exists(attacker_ip):
                logger.info(f"The IP: { attacker_ip } it's from a new attacker")
                created = create_attacker(attacker_ip, CURRENT_CONTAINER)
                if not created:
                    return

                logger.info(f"The IP: { attacker_ip } was added on attacker's table")
                logger.info("Initiating proccess of attaching this IP to a docker instance")
                logger.info("Removing main rule")
                host_port = docker_host_port(CURRENT_CONTAINER)[HONEYPOT_DOCKER_SERVICE_PORT]
                command(
                    "iptables -t nat -D PREROUTING -p tcp "
                    f"-d { local_ip } "
                    f"--dport { HONEYPOT_SERVICE_PORT } "
                    "-j DNAT "
                    f"--to { local_ip }:{ host_port }"
                )
                logger.info("Attaching this IP to container")
                command(
                    "iptables -t nat -A PREROUTING -p tcp "
                    f"-s { attacker_ip } "
                    f"-d { local_ip } "
                    f"--dport { HONEYPOT_SERVICE_PORT } "
                    "-j DNAT "
                    f"--to { local_ip }:{ host_port }"
                )

                logger.info("Creating a new docker instance")
                create_container()
                host_port = docker_host_port(CURRENT_CONTAINER)[HONEYPOT_DOCKER_SERVICE_PORT]
                logger.info(f"New docker container created on port { host_port }")

                logger.info("Creating main rule to new docker")
                command(
                    "iptables -t nat -A PREROUTING -p tcp "
                    f"-d { local_ip } "
                    f"--dport { HONEYPOT_SERVICE_PORT } "
                    "-j DNAT "
                    f"--to { local_ip }:{ host_port }"
                )
                logger.info("Done!")
            else:
                logger.info(
                    f"The IP: { attacker_ip } it's from a returning attacker. No action required"
                )


if __name__ == "__main__":
    banner()
    logger.info("Initializing...")

    logger.info("Starting base docker")
    create_container()
    host_port = docker_host_port(CURRENT_CONTAINER)[HONEYPOT_DOCKER_SERVICE_PORT]
    logger.info("Base docker has started")

    logger.info("Creating initial iptables rules...")
    local_ip = get_local_ip(INTERFACE)
    command(
        f"iptables -t nat -A PREROUTING "
        "-m state "
        "--state NEW,ESTABLISHED "
        "-j ACCEPT"
    )
    command(
        "iptables -t nat -A PREROUTING -p tcp "
        f"-d { local_ip } "
        f"--dport { HONEYPOT_SERVICE_PORT } "
        "-j LOG "
        "--log-prefix \"Connection established: \" "
    )
    command(
        "iptables -t nat -A PREROUTING -p tcp "
        f"-d { local_ip } "
        f"--dport { HONEYPOT_SERVICE_PORT } "
        "-j DNAT "
        f"--to { local_ip }:{ host_port }"
    )
    logger.info("Rules created. Honeydock is ready to go. :)")

    handler = EventHandler(KERN_LOG_PATH)
    watch_manager = WatchManager()
    watch_manager.add_watch(handler.file_path, IN_MODIFY)
    notifier = Notifier(watch_manager, handler)
    notifier.loop()