import docker
from docker.errors import DockerException


try:
	client = docker.from_env()
	client.containers.run("ubuntu:latest", "sleep infinity", detach=True)
except (DockerException) as e:
	print(str(e))

