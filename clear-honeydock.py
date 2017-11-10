#/usr/bin/python3

import os
import time
import logging
import subprocess
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

def docker_stop(container_list):
    command = "docker stop"

    try:
        subprocess.call(command.split() + container_list)
        print("Containers stopped.")
    except subprocess.CalledProcessError:
        now = time.strftime("[%d/%m/%Y - %H:%M:%S]")
        logger.exception("{} error stopping containers".format(now))

def docker_rm(container_list):
    command = "docker rm"

    try:
        subprocess.call(command.split() + container_list)
        print("Containers removed.")
    except subprocess.CalledProcessError:
        now = time.strftime("[%d/%m/%Y - %H:%M:%S]")
        logger.exception("{} error removing containers".format(now))

def docker_cleaner():
    command = "docker ps -aq"

    print("Stopping all running dockers...")

    try:
        container_list = subprocess.check_output(command.split())
        container_list = container_list.decode('utf-8')
        if container_list:
            container_list = container_list.split()
            docker_stop(container_list)
            docker_rm(container_list)
    except subprocess.CalledProcessError:
        now = time.strftime("[%d/%m/%Y - %H:%M:%S]")
        logger.exception("{} error getting containers id".format(now))

def iptable_d(rule, command):
    print(rule)

    try:
        subprocess.call(command.split(), stderr=subprocess.STDOUT, shell=True)
        print("{} removed.".format(rule))
    except subprocess.CalledProcessError:
        now = time.strftime("[%d/%m/%Y - %H:%M:%S]")
        logger.exception("{date} error removing {rule}".format(date=now, rule=rule))


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
    print("Rules cleared.")


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
