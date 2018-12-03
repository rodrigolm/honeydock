import json
import logging

from typing import List, Tuple

from utils import command

# Logging
logger = logging.getLogger(__name__)


def docker_cleaner() -> None:
    """Stop and remove all docker containers"""

    cmd = "docker ps -aq"
    out, ok = command(cmd)
    if ok:
        container_list = out.split()
        print("Stopping all running docker containers...")
        docker_stop(container_list)
        print("Removing all docker containers...")
        docker_rm(container_list)
    else:
        print("Error getting container id list!")


def docker_host_port(container: str) -> dict:
    """Get docker container host port

    :param container: docker container id
    :return: docker container host port
    """

    host_post = dict()
    cmd = "docker inspect -f"
    out, ok = command(cmd, [r"{{json .NetworkSettings.Ports}}", container])
    if ok:
        port_dict = json.loads(out)
        for port in port_dict.keys():
            local_port = port.split('/')[0]
            host_post[local_port] = port_dict[port][0]['HostPort']
    return host_post


def docker_rm(container_list: List[str]) -> None:
    """Remove all docker containers

    :param container_list: docker container id list
    """

    cmd = "docker rm"
    out, ok = command(cmd, container_list)
    if ok:
        print("Containers removed!\n", out)
    else:
        print("Error removing containers!")


def docker_run(
    image: str,
    image_cmd: str="",
    network: str="",
    options: str=""
) -> Tuple[str, bool]:
    """Run a container docker

    :param image: docker image
    :param image_cmd: command for image
    :param network: docker network config
    :param options: extra options
    :return: docker container id
    """

    cmd = f"docker run -d -P { network } { options } { image } { image_cmd }"
    out, ok = command(cmd)
    if out:
        print("Container created!\n", out)
        return out[:12], True
    else:
        print("Error creating container!")
        return "", False


def docker_stop(container_list: List[str]) -> None:
    """Stop all docker containers

    :param container_list: docker container id list
    """

    cmd = "docker stop"
    out, ok = command(cmd, container_list)
    if ok:
        print("Containers stopped!\n", out)
    else:
        print("Error stopping containers!")
