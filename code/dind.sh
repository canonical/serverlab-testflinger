sudo apt-get install \
    ca-certificates \
    curl \
    gpg \
    lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
sudo apt update
apt-cache policy docker-ce
sudo apt install docker-ce
# sudo apt install docker-ce python3-docker python3-dockerpty
sudo usermod -aG docker ${USER}
# logout / login
sudo update-alternatives --set iptables /usr/sbin/iptables-legacy
sudo update-alternatives --set ip6tables /usr/sbin/ip6tables-legacy
# requires privileged: true
sudo dockerd &
sudo chmod 666 /var/run/docker.sock
sudo vim /etc/docker/daemon.json
   add:
{
    "storage-driver": "vfs",
    "dns": ["10.1.10.3", "10.245.128.4"]
}
sudo pkill -f dockerd && sudo dockerd
--------------------------------------------------------
mkdir ~/portainer
docker pull portainer/portainer
docker tag portainer/portainer portnr_img
docker run -d -p 9000:9000 \
--restart always \
-v /var/run/docker.sock:/var/run/docker.sock \
-v ~/portainer:/data \
--name agnt_portnr \
portnr_img
--------------------------------------------------------
# antiquated
vim Dockerfile (testflinger-agent_cntr)
# docker exec -it testflinger-agent docker build -t test .
docker exec -it testflinger-agent docker build -t test /home/ubuntu/.
docker run --privileged=true -v /var/run/docker.sock:/var/run/docker.sock -it bash -c
# bash-5.1# traceroute 4.2.2.1
# traceroute to 4.2.2.1 (4.2.2.1), 30 hops max, 46 byte packets
#  1  172.17.0.1 (172.17.0.1)  0.006 ms  0.006 ms  0.004 ms
#  2  10.172.10.1 (10.172.10.1)  0.005 ms  0.004 ms  0.005 ms
#  3  10.1.10.2 (10.1.10.2)  0.282 ms  0.214 ms  0.245 ms

---------------------------------------------------------
# run proto_ag_cont.py




docker network create -d bridge agent_br3

sudo apt install apt-transport-https ca-certificates curl wget software-properties-common git

docker run -d -v /var/run/docker.sock:/var/run/docker.sock \
     --privileged=true -t -i bash

docker run -itd -v /var/run/docker.sock:/var/run/docker.sock up -d


import docker
client = docker.from_env()
client.containers.run("ubuntu", "echo hello world", volumes=['/var/run/docker.sock:/var/run/docker.sock'])





import docker

client = docker.from_env()
container = client.containers.run(
    'bfirsh/reticulate-splines', detach=True)
container.logs()


#### Notes ###
Dockerfile built in compose, then upload to container
two forks:
use fn in cmd= in api
use docker entrypoint file 
using docker instead of subprocess gets docker web interface for restarting agent
build process for subcontainer takes place @ build
restarting agents easy 
use cmd with logging 

