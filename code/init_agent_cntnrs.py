#!/usr/bin/python3

# add healthcheck (low level api)

from os import path, listdir
import docker
import sys
# from pudb import set_trace; set_trace()


class InitAgent:

    def __init__(
            self, client, sut, agnt_net, net_name, agnt_ip):
        self.client = client
        self.sut = sut
        self.agnt_net = agnt_net
        self.net_name = net_name
        self.agnt_ip = '10.172.15.%i' % agnt_ip
        self.image = 'agnt_img:latest'
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
        host_config = self.client.api.create_host_config(
            privileged=True,
            init=True,
            restart_policy={'Name': 'always'})

        try:
            cntnr = self.client.api.create_container(
                self.image,
                name=self.sut,
                hostname=self.sut,
                host_config=host_config,
                networking_config=net_config,
                # entrypoint=[self.entrypoint],
                command=[self.command],
                volumes=[
                    '%s:%s' % (self.dsock, self.dsock)],
                # volumes=['%s:%s' % self.dsock,
                #          self.log_dir:'log/sut'],
                domainname='maas',
                detach=True,
                tty=True)
        except docker.errors.APIError:
            print('  ## error creating container!')
            pass

        return cntnr

    def init_agent_cntnr(self):
        try:
            cntnr = self.client.containers.get(self.sut)
        except docker.errors.NotFound:
            net_config = self.create_net_config()
            cntnr = self.create_container(net_config)

        # logs = cntnr.logs(stream=True)

        # start container
        try:
            self.client.api.start(container=cntnr.get('Id'))
        except docker.errors.APIError as error:
            print(
                '  - Unable to start agent for: %s' % self.sut)
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
                                     # dockerfile='',
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
        print('[Validating agent image:]')
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


def main():
    # base dir of tf-agent
    work_dir = path.join(
        '/', 'home', 'ubuntu')
    # config dir of sut confs
    conf_dir = path.join(work_dir, 'sut')
    conf_list = listdir(conf_dir)

    # docker init
    client = docker.DockerClient(
        base_url='unix://var/run/docker.sock', timeout=10)

    # validate image
    img_name = 'test'
    try:
        client.images.get(img_name)
    except docker.errors.ImageNotFound:
        build_cntnr_img(client, img_name, work_dir)

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
                          sut,
                          agnt_net,
                          net_name,
                          idx)
        except Exception as error:
            print(
                ' # Unable to start agent for: %s' % sut)
            print('  e: %s' % error)
            print(' -----------------------')

        if idx == (len(conf_list) + 1):  # last sut
            # stop root logging handlers
            print('==============================')

# add arg to force recreation of containers


if __name__ == '__main__':
    main()
