#!/usr/bin/python3

# add healthcheck (low level api)

from pathlib import Path, PurePath
from os import listdir, path
import docker
import sys
# from pudb import set_trace; set_trace()


class InitAgent:

    def __init__(
            self, client, sut_conf, agnt_net, net_name, img_name, agnt_ip):
        self.client = client
        self.sut_conf = sut_conf
        self.sut = PurePath(sut_conf).stem
        self.sut_snpy = PurePath(
            '%s_snappy' % self.sut).with_suffix('.yaml')
        self.agnt_net = agnt_net
        self.net_name = net_name
        self.img_name = img_name
        self.agnt_ip = '172.20.0.%i' % agnt_ip
        self.init_agent_cntnr()

    def create_net_config(self):
        endpt_config = self.client.api.create_endpoint_config(
            ipv4_address=self.agnt_ip)
        net_config = self.client.api.create_networking_config({
            self.net_name: endpt_config})

        return net_config

    def create_container(self, net_config):
        # refactor with pathlib?
        dsock = '/var/run/docker.sock'
        # init
        init_file = '01_start_agent.sh'
        src_init_path = '/data/docker/%s' % init_file
        dst_init_path = '/opt/%s' % init_file
        # ssh export
        essh_file = 'export_ssh_pubkey.py'
        src_essh_path = '/data/docker/%s' % essh_file
        dst_essh_path = '/opt/%s' % essh_file
        # entrypoints
        command = ['/opt/cntnr_entrypt.sh']
        agnt_entrypt = 'agent_entrypt.py'
        cntnr_entrypt = 'cntnr_entrypt.sh'
        src_aetrypt_path = '/data/docker/%s' % agnt_entrypt
        dst_aentrypt_path = '/opt/%s' % agnt_entrypt
        src_centrypt_path = '/data/docker/%s' % cntnr_entrypt
        dst_centrypt_path = '/opt/%s' % cntnr_entrypt
        # agnt conf
        src_conf_path = '/home/ubuntu/sut/%s' % self.sut_conf
        dst_conf_path = '/data/testflinger-agent/sut/%s' % self.sut_conf
        # agnt snappy
        # src_snpy_path = '/data/snappy-device-agents/sut/%s' % self.sut_snpy
        src_snpy_path = '/home/ubuntu/snap/%s' % self.sut_snpy
        dst_snpy_path = '/data/snappy-device-agents/sut/%s' % self.sut_snpy
        # log
        src_log_path = '/var/log/sut-agent/%s.log' % self.sut
        dst_log_path = '/var/log/%s.log' % self.sut
        # common parameters
        host_config = self.client.api.create_host_config(
            privileged=True,
            init=True,
            mounts=[
                # docker socket
                docker.types.Mount(type='bind',
                                   target=dsock,
                                   source=dsock,
                                   read_only=False),
                # init
                docker.types.Mount(type='bind',
                                   target=dst_init_path,
                                   source=src_init_path,
                                   read_only=True),
                # ssh export
                docker.types.Mount(type='bind',
                                   target=dst_essh_path,
                                   source=src_essh_path,
                                   read_only=True),
                # agent entrypoint
                docker.types.Mount(type='bind',
                                   target=dst_aentrypt_path,
                                   source=src_aetrypt_path,
                                   read_only=True),
                # cntnr entrypoint
                docker.types.Mount(type='bind',
                                   target=dst_centrypt_path,
                                   source=src_centrypt_path,
                                   read_only=True),
                # agnt conf
                docker.types.Mount(type='bind',
                                   target=dst_conf_path,
                                   source=src_conf_path,
                                   read_only=True),
                # agent snappy
                docker.types.Mount(type='bind',
                                   target=dst_snpy_path,
                                   source=src_snpy_path,
                                   read_only=True),
                # log
                docker.types.Mount(type='bind',
                                   target=dst_log_path,
                                   source=src_log_path,
                                   read_only=False)],

            restart_policy={'Name': 'always'})

        # try:
        cntnr = self.client.api.create_container(
            self.img_name,
            name=self.sut,
            hostname=self.sut,
            host_config=host_config,
            networking_config=net_config,
            command=command,
            domainname='maas',
            detach=True,
            tty=True)
        # except docker.errors.APIError:
        #     print(' # error creating container!')
        #     pass

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
        subnet='172.20.0.0/24')
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool])

    agnt_net = client.api.create_network(net_name,
                                         driver='bridge',
                                         ipam=ipam_config)

    return agnt_net


def build_cntnr_img(client, img_name, dockf_path):
    def stream_build():
        for line in client.api.build(path=dockf_path,
                                     tag=img_name,
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
        print(' # unable to build agent image!')
        sys.exit()
    else:
        print()
        print('[Validating agent image]')
        try:
            client.images.get(img_name)
        except docker.errors.ImageNotFound:
            print(' # agent image not found!')
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
    work_dir = PurePath('/', 'home', 'ubuntu')
    log_dir = PurePath('/', 'var', 'log', 'sut-agent')
    # config dir of sut confs
    conf_dir = PurePath(work_dir, 'sut')
    # conf_list = list(Path(conf_dir).iterdir())
    conf_list = listdir(conf_dir)  # for enumerate

    # docker init
    # dockf_path = PurePath('/', 'home', 'ubuntu')
    dockf_path = path.join('/', 'home', 'ubuntu')
    client = docker.DockerClient(
        base_url='unix://var/run/docker.sock', timeout=10)

    # validate/(build) image
    img_name = 'agnt_img:latest'
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

    print('==============================')
    print('[Loading agent containers]')

    # iterate over agent conf dir to init agent cntnrs
    for idx, sut_conf in enumerate(conf_list):
        # filter non-conf files
        if not sut_conf.endswith('.conf'):
            pass

        # agnt ip offset
        idx = idx + 2  # first ip
        sut = PurePath(sut_conf).stem
        # touch log file
        log_f = PurePath(log_dir, sut).with_suffix('.log')
        Path(log_f).touch()

        # try:
        _ = InitAgent(client,
                      sut_conf,
                      agnt_net,
                      net_name,
                      img_name,
                      idx)
        # except Exception as error:
        #     print(
        #         ' # unable to start agent for: %s' % sut)
        #     print('  e: %s' % error)
        #     print(' -----------------------')

    print('==============================')


if __name__ == '__main__':
    main()
