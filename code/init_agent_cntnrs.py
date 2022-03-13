#!/usr/bin/python3

# TODO
# add healthcheck (low level api)
# add args to init specific conf file
# add

from pathlib import Path, PurePath
from os import listdir, path, fspath, environ
import docker
import time
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
        # passthru env var from compose
        self.dhost_path = environ.get('HOSTDIR')
        self.init_agent_cntnr()

    def create_net_config(self):
        endpt_config = self.client.api.create_endpoint_config(
            ipv4_address=self.agnt_ip)
        net_config = self.client.api.create_networking_config({
            self.net_name: endpt_config})

        return net_config

    def create_container(self, net_config):
        # paths
        dsock = PurePath('/',
                         'var',
                         'run',
                         'docker').with_suffix('.sock')
        # init
        init_file = '01_start_agent'  # .sh
        src_init_path = PurePath('/',
                                 self.dhost_path,
                                 'code',
                                 init_file).with_suffix('.sh')
        dst_init_path = PurePath('/',
                                 'etc',
                                 'my_init.d',
                                 init_file).with_suffix('.sh')
        # ssh export
        essh_file = 'export_ssh_pubkey_agnt'  # .py
        src_essh_path = PurePath('/',
                                 self.dhost_path,
                                 'code',
                                 essh_file).with_suffix('.py')
        dst_essh_path = PurePath('/',
                                 'opt',
                                 essh_file).with_suffix('.py')
        # entrypoints
        src_aetrypt_path = PurePath('/',
                                    self.dhost_path,
                                    'code',
                                    'agent_entrypt').with_suffix('.py')
        dst_aentrypt_path = PurePath('/',
                                     'opt',
                                     'agent_entrypt').with_suffix('.py')
        src_centrypt_path = PurePath('/',
                                     self.dhost_path,
                                     'code',
                                     'cntnr_entrypt').with_suffix('.sh')
        dst_centrypt_path = PurePath('/',
                                     'opt',
                                     'cntnr_entrypt').with_suffix('.sh')
        # agnt conf
        src_conf_path = PurePath('/',
                                 self.dhost_path,
                                 'sut',
                                 'agent',
                                 self.sut_conf)
        dst_conf_path = PurePath('/',
                                 'data',
                                 'testflinger-agent',
                                 'sut',
                                 self.sut_conf)
        # agnt snappy
        src_csnpy_path = PurePath('/',
                                  self.dhost_path,
                                  'sut',
                                  'snappy',
                                  self.sut_snpy)
        dst_snpy_path = PurePath('/',
                                 'data',
                                 'snappy-device-agents',
                                 'sut',
                                 self.sut_snpy)
        # log
        src_log_path = PurePath('/',
                                'log',
                                self.sut).with_suffix('.log')
        dst_log_path = PurePath('/',
                                'var',
                                'log',
                                self.sut).with_suffix('.log')
        # end paths
        # common parameters
        host_config = self.client.api.create_host_config(
            restart_policy={'Name': 'always'},
            privileged=True,
            mounts=[
                # docker socket
                docker.types.Mount(type='bind',
                                   target=fspath(dsock),
                                   source=fspath(dsock),
                                   read_only=False),
                # init
                docker.types.Mount(type='bind',
                                   target=fspath(dst_init_path),
                                   source=fspath(src_init_path),
                                   read_only=True),
                # ssh export
                docker.types.Mount(type='bind',
                                   target=fspath(dst_essh_path),
                                   source=fspath(src_essh_path),
                                   read_only=True),
                # agent entrypoint
                docker.types.Mount(type='bind',
                                   target=fspath(dst_aentrypt_path),
                                   source=fspath(src_aetrypt_path),
                                   read_only=True),
                # cntnr entrypoint
                docker.types.Mount(type='bind',
                                   target=fspath(dst_centrypt_path),
                                   source=fspath(src_centrypt_path),
                                   read_only=True),
                # agnt conf
                docker.types.Mount(type='bind',
                                   target=fspath(dst_conf_path),
                                   source=fspath(src_conf_path),
                                   read_only=True),
                # agent snappy
                docker.types.Mount(type='bind',
                                   target=fspath(dst_snpy_path),
                                   source=fspath(src_csnpy_path),
                                   read_only=True),
                # log
                docker.types.Mount(type='bind',
                                   target=fspath(dst_log_path),
                                   source=fspath(src_log_path),
                                   read_only=False)])

        # try:
        cntnr = self.client.api.create_container(
            self.img_name,
            name=self.sut,
            hostname=self.sut,
            host_config=host_config,
            networking_config=net_config,
            command=[fspath(dst_centrypt_path)],
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
            # throttle calls
            time.sleep(1)

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


def build_cntnr_img(client, img_name, dockf_dir):
    def stream_build():
        for line in client.api.build(path=dockf_dir,
                                     tag=img_name,
                                     nocache=True,
                                     rm=True,
                                     decode=True):
            line = str(
                line.get('stream')).rstrip('\n')

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
    # config dir of sut confs
    conf_dir = PurePath(
        '/', 'data', 'testflinger-agent', 'sut')
    log_dir = PurePath('/', 'var', 'log', 'sut-agent')
    # conf_list = list(Path(conf_dir).iterdir())
    conf_list = listdir(conf_dir)  # for enumerate

    # docker init
    # need to use os.path
    dockf_dir = path.join('/', 'data', 'docker')
    client = docker.DockerClient(
        base_url='unix://var/run/docker.sock', timeout=30)

    # validate/(build) image
    img_name = 'agnt_img:latest'
    try:
        client.images.get(img_name)
    except docker.errors.ImageNotFound:
        # build image if not present
        build_cntnr_img(client, img_name, dockf_dir)

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
