# Docker scripts in Python 3
1. Initialize a single-node Docker Swarm with the name “ExPECA”.
2. Prints out the ID, name, and creation date of the Swarm.
3. Creates a network named “expeca_test_net”, using the “overlay”
driver, “global” scope, and with an IP CIDR range of 10.100.0.0/24.
4. Prints out the ID, name, and creation date of the network.
5. Deploys a service named “server” with three (3) replicas of
the molguin/edgedroid2:server docker image (see https://hub.docker.com/repository/docker/molguin/edgedroid2)
• Passing the following arguments to the service containers: 0.0.0.0 5000 test -v, will make them listen for  incoming connections on port 5000 on all container interfaces.
• The service automatically restarts (always)
• The code should print out the names, IDs, and number of running replicas of both server and client services.
• You can make your code run for a set amount of time (e.g. 1
minute), then shut down cleanly, clean up after itself to bring down
services, remove the overlay network, and finally tear down the Docker Swarm

## Further notes:
### Help
docker run --rm -it molguin/edgedroid2:server --help
## Resources
• Python 3.10 standard library: https://docs.python.org/3/
• Docker: https://docs.docker.com/
• Docker Swarm: https://docs.docker.com/engine/swarm/
• Libraries for interacting with Docker from Python:
– docker-py: https://docker-py.readthedocs.io
