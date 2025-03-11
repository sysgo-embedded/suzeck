import docker
from docker.errors import DockerException

try:
	client = docker.from_env()
	if len(client.containers.list())==0:
		print("----Container list is empty------")
	else:
		print ("----- CONTAINER LIST-------")
		for container in client.containers.list():
			print(container.name)
		
		print("----- STOPPING ACTIVE CONTAINERS------")
		for container in client.containers.list():
			container.stop()
			
		print ("----- CONTAINER LIST-------")
		if len(client.containers.list())==0:
			print("----Container list is empty------")
		else:
			for container in client.containers.list():
				print(container.name)
			
except (DockerException, Exception) as e:
	print(str(e))


