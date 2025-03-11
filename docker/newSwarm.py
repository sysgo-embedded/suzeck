import docker
from docker.errors import DockerException, APIError

from datetime import datetime

linux_date="Fri Feb 25 16:07:17 UTC 2022"

# transform date String to python date....
def extractDate(attrDate):
	try:
		dateOnly = attrDate.split('T')
		time=dateOnly[1]
		#print("time Created: ",time)
		return dateOnly[0]
	except(Exception) as e:
		print("Date transformation error: "+str(e))


try:
	client = docker.from_env()
	
	client.swarm.leave(force=True)
	#if client.swarm:
	#	print("Swarm exists, leaving forcefully swarm: "+str(client))
	#	client.swarm.leave(force=True)
		
	print("Starting new swarm.....\n")	
	
	client.swarm.init(
		advertise_addr='127.0.0.1:80', listen_addr='127.0.0.1:5000',
		force_new_cluster=False, default_addr_pool=['10.30.0.0/16'],
		subnet_size=24, snapshot_interval=5000,
		log_entries_for_slow_followers=1200
	)

	#print(client.swarm.attrs)
	allAttrs=client.swarm.attrs

	dateCreated = extractDate(allAttrs['CreatedAt'])

	print("Created At: ",dateCreated,
			"Swarm ID: ",allAttrs['ID'])#,"Name: ",allAttrs['Name'] )
	
	if(client.swarm.leave(force=True)):
		print("\nForcefully left the swarm")
	#print(client.swarm)
	
except (DockerException, APIError, Exception) as e:
	print("EXCEPTION: "+str(e))
