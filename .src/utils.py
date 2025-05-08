import logging
import os
import re
from enum import Enum
from typing import List, Dict, Optional
from sys import platform
import warnings
import functools
import uuid

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.
    
    """
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("{} is deprecated.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return new_func

class Constants(Enum):
    BASE_URL = 'https://software.r3.com/artifactory'
    GITHUB_URL = 'https://github.com/corda'
    EXT_PACKAGE = 'extensions-lib-release-local/com/r3/appeng'
    ENM_PACKAGE = 'r3-enterprise-network-manager/com/r3/enm'
    CORDA_PACKAGE = 'r3-corda-releases/com/r3/corda'
    CORDAPP_PACKAGE = 'corda-releases/net/corda'
    CORDA_PLUGIN_PACKAGE = 'corda-gateway-plugins/com/r3/corda'

    MSSQL_DRIVER = 'https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/8.2.2.jre8/mssql-jdbc-8.2.2.jre8.jar'
    POSTGRES_DRIVER = 'https://repo1.maven.org/maven2/org/postgresql/postgresql/42.5.2/postgresql-42.5.2.jar'
    ORACLE_DRIVER = 'https://repo1.maven.org/maven2/com/oracle/ojdbc/ojdbc8/19.3.0.0/ojdbc8-19.3.0.0.jar'

    REPOS = ['auth', 'gateway', 'idman', 'nmap', 'notary', 'node', 'pki', 'signer', 'zone']
    DB_SERVICES = ['auth', 'idman', 'nmap', 'notary', 'node', 'zone']

    RUNTIME_FILES = {
        'dirs': ["logs", "h2", "ssh", "shell-commands", "djvm", "artemis", "brokers", "additional-node-infos"],
        'notary_files': ["process-id", "network-parameters", "nodekeystore.jks", "truststore.jks", "sslkeystore.jks", "certificate-request-id.txt"],
        'angel_files': ["network-parameters.conf", "network-parameters.conf_bak", "networkmap.conf", "networkmap.conf_bak", "identitymanager.conf", "identitymanager.conf_bak", "token"]
    }

class Platform(Enum):
    LINUX = 'linux'
    OSX = 'osx'
    WINDOWS = 'windows'

class DeployTimeConstants(Enum):
    ANGEL_DEPLOY_TIME = 5
    IDMAN_DEPLOY_TIME = 10
    SIGNER_DEPLOY_TIME = 10
    NMAP_DEPLOY_TIME = 20
    AUTH_DEPLOY_TIME = 15
    GATEWAY_DEPLOY_TIME = 5
    ZONE_DEPLOY_TIME = 10

    NOTARY_DEPLOY_TIME = 60
    NODE_DEPLOY_TIME = 70

class DeployTimeAngelConstants(Enum):
    ANGEL_DEPLOY_TIME = 5
    IDMAN_DEPLOY_TIME = 30
    SIGNER_DEPLOY_TIME = 10
    NMAP_DEPLOY_TIME = 20
    AUTH_DEPLOY_TIME = 15
    GATEWAY_DEPLOY_TIME = 5
    ZONE_DEPLOY_TIME = 10

    NOTARY_DEPLOY_TIME = 5
    NODE_DEPLOY_TIME = 30

def java_string(java_version: int) -> str:
    java_home = re.sub(r"\d+", str(java_version), SystemInteract().run_get_stdout('echo $JAVA_HOME').strip())
    return f'unset JAVA_HOME; export JAVA_HOME={java_home}'

def get_cenm_java_version(version: str) -> int:
    cenm_sub_version = re.findall(r'\.(\d+).?', version)[0]
    if not cenm_sub_version:
        return 8
    elif int(cenm_sub_version) < 7:
        return 8
    else:
        return 17

def get_corda_java_version(version: str) -> int:
    corda_sub_version = re.findall(r'\.(\d+).?', version)[0]
    if not corda_sub_version:
        return 8
    elif int(corda_sub_version) < 12:
        return 8
    else:
        return 17

# TODO: Logger needs an overhaul
class Logger:
    """Logger management

    """
    def __init__(self):
        self.formatter = logging.Formatter('[%(asctime)s, %(levelname)s] %(name)s %(message)s')

    def _set_logging_config(self, logger_name: str, log_file: str, level=logging.DEBUG):
        logger = logging.getLogger(logger_name)

        fileHandler = logging.FileHandler(log_file, mode='a')
        fileHandler.setFormatter(self.formatter)

        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(self.formatter)

        logger.setLevel(level)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

    def get_logger(self, name: str):
        """Create a logger

        Args:
            name:
                The name of the class that called the logger.

        Returns:
            A logger object with the name of the class that called it.

        """
        self._set_logging_config(name, f".logs/default-deployment-{name}.log")
        return logging.getLogger(name)

# TODO: Printer can probably be absorbed into [ServiceManager]
class Printer:
    """Printer for version printing

    """
    def __init__(self,
        cenm_version: str,
        auth_version: str,
        gateway_version: str,
        nms_visual_version: str,
        node_plugin_version: str,
        flow_plugin_version: str,
        corda_version: str
    ):
        self.cenm_version = cenm_version
        self.auth_version = auth_version
        self.gateway_version = gateway_version
        self.nms_visual_version = nms_visual_version
        self.node_plugin_version = node_plugin_version
        self.flow_plugin_version = flow_plugin_version
        self.corda_version = corda_version

    def print_cenm_version(self):
        print("""
CENM local deployment manager
=====================================

Current CENM version:        {}
Current Auth version:        {}
Current Gateway version:     {}
Current NMS version:         {}
Current Node plugin version: {}
Current Flow plugin version: {}

Current Corda version:       {}
        """.format(
            self.cenm_version,
            self.auth_version,
            self.gateway_version,
            self.nms_visual_version,
            self.node_plugin_version,
            self.flow_plugin_version,
            self.corda_version
        ))

class SystemInteract:
    """Class for using system commands

    """
    def __init__(self):
        self.platform = self._platform()

    def _platform(self) -> Optional[str]:
        if platform == "linux" or platform == "linux2":
            return Platform.LINUX
        elif platform == "darwin":
            return Platform.OSX
        elif platform == "win32":
            return Platform.WINDOWS
        else:
            return None

    def path_exists(self, path: str) -> bool:
        """Checks a path exists

        Args:
            path:
                A path to check.

        Returns:
            True if path exists False if not.

        """
        return os.path.exists(path)

    def sleep(self, seconds: int):
        """Sends sleep command to system, not python sleep

        Args:
            seconds:
                Number of seconds to sleep.

        """
        os.system(f'sleep {seconds}')

    def perl(self, file: str, predicate: str, replace: str, multi_line: bool = False):
        """Runs a perl replacement command

        Args:
            file:
                The file on which to perform the replacement.
            predicate:
                The string to replace.
            replace:
                The string to replace with.
            multi_line:
                If true, will ingest the whole file to perform multi-line replacements.

        """
        if multi_line:
            os.system(f'perl -0777 -i -pe "s/{predicate}/{replace}/" {file}')
        else:
            os.system(f'perl -i -pe "s/{predicate}/{replace}/" {file}')

    def remove(self, path: str, silent: bool = False):
        """Removes a system path

        Args:
            path:
                A path to remove (works for both folders and files).
            silent:
                If true, will suppress output.

        """
        if silent:
            os.system(f'rm -rf {path} > /dev/null 2>&1')
        else:
            os.system(f'rm -rf {path}')

    def create_file_with(self, path: str, content: str):
        """Creates a file with content

        Args:
            path:
                A path to create.
            content:
                The content to write to the file.

        """
        os.system(f'echo "{content}" > {path}')

    def file_contains(self, path: str, content: str) -> bool:
        """Checks if a file contains a string

        Args:
            path:
                A path to check.
            content:
                The content to check for.

        Returns:
            True if the file contains the string, False otherwise.

        """
        return os.system(f'grep -q "{content}" {path}') == 0

    def run(self, cmd: str, silent: bool = False):
        """Runs a system command

        Args:
            cmd:
                Command to run.

        """
        if silent:
            os.system(f'{cmd} > /dev/null 2>&1')
        else:
            os.system(cmd)

    def run_get_exit_code(self, cmd: str, silent: bool = False) -> int:
        """Runs a system command and returns the exit code

        Args:
            cmd:
                Command to run.
            silent:
                If true, will suppress output.

        Returns:
            The exit code of the command.

        """
        if silent:
            return os.system(f'{cmd} > /dev/null 2>&1')
        else:
            return os.system(cmd)

    def run_get_stdout(self, cmd: str) -> str:
        """Runs a system command and returns the stdout stream

        Args:
            cmd:
                Command to run.

        Returns:
            The stdout stream as a string.

        """
        unique_file = f'.tmp-{uuid.uuid4().hex}'
        os.system(f'{cmd} > {unique_file}')
        try:
            with open(unique_file, 'r') as f:
                out = f.read()
            self.remove(unique_file, silent=True)
        except:
            out = 'E: Could not read stdout'
            self.remove(unique_file, silent=True)
        return out
    
    def wait_for_host_on_port(self, port: int, host: str = "localhost"):
        """Waits for a host to be available on a port

        Args:
            port:
                The port to wait on.
            host:
                The host to wait on, default is localhost.

        """
        wait_code = "G" if self.platform == Platform.OSX else "w"
        while self.run_get_exit_code(f'nc -z -{wait_code} 3 {host} {port} > /dev/null 2>&1') != 0:
            self.sleep(5)
        # Safety sleep to allow service on [port] to fully start
        self.sleep(10)

class CenmTool:
    """Class for using cenm cli tool

    Args:
        version:
            The version of the cenm cli tool to use.

    """
    def __init__(self, nms_visual_version: str):
        self.host = 'http://127.0.0.1:8089'
        self.path = 'cenm-gateway/cenm-tool'
        self.jar = f'cenm-tool-{nms_visual_version}.jar'
        self.java_version = get_cenm_java_version(nms_visual_version)
        self.sysi = SystemInteract()

    def _run(self, cmd: str):
        print(f'Running: {cmd}')
        return self.sysi.run_get_stdout(f'(cd {self.path} && {java_string(self.java_version)} && java -jar {self.jar} {cmd})')

    def _login(self, username: str, password: str):
        self._run(f'context login -s {self.host} -u {username} -p {password}')
    
    def _logout(self):
        self._run(f'context logout {self.host}')

    def create_zone(self,
        config_file: str, 
        network_map_address: str,
        network_parameters: str, 
        label: str,
        label_color: str
    ) -> str:
        self._login('network-maintainer', 'p4ssWord')
        token = self._run(f'zone create-subzone --config-file={config_file} --network-map-address={network_map_address} --network-parameters={network_parameters} --label={label} --label-color="{label_color}" --zone-token')
        self._logout()
        return token

    def set_config(self, service: str, config_file: str, subzone: str = None) -> str:
        self._login('config-maintainer', 'p4ssWord')
        if subzone:
            token = self._run(f'{service} config set -s {subzone} -f={config_file} --zone-token')
        else:
            token = self._run(f'{service} config set -f={config_file} --zone-token')
        self._logout()
        return token

    def set_admin_address(self, service: str, address: str, subzone: str = None):
        self._login('config-maintainer', 'p4ssWord')
        # You can only specify sub_zone for netmap
        if subzone and service == "netmap":
            self._run(f'{service} config set-admin-address -s {subzone} -a={address}')
        else:
            self._run(f'{service} config set-admin-address -a={address}')
        self._logout()

    def get_subzones(self) -> List[str]:
        self._login('config-maintainer', 'p4ssWord')
        subzones = self._run('zone get-subzones')
        self._logout()
        zones = self.sysi.run_get_stdout(f"echo \"{subzones}\" | grep id | rev | cut -d ' ' -f 1 | rev | xargs").replace(',','').replace('\n','').split(' ')
        return zones

    def cenm_subzone_deployment_init(self) -> Dict[str, str]:
        tokens = {}

        self.set_admin_address('identity-manager', 'localhost:5053')
        # print(self.sysi.run_get_stdout(f'(cd {self.path} && cat ../../cenm-idman/identitymanager-init.conf)'))
        tokens['idman'] = self.set_config('identity-manager', '../../cenm-idman/identitymanager-init.conf')

        self.sysi.create_file_with(f'cenm-idman/token', tokens['idman'])

        while not self.sysi.file_contains("cenm-nmap/network-parameters-init.conf", "notaryNodeInfoFile.*nodeInfo"):
            self.sysi.sleep(5)

        # print(self.sysi.run_get_stdout(f'(cd {self.path} && cat ../../cenm-nmap/network-parameters-init.conf)'))
        tokens['nmap'] = self.create_zone(
            config_file='../../cenm-nmap/networkmap-init.conf',
            network_map_address='localhost:20000',
            network_parameters='../../cenm-nmap/network-parameters-init.conf',
            label='Main',
            label_color='#941213'
        )
        self.set_admin_address('signer', 'localhost:5054')
        # print(self.sysi.run_get_stdout(f'(cd {self.path} && cat ../../cenm-signer/signer.conf)'))
        tokens['signer'] = self.set_config('signer', '../../cenm-signer/signer.conf')

        for token_dir, token in tokens.items():
            if not self.sysi.path_exists(f'cenm-{token_dir}/token'):
                self.sysi.create_file_with(f'cenm-{token_dir}/token', token)

        return tokens

    def cenm_set_subzone_config(self, subzone: str) -> str:
        self.set_admin_address('netmap', 'localhost:5055', subzone=subzone)
        return self.set_config('netmap', '../../cenm-nmap/networkmap-init.conf', subzone=subzone)
