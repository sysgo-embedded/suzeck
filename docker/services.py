#!/usr/bin/python

from time import sleep
import sys

import docker
from docker.types import RestartPolicy, Placement
from docker.errors import DockerException, APIError

# --- Return the date (and the time) of a docker attr date ---
def extractDate(attrDate):
	try:
		dateOnly = attrDate.split('T')
		time=dateOnly[1]
		time=time.split('.') # get rid of millisecs
		time=time[0]
		#print("time created: ",time)
		return dateOnly[0]
	except(Exception) as e:
		print("Date transformation error: "+str(e))
		print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
# ----------------------------------------

# --- Initialize a swarm over a docker client. Return the ID
def swarm_init(client):
	try:
		client.swarm.init(
			#advertise_addr='127.0.0.1:80', 
			listen_addr='127.0.0.1:5000',
			force_new_cluster=False, 
			#default_addr_pool=['10.30.0.0/16'],
			#subnet_size=24, 
			#name='dddddd',
			snapshot_interval=5000,
			log_entries_for_slow_followers=1200
		)

		print('Swarm Created:',
				'\n\t ID: ',client.swarm.attrs['ID'],
				'\n\t Name: ',client.swarm.attrs['Spec']['Name'],
				'\n\t Created at: ',extractDate(client.swarm.attrs['CreatedAt'])
				)
		return client.swarm.attrs['ID']
	except (DockerException, APIError, Exception) as e:
		print("swarm_init EXCEPTION: "+str(e))	
		print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
# ----------------------------------------

# --- Create a network over a docker swarm. Return the ID
def network_init(client):
	ipam_pool = docker.types.IPAMPool(
		 subnet='10.100.0.0/24'
		 #gateway='192.168.52.254'
	)
	ipam_config = docker.types.IPAMConfig(
		pool_configs=[ipam_pool]
	)
	try:
		net = client.networks.create("expeca_test_net", 
						driver="overlay", 
						scope="global",		
						ipam = ipam_config
				)

		print("Network Created:\n\t ID: ",net.id, 
				"\n\t Name: ",net.name, 
				"\n\t Created at: ",extractDate(net.attrs["Created"])
				)
		#print(net.attrs) # print all network attributes
		cidr=net.attrs["IPAM"]["Config"][0] #sublist
		#print(cidr['Subnet']) #print the subnet assigned
		return net.id
	except (APIError) as e:
		print("network_init EXCEPTION: "+str(e))	
		print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
# ----------------------------------------

# --- Initialize a server service over a docker client. Return the ID
def service_init_server(client):
	try:
		service_created = client.services.create(
			mode='replicated', 
			#replicas=3,
			image='molguin/edgedroid2:server',
			#command='python /home/ubuntu/python.py',
			constraints=['node.role == manager'],
			#mounts='/home/ubuntu/deployment/python.py:/home/ubuntu/python.py:rw',
			networks=['expeca_test_net'],
			restart_policy=RestartPolicy(condition='none'),
			name='server'
			
			# change the restart condition to 'always'
			# create 3 replicas
			
		)
		service_created.scale(3)
		
		''''
		scaled = True# service_created.scale(3)
		if scaled==True:
			print("Scaled service: ",scaled)
		else:
			print("Scaling service FAILED...")
		'''
		
		#print('\n\n',service_created.attrs,'\n\n') # print all service attributes
		
		print("Service SERVER created:", 
				"\n\t Name: ",service_created.name,
				"\n\t Replicas: ",service_created.attrs['Spec']['Mode']['Replicated']['Replicas']
				)
		return service_created.id
		
	except (DockerException, APIError, Exception) as e:
		print("service_init_server EXCEPTION: "+str(e))	
		print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
# ----------------------------------------

# --- Initialize a client service over a docker client. Return the ID
def service_init_client(client):
	try:
		service_created = client.services.create(
			mode='replicated', 
			#replicas=3,
			image='molguin/edgedroid2:client',
			constraints=['node.role == worker'],
			networks=['expeca_test_net'],
			restart_policy=RestartPolicy(condition='none'),
			name='client'
			
			# change the restart condition to 'always'
			# create 3 replicas
			
		)
		
		'''
		scaled = service_created.scale(3)
		if scaled:
			print("Scaled client service: ",scaled)
		else:
			print("Scale to 3 replicas failed...")
		'''
		
		print("Service CLIENT created:", 
				"\n\t Name: ",service_created.name,
				"\n\t Replicas: ",service_created.attrs['Spec']['Mode']['Replicated']['Replicas']
				)
		#client.services.list()
		return service_created.id
	except (DockerException, APIError, Exception) as e:
		print("service_init_client EXCEPTION: "+str(e))	
		print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))
# ----------------------------------------

# --- print all attributes of a swarm
def print_all_attrs(client):
	print("---------- SWARM ATTRIBUTES --------")
	for k,v in client.swarm.attrs.items():
		print (k," --> ") 
		print(v,"\n")
	print("---------- SWARM ATTRIBUTES --------\n")
# ----------------------------------------

# --- time counter. Insert time in secs
def timeCounter(secs):
	timeCounter=secs
	print("---\tWaiting for",secs," secs\t----\n")
	while (timeCounter<0): 
		sleep(1) #wait one sec
		timeCounter+=1
		if timeCounter%10==0: # print only every 10 secs
			print(secs, " seconds passed: ",timeCounter)
	print("---\tCommence Deleting/Cleaning all\t----")
# ----------------------------------------


# =============== MAIN ======================
try:
	#client = docker.DockerClient(base_url='unix://var/run/docker.sock')
	client = docker.from_env()
	#print_all_attrs(client)
	
	swarmLeave = client.swarm.leave(force=True)
	if (swarmLeave):
		print("Existing swarm exited succesfully")
	print('\n')
	
	swarmID = swarm_init(client)
	print('\n')
	
	networkID = network_init(client)
	print('\n')
	
	serverServiceID = service_init_server(client)
	print('\n')
	
	clientServiceID = service_init_client(client)
	print('\n')

	timeCounter(6) # wait XX seconds

# -------------- SERVICES -------------------------------
	print('\nActive services: ',client.services.list())
	if(serverServiceID or clientServiceID):
		print("\tServices exist. About to delete them...")
		if(client.services.get(clientServiceID).remove() and
			client.services.get(serverServiceID).remove()):
				print("\tBoth services deleted sucessfuly...")
	print('Active services: ',client.services.list(),'\n')
	
#-------------- NETWORK ---------------------------------
	print('Existing networks=',len(client.networks.list()))
	print('Deleting created network (remove)')
	try:
		client.networks.get(networkID).remove()
		print("Network ",networkID,", deleted sucesfully")
	except (Exception, APIError, DockerException) as e:
		print("delete networks EXCEPTION: "+str(e))
	print('Existing networks=',len(client.networks.list()),'\n')

# ------------- SWARM ------------------------------------
	'''
	if (client.swarm.leave(force=True)):
		print("Swarm exited succesfully\n")
	else:
		print("Swarm falied to delete...\n")
	'''	
except (Exception) as e:
	print("main EXCEPTION: "+str(e))
	print("Error on line {}".format(sys.exc_info()[-1].tb_lineno))