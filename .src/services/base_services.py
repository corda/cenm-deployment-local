import os
from abc import ABC
from pyhocon import ConfigFactory
from managers.download_manager import DownloadManager
from utils import SystemInteract, Logger, Constants, java_string
import glob
import uuid
import re

class BaseService(ABC):
    """Base service for all services to inherit.

    Args:
        abb:
            The abbreviation of the service.
        dir:
            The directory for the service.
        plugin:
            Whether the service is a plugin.
        repo:
            Whether the service has its own repository.
        artifact_name:
            The name of the artifact.
        version:
            The version of the artifact.
        ext:
            The extension of the artifact.
        url:
            The url to download the artifact from.
        dlm:
            A download manager.
        
    """
    def __init__(self,
        abb: str,
        dir: str,
        artifact_name: str, 
        version: str, 
        ext: str, 
        url: str,
        username: str,
        password: str
    ):
        self.abb = abb
        self.dir = f'cenm-{dir}'
        self.artifact_name = artifact_name
        self.ext = ext
        self.version = version
        self.url = self.__build_url(url)
        self.dlm = DownloadManager(username, password)
        self.sysi = SystemInteract()
        self.error = False

    def __str__(self) -> str:
        return f"BaseService[{self.abb}, {self.dir}, {self.artifact_name}, {self.ext}, {self.version}]"

    def __repr__(self):
        return self.__str__()
        
    # internal url builder
    def __build_url(self, url: str):
        return f'{url}/{self.artifact_name}/{self.version}/{self.artifact_name}-{self.version}.{self.ext}'

    def _zip_name(self, no_version: bool = False):
        return f'{self.artifact_name}.{self.ext}' if no_version else f'{self.artifact_name}-{self.version}.{self.ext}'
    
    def _clone_repo(self):
        if not self.sysi.path_exists(self.dir):
            print(f'Cloning {self.dir}')
            self.sysi.run(f'git clone {Constants.GITHUB_URL.value}/{self.dir}-deployment-local.git {self.dir} --quiet')

    def _check_presence(self) -> bool:
        for _, _, files in os.walk(self.dir):
            if f'{self.artifact_name}.jar' in files or f'{self.artifact_name}-{self.version}.jar' in files:
                return True
        return False
    
    def _move(self):
        self.sysi.run(f'mv {self._zip_name()} {self.dir}')
        if self.ext == "zip":
            self.sysi.run(f'(cd {self.dir} && unzip -q -o {self._zip_name()} && rm {self._zip_name()})')

    def download(self) -> bool:
        self._clone_repo()
        if self._check_presence():
            return #self.dlm.validate_download(self.url)
        # If artifact not present then download it
        print(f'Downloading {self._zip_name()}')
        self.error = self.dlm.download(self.url)
        self._move()
        return self.error

    # TODO: wip
    def validate_artifact(self) -> bool:
        raise NotImplementedError
        # return all([self._check_presence(), self.dlm.validate_download(self.url)])
        # return self.dlm.check_md5sum(f'{self.dir}/{self._zip_name()}', self.url)
    
class SignerPluginService(BaseService):
    """Base service for signing service plugins
    
    """
    def _handle_plugin(self):
        if not self.sysi.path_exists(f'{self.dir}/plugins'):
            self.sysi.run(f'mkdir {self.dir}/plugins')
        self.sysi.run(f'mv {self._zip_name()} {self.dir}/plugins')

    def download(self) -> bool:
        if self._check_presence():
            return
        # If artifact not present then download it
        print(f'Downloading {self._zip_name()}')
        self.error = self.dlm.download(self.url)
        self._handle_plugin()
        return self.error

class CordappService(BaseService):
    """Base service for CorDapps
    
    """
    def _handle_cordapp(self):
        if not self.sysi.path_exists(f'{self.dir}/cordapps'):
            self.sysi.run(f'mkdir {self.dir}/cordapps')
        self.sysi.run(f'mv {self._zip_name()} {self.dir}/cordapps')
    
    def download(self) -> bool:
        if self._check_presence():
            return
        # If artifact not present then download it
        print(f'Downloading {self._zip_name()}')
        self.error = self.dlm.download(self.url)
        self._handle_cordapp()
        return self.error

class DeploymentService(BaseService):
    """Base service for deployable services

    Args:
        first 8 args:
            passed to [BaseService] constructor (see above)
        config_file:
            The name of the configuration file for the service
        deployment_time:
            The time taken for the service to deploy (average)
            this gives an indication how long the deployment manager
            should sleep before starting the next service
        certificates:
            The number of certificates required for the service
        java_version:
            The version of java to use for the service

    """
    def __init__(self,
        abb: str,
        dir: str,
        artifact_name: str, 
        version: str, 
        ext: str, 
        url: str,
        username: str,
        password: str,
        config_file: str,
        deployment_time: int,
        certificates: int = None,
        java_version: int = 8
    ):
        super().__init__(
            abb, 
            dir, 
            artifact_name, 
            version, 
            ext, 
            url,
            username,
            password
        )
        logging_manager = Logger()
        self.logger = logging_manager.get_logger(dir)
        self.runtime_files = Constants.RUNTIME_FILES.value
        self.config_file = config_file
        self.deployment_time = deployment_time
        self.certificates = certificates
        self.java_version = java_version

    def __str__(self) -> str:
        return f"DeploymentService[{self.abb}, {self.dir}, {self.artifact_name}, {self.ext}, {self.version}]"

    def __repr__(self):
        return self.__str__()

    def _get_cert_count(self) -> bool:
        cert_count = self.sysi.run_get_stdout(f"ls {self.dir}/certificates | xargs | wc -w | sed -e 's/^ *//g'")
        return int(cert_count)
        
    def deploy(self):
        self.logger.info(f'Thread started to deploy {self.artifact_name}')
        while True:
            try:
                self.logger.debug(f'[Running] (cd {self.dir} && {java_string(self.java_version)} && java -jar {self.artifact_name}.jar -f {self.config_file}) to start {self.artifact_name} service')
                exit_code = self.sysi.run_get_exit_code(f'(cd {self.dir} && {java_string(self.java_version)} && java -jar {self.artifact_name}.jar -f {self.config_file})')
                if exit_code != 0:
                    raise RuntimeError(f'{self.artifact_name} service stopped')
            except:
                self.logger.warning(f'{self.artifact_name} service stopped. Restarting...')

    def validate_config(self) -> str:
        try:
            ConfigFactory.parse_file(f'{self.dir}/{self.config_file}')
            return ""
        except Exception as e:
            return str(e)

    def validate_certs(self) -> str:
        if self._get_cert_count() < self.certificates:
            return f'Certificate mismatch ({self._get_cert_count()} found, {self.certificates} expected)'
        else:
            return ""

    def clean_runtime(self):
        for root, dirs, files in os.walk(self.dir):
            for dir in dirs:
                if dir in self.runtime_files['dirs']:
                    self.sysi.remove(os.path.join(root, dir))

    def clean_artifacts(self):
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                if file.endswith('.jar'):
                    self.sysi.remove(os.path.join(root, file))
                elif file in ["cenm", "cenm.cmd"]:
                    self.sysi.remove(os.path.join(root, file))

    def clean_certificates(self):
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                if file.endswith('.jks') or file.endswith('.crl'):
                    self.sysi.remove(os.path.join(root, file))

    def clean_all(self):
        self.sysi.remove(self.dir)

class NodeDeploymentService(DeploymentService):
    """Base service for a Corda Node

    """
    def __str__(self) -> str:
        return f"NodeDeploymentService[{self.abb}, {self.dir}, {self.artifact_name}, {self.ext}, {self.version}]"

    def __repr__(self):
        return self.__str__()

    def _notary(self) -> bool:
        """Check if the [NodeDeploymentService] is a notary

            Caution this only works for the default notary configured
            in the [ServiceManager] from the hardcorded abb variable.

            To implement this properly the [NodeDeploymentService] should
            overload the __init__ method and pass in a notary boolean for
            node services.

        """
        return self.abb == "notary"

    def _construct_new_node_dir(self, new_dir):
        self.sysi.run(f'cp -r {self.dir} cenm-{new_dir}')
        node_number = new_dir.split("-")[-1]
        perl_dir = f'cenm-{new_dir}/node.conf'
        node_uuid = uuid.uuid4().hex[:5]
        self.sysi.perl(perl_dir, 'myLegalName.*O\\=\\K.*(?=, L\\=.*)', f'TestNode{node_number}-{node_uuid}')
        self.sysi.perl(perl_dir, 'p2pAddress.*:\\K.*(?=\\"\\\n)', f'60{node_number}11')
        self.sysi.perl(perl_dir, '^\\s*address.*:\\K.*(?=\\"\\\n)', f'60{node_number}12')
        self.sysi.perl(perl_dir, '^\\s*adminAddress.*:\\K.*(?=\\"\\\n)', f'60{node_number}13')
        self.sysi.perl(perl_dir, '^\\s*port \\= \\K.*(?=\\\n)', f'223{node_number}')

    def _copy(self, new_dir):
        new_node = NodeDeploymentService(
            abb=self.abb,
            dir=new_dir,
            artifact_name=self.artifact_name,
            version=self.version,
            ext=self.ext,
            url=self.url,
            username=self.dlm.username,
            password=self.dlm.password,
            config_file=self.config_file,
            deployment_time=self.deployment_time,
            certificates=self.certificates,
            java_version=self.java_version
        )
        if not self.sysi.path_exists(f'cenm-{new_dir}'):
            self._construct_new_node_dir(new_dir)
            new_node.download()
        return new_node

    def _is_registered(self) -> bool:
        return glob.glob(f'{self.dir}/nodeInfo-*')

    def _register_node(self, artifact_name):
        self.logger.info('Registering node to the network')
        self.sysi.wait_for_host_on_port(10000)
        exit_code = -1
        while exit_code != 0:
            self.logger.debug(f'[Running] (cd {self.dir} && {java_string(self.java_version)} && java -jar {artifact_name}.jar initial-registration --network-root-truststore ./certificates/network-root-truststore.jks --network-root-truststore-password trustpass -f {self.config_file}) to start {self.artifact_name} service')
            exit_code = self.sysi.run_get_exit_code(f'(cd {self.dir} && {java_string(self.java_version)} && java -jar {artifact_name}.jar initial-registration --network-root-truststore ./certificates/network-root-truststore.jks --network-root-truststore-password trustpass -f {self.config_file})')

    def deploy(self):
        artifact_name = f'{self.artifact_name}-{self.version}'

        if not self._is_registered():
            self._register_node(artifact_name)
            self.sysi.wait_for_host_on_port(20000)
            # wait for network parameters to be signed
            if self._notary():
                self.sysi.sleep(90)

        while True:
            try:
                self.logger.debug(f'[Running] (cd {self.dir} && {java_string(self.java_version)} && java -jar {artifact_name}.jar -f {self.config_file}) to start {self.artifact_name} service')
                exit_code = self.sysi.run_get_exit_code(f'(cd {self.dir} && {java_string(self.java_version)} && java -jar {artifact_name}.jar -f {self.config_file})')
                if exit_code != 0:
                    raise RuntimeError(f'{self.artifact_name} service stopped')
            except:
                self.logger.warning(f'{self.artifact_name} service stopped. Restarting...')

    def clean_runtime(self):
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                if file.startswith("nodeInfo"):
                    self.sysi.remove(os.path.join(root, file))
                if file in self.runtime_files['notary_files']:
                    self.sysi.remove(os.path.join(root, file), silent=True)
        super().clean_runtime()