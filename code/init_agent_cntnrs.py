#!/usr/bin/python3

# Todo
# add healthcheck (low level api)
# add args to init specific conf file
# change agnt net to use var
# import host net name

# Notes
# use mounts for scale

from pathlib import Path, PurePath
from os import listdir, path, fspath, environ
import docker
import time
import hvac
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
        self.agnt_ip = '10.245.130.%i' % agnt_ip
        self.vclient = self.configure_vault()
        self.init_agent_cntnr()

    def configure_vault(self):
        client = hvac.Client(
            url='http://10.245.128.121:8200',
            token='nh-vault-root',
        )

        return client

    def create_net_config(self):
        endpt_config = self.client.api.create_endpoint_config(
            ipv4_address=self.agnt_ip)
        net_config = self.client.api.create_networking_config({
            self.net_name: endpt_config})

        return net_config

    def create_host_config(self):
        # docker root
        try:
            dhost_path = PurePath(  # passthru env var from dckrfile
                str(environ.get('HOSTDIR')))
        except EnvironmentError:
            print('Environment var HOSTDIR undefined!')
            sys.exit()

        # paths (relative to host docker root)
        # init
        init_file = PurePath(
            '01_start_agent').with_suffix('.sh')
        src_init_path = PurePath(dhost_path,
                                 'code',
                                 init_file)
        dst_init_path = PurePath('/',
                                 'etc',
                                 'my_init.d',
                                 init_file)
        # ssh export
        essh_file = PurePath(
            'export_ssh_pubkey_agnt').with_suffix('.py')
        src_essh_path = PurePath(dhost_path,
                                 'code',
                                 essh_file)
        dst_essh_path = PurePath('/',
                                 'opt',
                                 essh_file)
        # agent entrypoint
        aentrypt_file = PurePath(
            'agent_entrypt').with_suffix('.py')
        src_aentrypt_path = PurePath(dhost_path,
                                     'code',
                                     aentrypt_file)
        dst_aentrypt_path = PurePath('/',
                                     'opt',
                                     aentrypt_file)
        # container entrypoint
        centrypt_file = PurePath(
            'cntnr_entrypt').with_suffix('.sh')
        src_centrypt_path = PurePath(dhost_path,
                                     'code',
                                     centrypt_file)
        dst_centrypt_path = PurePath('/',
                                     'opt',
                                     centrypt_file)
        # agnt snappy
        src_snpy_path = PurePath(dhost_path,
                                 'sut',
                                 'snappy',
                                 self.sut_snpy)
        dst_snpy_path = PurePath('/',
                                 'data',
                                 'snappy-device-agents',
                                 'sut',
                                 self.sut_snpy)
        # agnt server
        srv_conf = PurePath(
            'testflinger-agent').with_suffix('.conf')
        src_sconf_path = PurePath(dhost_path,
                                  'code',
                                  srv_conf)
        dst_sconf_path = PurePath('/',
                                  'data',
                                  'testflinger-agent',
                                  srv_conf)
        # healthcheck
        hlthchk_file = PurePath(
            'agent_healthcheck').with_suffix('.py')
        src_hlthchk_path = PurePath(dhost_path,
                                    'code',
                                    hlthchk_file)
        dst_hlthchk_path = PurePath('/',
                                    'opt',
                                    hlthchk_file)
        # sru tests
        sru_file = PurePath(
            'sru_01').with_suffix('.sh')
        src_sru_path = PurePath(dhost_path,
                                'code',
                                'sru',
                                sru_file)
        dst_sru_path = PurePath('/',
                                'opt',
                                sru_file)
        # agnt conf
        src_conf_path = PurePath(dhost_path,
                                 'sut',
                                 'agent',
                                 self.sut_conf)
        dst_conf_path = PurePath('/',
                                 'data',
                                 'testflinger-agent',
                                 'sut',
                                 self.sut_conf)
        # log
        src_log_path = PurePath(dhost_path,
                                'log',
                                self.sut).with_suffix('.log')
        dst_log_path = PurePath('/',
                                'var',
                                'log',
                                self.sut).with_suffix('.log')
        # end paths
        host_config = self.client.api.create_host_config(
            restart_policy={'Name': 'always'},
            # privileged=True,
            mem_limit='1g',
            mounts=[
                # shared mounts
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
                                   source=fspath(src_aentrypt_path),
                                   read_only=True),
                # cntnr entrypoint
                docker.types.Mount(type='bind',
                                   target=fspath(dst_centrypt_path),
                                   source=fspath(src_centrypt_path),
                                   read_only=True),
                # agent snappy
                docker.types.Mount(type='bind',
                                   target=fspath(dst_snpy_path),
                                   source=fspath(src_snpy_path),
                                   read_only=True),
                # agent server
                docker.types.Mount(type='bind',
                                   target=fspath(dst_sconf_path),
                                   source=fspath(src_sconf_path),
                                   read_only=True),
                # healthcheck
                docker.types.Mount(type='bind',
                                   target=fspath(dst_hlthchk_path),
                                   source=fspath(src_hlthchk_path),
                                   read_only=True),
                # sru tests
                docker.types.Mount(type='bind',
                                   target=fspath(dst_sru_path),
                                   source=fspath(src_sru_path),
                                   read_only=True),
                # unique mounts
                # agnt conf
                docker.types.Mount(type='bind',
                                   target=fspath(dst_conf_path),
                                   source=fspath(src_conf_path),
                                   read_only=False),
                # log
                docker.types.Mount(type='bind',
                                   target=fspath(dst_log_path),
                                   source=fspath(src_log_path),
                                   read_only=False)
            ])

        return (host_config, dst_centrypt_path, dst_hlthchk_path)

    def decrypt_env_vars(self):
        influx_vars = self.vclient.secrets.kv.read_secret_version(
            path='influx'
        )

        # env vars
        env = {
            'INFLUX_HOST': influx_vars['data']['data']['host'],
            'INFLUX_PORT': influx_vars['data']['data']['port'],
            'INFLUX_USER': influx_vars['data']['data']['user'],
            'INFLUX_PW': influx_vars['data']['data']['passw']
        }

        return env

    def create_container(self):
        # prelim config
        net_config = self.create_net_config()

        # common parameters
        host_config, cmd_path, hlthc_path = self.create_host_config()

        # define healthcheck
        healthchk = docker.types.Healthcheck(
            test=['CMD', 'python3', fspath(hlthc_path)],
            interval=(1000000 * 10 * 1000),  # 10 sec
            timeout=(1000000 * 20 * 1000),
            retries=2,
            start_period=(1000000 * 25 * 1000)
        )

        # try:
        cntnr = self.client.api.create_container(
            self.img_name,
            name=self.sut,
            hostname=self.sut,
            host_config=host_config,
            networking_config=net_config,
            command=[fspath(cmd_path)],
            healthcheck=healthchk,
            domainname='maas',
            environment=self.decrypt_env_vars(),
            detach=True,
            tty=True)
        # except docker.errors.APIError:
        #     print(' # error creating container!')
        #     pass

        return cntnr

    def init_agent_cntnr(self):
        # start container
        def start_cntnr(cntnr_id):
            try:
                self.client.api.start(container=cntnr_id)
            except docker.errors.APIError as error:
                print(
                    ' # unable to start agent for: %s' % self.sut)
                print('    e: %s' % error)
                print('  -----------------------')
            else:
                print('  * %s' % self.sut)

        try:
            cntnr = self.client.containers.get(self.sut)
        except docker.errors.NotFound:
            cntnr = self.create_container()
            # throttle calls
            time.sleep(3)
            start_cntnr(cntnr.get('Id'))
        else:
            start_cntnr(cntnr.id)


def init_network(client, net_name):
    ipam_pool = docker.types.IPAMPool(
        subnet='10.245.128.0/22')
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool])

    agnt_net = client.api.create_network(net_name,
                                         driver='macvlan',
                                         ipam=ipam_config)

    return agnt_net


# def load_env_vars():
#     host = getenv('INFLUX_HOST')
#     if not host:
#         print('InfluxDB host undefined')
#         sys.exit()
#     port = int(getenv('INFLUX_PORT', 8086))
#     user = getenv('INFLUX_USER', '')
#     password = getenv('INFLUX_PW', '')

#     build_args = {
#         'influx_host': host,
#         'influx_port': port,
#         'influx_user': user,
#         'influx_pw': password
#     }

#     return build_args

#     # import influx env vars
#     load_dotenv()
#     build_args = {
#         'INFLX_HOST': getenv('INFLX_HOST'),
#         'INFLX_USER': getenv('INFLX_USER'),
#         'INFLX_PW': getenv('INFLX_PW')


def build_cntnr_img(client, img_name, dockf_dir):
    def stream_build():
        for line in client.api.build(path=dockf_dir,
                                     tag=img_name,
                                     nocache=True,
                                     rm=True,
                                     decode=True,):
            line = str(
                line.get('stream')).rstrip('\n')

            if line != 'None':
                print(line)

    print('==============================')
    print('[ building agent cntnr image ]\n')
    try:
        stream_build()
    except docker.errors.BuildError:
        print(' # unable to build agent image!')
        sys.exit()
    else:
        print()
        print('[ validating agent image ]')
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
        base_url='unix://var/run/docker.sock', timeout=15)

    # validate/(build) image
    img_name = 'agnt_img:latest'
    try:
        client.images.get(img_name)
    except docker.errors.ImageNotFound:
        # build image if not present
        build_cntnr_img(client, img_name, dockf_dir)

    # setup network
    net_name = 'testflinger-docker_needham_int'
    first_ip = 126  # x.x.x.first_ip
    try:
        agnt_net = client.networks.get(net_name)
    except docker.errors.NotFound:
        agnt_net = init_network(client, net_name)

    print('==============================')
    print('[ loading agent containers ]')

    # iterate over agent conf dir to init agent cntnrs
    for idx, sut_conf in enumerate(conf_list):
        # filter non-conf files
        if not sut_conf.endswith('.conf'):
            pass

        # agnt ip offset
        ip_n = idx + first_ip
        sut = PurePath(sut_conf).stem
        # touch log file
        log_f = PurePath(log_dir, sut).with_suffix('.log')
        Path(log_f).touch()

        try:
            _ = InitAgent(client,
                          sut_conf,
                          agnt_net,
                          net_name,
                          img_name,
                          ip_n)
        except Exception as error:
            print(
                '  # unable to start agent for: %s' % sut)
            print('    e: %s' % error)
            print('    -----------------------')

    print('==============================')


if __name__ == '__main__':
    main()
