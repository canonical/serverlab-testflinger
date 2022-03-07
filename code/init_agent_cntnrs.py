#!/usr/bin/python3

# add healthcheck (low level api)

from os import path, listdir
import docker
import sys
# from pudb import set_trace; set_trace()


class InitAgent:

    def __init__(
            self, client, sut_conf, agnt_net, net_name, img_name, agnt_ip):
        self.client = client
        self.sut_conf = sut_conf
        self.sut = path.splitext(sut_conf)[0]
        self.agnt_net = agnt_net
        self.net_name = net_name
        self.img_name = img_name
        self.agnt_ip = '10.172.15.%i' % agnt_ip
        self.command = 'bash'
        # self.entrypoint = path.join(
        #     '/', 'opt', 'agnt_entrypt.py')
        self.dsock = '/var/run/docker.sock'
        # self.log_dir = path.join(
        #     '/', 'data', 'testflinger-agent')
        self.init_agent_cntnr()

    def create_net_config(self):
        endpt_config = self.client.api.create_endpoint_config(
            ipv4_address=self.agnt_ip)
        net_config = self.client.api.create_networking_config({
            self.net_name: endpt_config})

        return net_config

    def create_container(self, net_config):
        # common parameters
        src_conf_path = '/home/ubuntu/sut/%s' % self.sut_conf
        dst_conf_path = '/conf/%s' % self.sut_conf
        src_log_path = '/var/log/sut-agent/%s.log' % self.sut
        dst_log_path = '/var/log/%s.log' % self.sut
        host_config = self.client.api.create_host_config(
            privileged=True,
            init=True,
            mounts=[
                docker.types.Mount(type='bind',
                                   target=self.dsock,
                                   source=self.dsock,
                                   read_only=False),
                docker.types.Mount(type='bind',
                                   target=dst_conf_path,
                                   source=src_conf_path,
                                   read_only=True),
                docker.types.Mount(type='bind',
                                   target=dst_log_path,
                                   source=src_log_path,
                                   read_only=False)],
            restart_policy={'Name': 'always'})

        try:
            cntnr = self.client.api.create_container(
                self.img_name,
                name=self.sut,
                hostname=self.sut,
                host_config=host_config,
                networking_config=net_config,
                # entrypoint=[self.entrypoint],
                command=[self.command],
                domainname='maas',
                detach=True,
                tty=True)
        except docker.errors.APIError:
            print(' # error creating container!')
            pass

        return cntnr

    def init_agent_cntnr(self):
        try:
            cntnr = self.client.containers.get(self.sut)
        except docker.errors.NotFound:
            net_config = self.create_net_config()
            cntnr = self.create_container(net_config)

        # start container
        try:
            self.client.api.start(container=cntnr.get('Id'))
        except docker.errors.APIError as error:
            print(
                ' # unable to start agent for: %s' % self.sut)
            print('    e: %s' % error)
            print('  -----------------------')
        else:
            print('  * %s' % self.sut)


def init_network(client, net_name):
    ipam_pool = docker.types.IPAMPool(
        subnet='10.172.15.0/24',
        gateway='10.172.15.1')
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool])

    agnt_net = client.api.create_network(net_name,
                                         driver='bridge',
                                         ipam=ipam_config)

    return agnt_net


def build_cntnr_img(client, img_name, dockf_path):
    def stream_build():
        for line in client.api.build(path=dockf_path,
                                     tag='agnt_img',
                                     nocache=True,
                                     rm=True,
                                     decode=True):
            line = str(line.get('stream')).rstrip('\n')

            if line != 'None':
                print('%s' % line)

    print('==============================')
    print('[Building agent cntnr image]\n')
    try:
        stream_build()
    except docker.errors.BuildError:
        print(' ## unable to build agent image!')
        sys.exit()
    else:
        print()
        print('[Validating agent image]')
        try:
            client.images.get(img_name)
        except docker.errors.ImageNotFound:
            print(' ## agent image not found!')
            sys.exit()
        else:  # just in case
            print(' * agent image present')


def create_cntnr_vol():
    # map to /var/log/sut-agent/<sut>
    pass


def recreate_cntnrs():
    # add arg to force recreation of containers
    pass


def main():
    # base dir of tf-agent
    work_dir = path.join(
        '/', 'home', 'ubuntu')
    # config dir of sut confs
    conf_dir = path.join(work_dir, 'sut')
    conf_list = listdir(conf_dir)

    # docker init
    dockf_path = path.join(
        '/', 'home', 'ubuntu')
    client = docker.DockerClient(
        base_url='unix://var/run/docker.sock', timeout=10)

    # validate/(build) image
    img_name = 'agnt_img'
    try:
        client.images.get(img_name)
    except docker.errors.ImageNotFound:
        # build image if not present
        build_cntnr_img(client, img_name, dockf_path)

    # setup network
    net_name = 'agent_net'
    try:
        agnt_net = client.networks.get(net_name)
    except docker.errors.NotFound:
        agnt_net = init_network(client, net_name)

    print('\n==============================')
    print('[Loading agent containers]')

    for idx, sut_conf in enumerate(conf_list):
        # agnt ip offset
        idx = idx + 2
        sut = path.splitext(sut_conf)[0]

        try:
            _ = InitAgent(client,
                          sut_conf,
                          agnt_net,
                          net_name,
                          img_name,
                          idx)
        except Exception as error:
            print(
                ' # unable to start agent for: %s' % sut)
            print('  e: %s' % error)
            print(' -----------------------')

        if idx == (len(conf_list) + 1):  # last sut
            # stop root logging handlers
            print('==============================')


if __name__ == '__main__':
    main()
