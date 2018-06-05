#!/usr/bin/env python3

# TODO import argparse  #  https://docs.python.org/3/library/argparse.html
import logging
import pyinotify
import re
import sqlite3

from .docker import docker_host_port, docker_run
from .utils import banner, command, get_local_ip

# Honeypot Config
HONEYPOT_DOCKER_IMAGE = "cowrie/cowrie"
HONEYPOT_DOCKER_IMAGE_CMD = ""
HONEYPOT_DOCKER_OPTIONS = \
    "-e 'DOCKER=yes' -v $(PROJECT_PATH)/honeypot/cowrie/cowrie.cfg:/cowrie/cowrie-git/cowrie.cfg"
HONEYPOT_DOCKER_SERVICE_PORT = "2222"
HONEYPOT_SERVICE_PORT = "22"

# Global Variables
CURRENT_CONTAINER = None
INTERFACE = "enp0s3"
KERN_LOG_PATH = "/var/log/kern.log"
KERN_LOG_CONTENT = open(KERN_LOG_PATH, 'r').readlines()
KERN_LOG_LEN = len(KERN_LOG_CONTENT)

# Pyinotify
WATCH_MANAGER = pyinotify.WatchManager()

# Open database connection
DB = sqlite3.connect("honeydock.db")
CONN = DB.cursor()


# Logging
logger = logging.getLogger(__name__)
logging.root.handlers = []
logging.basicConfig(
    format="[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s",
    level=logging.DEBUG,
    filename="honeydock.log"
)

# Create a console handler
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)

# Create a logging format
formatter = logging.Formatter("[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s")
console.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(console)


def attacker_exists(ip):
    """Check if a attacker exists"""

    CONN.execute(f"SELECT ip FROM attacker WHERE ip='{ ip }' LIMIT 1")
    rows = CONN.fetchall()
    return len(rows) == 1


def create_attacker(ip, container):
    """Create a attacker"""

    CONN.execute(f"INSERT INTO attacker (ip, container) VALUES ('{ ip }', '{ container }')")
    return db_commit()


def create_container() -> str or bool:
    """Create a container with a honeypot docker image

    :return: get container host port or false
    """

    container, created = docker_run(
        image=HONEYPOT_DOCKER_IMAGE,
        image_cmd=HONEYPOT_DOCKER_IMAGE_CMD,
        options=HONEYPOT_DOCKER_OPTIONS
    )
    return container if created else created


def create_table() -> None:
    """Create a table attacker"""

    CONN.execute('''
        CREATE TABLE attacker (
            ip text,
            container text
        )
    ''')
    return db_commit()


def db_commit() -> bool:
    """Commit operation in database"""

    try:
        DB.commit()
        return True
    except sqlite3.Error:
        DB.rollback()
        return False


class EventHandler(pyinotify.ProcessEvent):

    def __init__(self, file_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_path = file_path
        self._last_position = 0
        logpats = r'I2G\(JV\)'
        self._logpat = re.compile(logpats)

    def process_IN_MODIFY(self, event):
        global CURRENT_CONTAINER
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
            if "Connection established:" in log:
                attacker_ip = (re.search(r'DST=(.*?) ', log)).group(1)

                logger.debug("New connection was established!")
                logger.debug(f"Connection detail: { log }")
                logger.debug(f"Attacker ({ attacker_ip }) on SSH service!")
                if not attacker_exists(attacker_ip):
                    logger.info(f"The IP: { attacker_ip } it's from a new attacker")
                    # send_email_alert(attacker_ip, 1)
                    # logger.info("E-mail alert sent.")
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
                    container = create_container()
                    CURRENT_CONTAINER = container
                    host_port = docker_host_port(container)[HONEYPOT_DOCKER_SERVICE_PORT]
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
                        f"The IP: { attacker_ip } it's from a returning attacker. "
                        "No action required"
                    )
                    # send_email_alert(attacker_ip, 2)


if __name__ == "__main__":
    global CURRENT_CONTAINER

    banner()
    logger.info("Initializing...")

    logger.info("Starting base docker")
    container = create_container()
    CURRENT_CONTAINER = container
    host_port = docker_host_port(container)[HONEYPOT_DOCKER_SERVICE_PORT]
    logger.info("SSH base docker has started")

    logger.info("Creating initial iptables rules...")
    local_ip = get_local_ip(INTERFACE)
    command(
        "iptables -t nat -A PREROUTING -p tcp "
        f"-d { local_ip } "
        f"--dport { HONEYPOT_SERVICE_PORT } "
        "-j DNAT "
        f"--to { local_ip }:{ host_port }"
    )
    command(
        f"iptables -A INPUT "
        "-i { INTERFACE } "
        "-p tcp "
        f"--dport { HONEYPOT_SERVICE_PORT } "
        "-m state "
        "--state NEW,ESTABLISHED "
        "-j ACCEPT"
    )
    command(
        f"iptables -A OUTPUT "
        "-o { INTERFACE } "
        "-p tcp "
        f"--sport { HONEYPOT_SERVICE_PORT } "
        "-m state "
        "--state ESTABLISHED "
        "-j ACCEPT"
    )
    command(
        "iptables -A OUTPUT "
        "-p tcp "
        "--tcp-flags SYN,ACK SYN,ACK "
        "-j LOG "
        "--log-prefix \"Connection established: \" "
    )
    logger.info("Rules created. Honeydock is ready to go. :)")

    handler = EventHandler(KERN_LOG_PATH)
    notifier = pyinotify.Notifier(WATCH_MANAGER, handler)
    WATCH_MANAGER.add_watch(handler.file_path, pyinotify.IN_MODIFY)
    notifier.loop()
