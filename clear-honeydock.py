#/usr/bin/python3

import os
import time
import logging
from subprocess import Popen, PIPE, CalledProcessError
import netifaces as ni

logger = logging.getLogger()

interface = ''
local_ip = ''


def banner():
    subprocess.call("clear", shell=True)
    print()
    print("   _                                _            _     ")
    print("  | |                              | |          | |    ")
    print("  | |__   ___  _ __   ___ _   _  __| | ___   ___| | __ ")
    print("  | '_ \ / _ \| '_ \ / _ \ | | |/ _` |/ _ \ / __| |/ / ")
    print("  | | | | (_) | | | |  __/ |_| | (_| | (_) | (__|   <  ")
    print("  |_| |_|\___/|_| |_|\___|\__, |\__,_|\___/ \___|_|\_\ ")
    print("                           __/ |                       ")
    print("                          |___/                   v0.1 ")
    print()


def get_interface():
    global interface

    interface = [i for i in ni.interfaces() if i not in ['lo', 'docker0']][0]
    print("Interface:", interface)


def get_local_ip():
    global interface
    global local_ip

    local_ip = ni.ifaddresses(interface)[ni.AF_INET][0]['addr']
    print("Local IP:", local_ip)


def call(cmd):
    date = time.strftime("%d/%m/%Y - %H:%M:%S")
    if isinstance(cmd, str):
        cmd = cmd.split()

    try:
        out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    except CalledProcessError as err:
        logger.exception("[{date}] {err}".format(date=date, err=err))

    if err:
        logger.error("[{date}] {err}".format(err=err))
        return None
    return out.decode('utf-8') or True


def docker_stop(container_list):
    command = "docker stop"
    command = command.split() + container_list

    out = call(command)
    if out:
        print("Containers stopped!\n", out)
    else:
        print("Error stopping containers!")


def docker_rm(container_list):
    command = "docker rm"
    command = command.split() + container_list

    out = call(command)
    if out:
        print("Containers removed!\n", out)
    else:
        print("Error removing containers!")


def docker_cleaner():
    command = "docker ps -aq"
    print("Stopping all running dockers...")

    out = call(command)
    if out:
        container_list = out.split()
        docker_stop(container_list)
        docker_rm(container_list)
    else:
        print("Error getting containers id!")


def iptable_d(rule, command):
    print(rule)
    out = call(command)
    if out:
        print("{} removed!".format(rule))
    else:
        print("Error removing {rule}!".format(rule=rule))


def iptables_cleaner():
    global interface
    global local_ip

    print("Cleaning iptables rules...")

    iptable_d(
        "Rule #1: PREROUTING",
        "iptables -t nat -D PREROUTING -p tcp -d {local_ip} --dport 22 -j DNAT --to {local_ip}:22222".format(local_ip=local_ip)
    )
    iptable_d(
        "Rule #2: INPUT",
        "iptables -D INPUT -i {interface} -p tcp --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT".format(interface=interface)
    )
    iptable_d(
        "Rule #3: OUTPUT",
        "iptables -D OUTPUT -o {interface} -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT".format(interface=interface)
    )
    iptable_d(
        "Rule #4: FLAGS",
        "iptables -D OUTPUT -p tcp --tcp-flags SYN,ACK SYN,ACK -j LOG --log-prefix \"Connection established: \" "
    )
    print("Rules cleared!")


def honeydock_cleaner():
    banner()
    interface = get_interface()
    local_ip = get_local_ip()

    print("Cleaning process has started.")

    docker_cleaner()
    iptables_cleaner()

    print("Done!")


if __name__ == "__main__":
    honeydock_cleaner()
