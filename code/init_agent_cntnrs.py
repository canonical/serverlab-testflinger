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
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(message)s')
logger = logging.getLogger(__name__)


class InitAgent:

    def __init__(
            self, client, sut_conf, agnt_net, net_name, img_name, mac_addr
    ):
        self.client = client
        self.sut_conf = sut_conf
        self.sut = PurePath(sut_conf).stem
        self.sut_snpy = PurePath(
            '%s_snappy' % self.sut).with_suffix('.yaml')
        self.agnt_net = agnt_net
        self.net_name = net_name
        self.img_name = img_name
        self.mac_addr = mac_addr
        self.vclient = self.configure_vault()
        self.init_agent_cntnr()

    def configure_vault(self):
        vault_client = hvac.Client(
            url='http://172.16.0.2:8200',
            token='nh-vault-root',
        )

        return vault_client

    def create_net_config(self):
        endpt_config = self.client.api.create_endpoint_config(
            aliases=[self.sut, ]
        )

        net_config = self.client.api.create_networking_config({
            self.net_name: endpt_config}
        )

        return net_config

    def create_host_config(self):
        # docker root
        try:
            dhost_path = PurePath(  # passthru env var from dckrfile
                str(environ.get('HOSTDIR'))
            )
        except EnvironmentError:
            logger.error('Environment var HOSTDIR undefined!')
            sys.exit()

        # paths (relative to host docker root)
        # config.sh
        sec_conf_file = PurePath(
            'env_config').with_suffix('.sh')
        src_secconf_path = PurePath(dhost_path,
                                 'code',
                                 sec_conf_file)
        dst_secconf_path = PurePath('/',
                                 'opt',
                                 sec_conf_file) 
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
        # agnt server
        srv_conf = PurePath(
            'testflinger-agent').with_suffix('.conf')
        src_sconf_path = PurePath(dhost_path,
                                  'code',
                                  srv_conf)
        dst_sconf_path = PurePath('/',
                                  'data',
                                  'testflinger',
                                  'agent',
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
                                 'testflinger',
                                 'agent',
                                 'sut',
                                 self.sut_conf)
        # agnt snappy
        src_snpy_path = PurePath(dhost_path,
                                 'sut',
                                 'snappy',
                                 self.sut_snpy)
        dst_snpy_path = PurePath('/',
                                 'data',
                                 'testflinger',
                                 'device-connectors',
                                 'sut',
                                 self.sut_snpy)
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
                # env_conf.sh
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_secconf_path),
                    source=fspath(src_secconf_path),
                    read_only=True
                ),
                # init
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_init_path),
                    source=fspath(src_init_path),
                    read_only=True
                ),
                # ssh export
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_essh_path),
                    source=fspath(src_essh_path),
                    read_only=True
                ),
                # agent entrypoint
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_aentrypt_path),
                    source=fspath(src_aentrypt_path),
                    read_only=True
                ),
                # cntnr entrypoint
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_centrypt_path),
                    source=fspath(src_centrypt_path),
                    read_only=True
                ),
                # agent server
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_sconf_path),
                    source=fspath(src_sconf_path),
                    read_only=True
                ),
                # healthcheck
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_hlthchk_path),
                    source=fspath(src_hlthchk_path),
                    read_only=True
                ),
                # sru tests
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_sru_path),
                    source=fspath(src_sru_path),
                    read_only=True
                ),
                # unique mounts
                # agnt conf
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_conf_path),
                    source=fspath(src_conf_path),
                    read_only=False
                ),
                # agent snappy
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_snpy_path),
                    source=fspath(src_snpy_path),
                    read_only=False
                ),
                # log
                docker.types.Mount(
                    type='bind',
                    target=fspath(dst_log_path),
                    source=fspath(src_log_path),
                    read_only=False
                ),
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
            'INFLUX_PW': influx_vars['data']['data']['passw'],
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

        try:
            cntnr = self.client.api.create_container(
                self.img_name,
                name=self.sut,
                hostname=self.sut,
                host_config=host_config,
                networking_config=net_config,
                mac_address=self.mac_addr,
                command=[fspath(cmd_path)],
                healthcheck=healthchk,
                domainname='maas',
                environment=self.decrypt_env_vars(),
                detach=True,
                tty=True
            )
        except docker.errors.APIError as error:
            logger.error(f'{error}\nAPIError while creating container!')

        return cntnr

    def init_agent_cntnr(self):
        # start container
        def start_cntnr(cntnr_id):
            try:
                self.client.api.start(container=cntnr_id)
            except docker.errors.APIError as error:
                logger.error(
                    f' # (init_agent_cntnr()) unable to start agent for: {self.sut}'
                    f'\n    e: {error})'
                    '\n  -----------------------'
                )
            else:
                logger.info(f'  * {self.sut}')

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
        subnet='10.245.128.0/21',
        iprange='10.245.133.0/23',
        gateway='10.245.128.1')
    ipam_config = docker.types.IPAMConfig(
        pool_configs=[ipam_pool])

    agnt_net = client.api.create_network(net_name,
                                         driver='macvlan',
                                         ipam=ipam_config)

    return agnt_net


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
                logger.info(line)

    logger.info(
        '=============================='
        '\n[ building agent cntnr image ]\n'
    )
    try:
        stream_build()
    except docker.errors.BuildError:
        logger.info(' # unable to build agent image!')
        sys.exit()

    logger.info('\n[ validating agent image ]')
    try:
        client.images.get(img_name)
    except docker.errors.ImageNotFound:
        logger(' # agent image not found!')
        sys.exit()

    logger.error(' * agent image present')


def main():
    # config dir of sut confs
    conf_dir = PurePath(
        '/', 'data', 'testflinger', 'agent', 'sut')
    log_dir = PurePath('/', 'var', 'log', 'sut-agent')
    # conf_list = list(Path(conf_dir).iterdir())
    conf_list = listdir(conf_dir)  # for enumerate
    # matched in dhcp server snippet
    mac_prefix = "02:42:0a:f5:"

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
    net_name = 'serverlab-testflinger_needham_int'  # docker-compose
    try:
        agnt_net = client.networks.get(net_name)
    except docker.errors.NotFound:
        agnt_net = init_network(client, net_name)

    logger.info(
        '============================='
        '\n[ loading agent containers ]'
    )

    # iterate over agent conf dir to init agent cntnrs
    for idx, sut_conf in enumerate(conf_list):
        # filter non-conf files
        if not sut_conf.endswith('.conf'):
            continue

        sut = PurePath(sut_conf).stem
        # touch log file
        log_f = PurePath(log_dir, sut).with_suffix('.log')
        Path(log_f).touch()

        # convert idx int to hex
        mac_suffix = "{:05x}".format(idx)
        if len(mac_suffix) > 5:
            raise ValueError("index length exceeds valid MAC suffix length")

        mac_addr = mac_prefix + ":".join(
            mac_suffix[i:i + 2] for i in range(0, len(mac_suffix), 2))

        try:
            InitAgent(
                client,
                sut_conf,
                agnt_net,
                net_name,
                img_name,
                mac_addr
            )
        except Exception as error:
            logger.error(
                f'  # unable to start agent for: {sut}'
                f'\n    e: {error}'
                '\n    -----------------------'
            )

    logger.info('=============================')


if __name__ == '__main__':
    main()
