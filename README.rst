******************
Testflinger-Docker
    Basic info, deployment and other notes.
*******************************************

Docker Containers
=================
All container dockerfiles are located in the project root.

testflinger-agent
-----------------
Standard testflinger agent build, using Docker.
    • Includes snappy device agents.
    • Runs a heavily customized image.

testflinger-cli
---------------
Standard testflinger cli build, using Docker.
    • Runs a heavily customized image.

testflinger-api
---------------
Gunicorn, with gevent.

testflinger-db
--------------
Redis database container.

testflinger-mqtt
----------------
Stack MQTT broker.


Project notes and files of interest
===================================
* ./code/start_sut_agents
    • Runs on testflinger-agent.
    • Starts all agents, and performs logging.
    • Transmits agent output to stack MQTT broker.
    • Logs agent output /var/log/sut-agent within testflinger-agent.
    • Developer notes and aspirations within source file.

    Published MQTT topics::
    	agent : agent/logger status
    	c3 : current status of REST comms from agent to C3
    	output: current agent output
    	submit_status : when active, lists topic to publish test cmd
    	submit : last published job (as seen on the recieving end)
        job

* ./code/start_submit_agents
    • Runs on testflinger-cli.
    • Starts lightweight sut agents, similar to start_sut_agents.
    • The "submit_status" topic will list instructions if the submit agent is ready.
    • These agents listen for test submissions via MQTT, will then start the appropriate job. See MQTT notes below for useage.

* ./code/01_run_sut_agents
    • Starts sut agents on testflinger-agent boot.

* ./code/01_run_submit_agents
    • Starts submit agents on testflinger-cli boot.

* ./code/export_ssh_pubkey.py
    • Pushes ssh keys to specified stack MAAS host for maas-cli api.
    • Runs on container boot, will not push key if it already exists.

* ./reference.yaml
    • Reference device agent file to facilitate job pushing via MQTT.

* ./tf-entrypoint
    • Runs on testflinger-agent and testflinger-cli.
    • Starts appropriate microservices, see below for more info.

* ./tools/*
    • Contains convenience scripts for streamlined Docker ops.
    • Most used scripts::
    	 deploy_stack.sh : complete, clean deployment of stack
    	 reroll.sh : completely destroy stack, pull Git and redeploy
    	 orb_nuke.sh : completely destroy stack and all associated files and data


MQTT notes and useage
=====================
*Grab a MQTT client, MQTT Explorer recommended.
    • This provides an excellent top-level view of all MQTT clients and topics within the MQTT broker. This means you can see all Testflinger agents running in the lab and their respective output and auxillary topics such as C3 status relative to the agent.

* Point the client MQTT broker, as in Needham (stack broker settings):
    • Protocol: mqtt://
    • Host: 10.245.128.14
    • Port: 1883
    • Leave username and password blank.
    • Keep 'validate certificate' and 'encryption' unchecked

* To submit a test via MQTT, publish to <sut>/submit.
    • The "submit_status" topic indicates if the submit agent is ready.
    • If using MQTT explorer (or similar clients):
        • Use the "publish" field and use <sut>/submit as the topic. 
        • Raw text mode suggested, but other modes should work.
    • Publish the test cmd as in the same field in the sut snappy yaml file::
        ssh -o StrictHostKeyChecking=no \
        ubuntu@$DEVICE_IP \
        /usr/bin/test-network
    Note: when using MQTT explorer, breaking up long lines as above is recommended.

A web-based MQTT client running within the lab, as a part of larger monitoring (or automation/CI) is the next natural step here (so a client isn't necessary).


Deploying Stack
===============

Deploy and configure Docker host
--------------------------------
Deploy 18.04+ host via MAAS.
After host is deployed, setup prerequisites:

* Update system::
    sudo apt update

* Install Docker package dependencies::
    sudo apt install apt-transport-https ca-certificates curl wget software-properties-common git

* Install Docker GPG key::
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

* Add Docker repo to APT sources::
    sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    sudo apt update
    apt-cache policy docker-ce

* Install Docker::
    sudo apt install docker-ce
    sudo systemctl start docker

* Add user to Docker group to exec Docker commands without sudo::
    sudo usermod -aG docker ${USER}
    su - ${USER}
    (or logout and log back in)

* Verify user in appropriate group::
    id -nG | grep docker

* Find target Docker Compose version (use 1.29.2+)::
    https://github.com/docker/compose/releases

* Download and install Docker Compose::
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

* Make executable::
    sudo chmod +x /usr/local/bin/docker-compose

* Verify Docker Compose installation & version::
    docker-compose --version

* Pull repo from Launchpad or Github::
    git clone https://git.launchpad.net/~alanec/+git/testflinger-docker
    (or)
    git clone https://github.com/hum4n0id/testflinger-docker


Customize source and config files for environment:
--------------------------------------------------
All work is done in the Git cloned Docker root dir (testflinger-docker/).

Update relevant files are to match local environment:
-----------------------------------------------------
Files that need to be updated:
* Required updates::
    ./docker-compose.yaml
    ./code/tf-entrypoint.sh
    ./code/testflinger.conf

* Deployment optional updates (can be added post-deployment)::
    ./sut/*

* Optional updates (uses default parameters)::
    ./tools/deploy_stack.sh

* After this step, run ./tools/parse_tf_files.sh

Edit docker-compose.yaml file to match environment:
---------------------------------------------------
* Change the parent network parameters to match the environment. Keeping the default bridge parameters will work in any standard environment.

* Likewise, update container IPs to match said networks.

Edit the testflinger entrypoint file (tf-entrypoint):
-----------------------------------------------------
File location: ./code/tf-entrypoint.sh (ref*).
This shell script is exec’d upon container boot/start.

* Update the top-level variables to match your environment:
    • TF_MAAS_ACT is the MAAS Testflinger account (create one if it doesn’t exist).
    • MAAS API key is located in the MAAS dashboard for the testflinger  account’s settings (create one if it doesn’t exist).

* Add them to the file as follows::
    TF_MAAS_ACT=testflinger_a
    MAAS_SERVER=10.245.128.4
    MAAS_PORT=5240
    MAAS_API_KEY=’<api_key>’

Edit ./code/testflinger.conf (ref *):
-------------------------------------
* Update the REDIS_HOST field to the db container ip address::
    REDIS_HOST = '10.172.10.13'

Modify/Create SUT files:
------------------------
* Update any testflinger-agent *.conf files with the api server IP::
    server_address: http://10.245.128.10:8000 (use actual api ip)

* Make sure the snappy-device-agents yaml files are appended with _snappy if you want the deployment to automatically transfer them from the sut directory to the containers. You can alternatively create the config files inside the container post-deployment.


Deploy Compose Stack:
=====================
* Execute the deploy-stack script to start deployment::
    bash ./tools/deploy-stack.sh

* If you want to start over from scratch, execute the orb_nuke (orbital nuke) script.::
    bash ./tools/orb_nuke.sh

* The rest of the deployment should be handled by the Docker code included in the source directory.

Validate Deployment:
--------------------
When successfully deployed and running, you can check the output of the stack.

* Show containers::
    docker-compose ps

* Validate logs::
    docker logs <containter_name>

Once the deployment is complete, no other steps should be required to start executing Testflinger tests on SUTs outside of ensuring the appropriate configuration files are in the agent and cli containers.


References (incomplete):
========================
Docker Compose Specification:
https://github.com/compose-spec/compose-spec/blob/master/spec.md

Docker Build Ref (Dockerfile):
https://docs.docker.com/engine/reference/builder/

Phusion Baseimage:
https://github.com/phusion/baseimage-docker
