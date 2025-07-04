from services.services import *
from managers.config_manager import ConfigManager
from managers.database_manager import DatabaseManager
from managers.download_manager import DownloadManager
from managers.deployment_manager import DeploymentManager
from managers.node_manager import NodeManager
from utils import *
from typing import List, Dict, Tuple, Any

class ServiceError(Exception):
    def __init__(self, service, dir):
        super().__init__("""
{} artifact not found in {} directory, please try and download agian.
        """.format(service, dir))

class ServiceManager:
    """A manager to manage operations on all CENM services including:
        
        - Downloading Artifacts
        - Downloading Database Drivers
        - Deploying Services
        - Cleaning services

    Args:
        username:
            The username to use for the download.
        password:
            The password to use for the download.
        auth_version:
            The version of the auth service.
        gateway_version:
            The version of the gateway service.
        cenm_version:
            The version of cenm services.
        nms_visual_version:
            The version of nms visual services .
        corda_version:
            The version of Corda to be used.
    
    """
    def __init__(self,
        username: str,
        password: str,
        auth_version: str,
        gateway_version: str,
        cenm_version: str,
        nms_visual_version: str,
        node_plugin_version: str,
        flow_plugin_version: str,
        corda_version: str,
        node_count: int,
        deploy_without_angel: bool
    ):
        self.base_url = Constants.BASE_URL.value
        if auth_version.endswith("-SNAPSHOT") and gateway_version.endswith("-SNAPSHOT"):
            self.ext_package = Constants.EXT_PACKAGE_DEV.value
        else:
            self.ext_package = Constants.EXT_PACKAGE.value
        self.enm_package = Constants.ENM_PACKAGE.value
        self.corda_package = Constants.CORDA_PACKAGE.value
        self.cordapp_package = Constants.CORDAPP_PACKAGE.value
        self.repos = Constants.REPOS.value
        self.db_services = Constants.DB_SERVICES.value
        self.node_count = node_count
        self.deploy_without_angel = deploy_without_angel
        self.sysi = SystemInteract()
        self.printer = Printer(
            cenm_version,
            auth_version,
            gateway_version,
            nms_visual_version,
            node_plugin_version,
            flow_plugin_version,
            corda_version
        )
        if node_plugin_version.endswith("-SNAPSHOT"):
            self.node_corda_plugin_package = Constants.CORDA_PLUGIN_PACKAGE_DEV.value
        else:
            self.node_corda_plugin_package = Constants.CORDA_PLUGIN_PACKAGE.value

        if flow_plugin_version.endswith("-SNAPSHOT"):
            self.flow_corda_plugin_package = Constants.CORDA_PLUGIN_PACKAGE_DEV.value
        else:
            self.flow_corda_plugin_package = Constants.CORDA_PLUGIN_PACKAGE.value

        if deploy_without_angel:
            self.deploy_time = DeployTimeConstants
        else:
            self.deploy_time = DeployTimeAngelConstants
        self.cenm_java_version = get_cenm_java_version(cenm_version)
        self.corda_java_version = get_corda_java_version(corda_version)

        self.AUTH = AuthService(
            abb=            'auth',
            dir=            'auth',
            artifact_name=  'accounts-application',
            version=        auth_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.ext_package}/accounts',
            username=       username,
            password=       password,
            config_file=    'auth.conf',
            deployment_time=self.deploy_time.AUTH_DEPLOY_TIME.value,
            certificates=   2,
            java_version=   self.cenm_java_version)
        self.CLIENT = AuthClientService(
            abb=            'client',
            dir=            'auth',
            artifact_name=  'accounts-client',
            version=        auth_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.ext_package}/accounts',
            username=       username,
            password=       password)
        self.AUTH_PLUGIN = AuthPluginService(
            abb=            'auth-plugin',
            dir=            'auth',
            artifact_name=  'accounts-baseline-cenm',
            version=        cenm_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.enm_package}',
            username=       username,
            password=       password)
        self.AUTH_NODE_PLUGIN = AuthNodePluginService(
            abb=            'auth-node-plugin',
            dir=            'auth',
            artifact_name=  'auth-baseline-node-management-plugin',
            version=        node_plugin_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.node_corda_plugin_package}/node/management/plugin',
            username=       username,
            password=       password)
        self.AUTH_FLOW_PLUGIN = AuthFlowPluginService(
            abb=            'auth-flow-plugin',
            dir=            'auth',
            artifact_name=  'auth-baseline-flow-management-plugin',
            version=        flow_plugin_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.flow_corda_plugin_package}/flow/management/plugin',
            username=       username,
            password=       password)
        self.GATEWAY = GatewayService(
            abb=            'gateway',
            dir=            'gateway',
            artifact_name=  'gateway-service',
            version=        gateway_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.ext_package}/gateway',
            username=       username,
            password=       password,
            config_file=    'gateway.conf',
            deployment_time=self.deploy_time.GATEWAY_DEPLOY_TIME.value,
            certificates=   4,
            java_version=   self.cenm_java_version)
        self.GATEWAY_PLUGIN = GatewayPluginService(
            abb=            'gateway-plugin',
            dir=            'gateway',
            artifact_name=  'cenm-gateway-plugin',
            version=        nms_visual_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.enm_package}',
            username=       username,
            password=       password)
        self.NODE_PLUGIN = NodePluginService(
            abb=            'node-plugin',
            dir=            'gateway',
            artifact_name=  'node-management-plugin',
            version=        node_plugin_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.node_corda_plugin_package}/node/management/plugin',
            username=       username,
            password=       password)
        self.FLOW_PLUGIN = FlowPluginService(
            abb=            'flow-plugin',
            dir=            'gateway',
            artifact_name=  'flow-management-plugin',
            version=        flow_plugin_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.flow_corda_plugin_package}/flow/management/plugin',
            username=       username,
            password=       password)
        self.CLI = CliToolService(
            abb=            'cli',
            dir=            'gateway',
            artifact_name=  'cenm-tool',
            version=        nms_visual_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}',
            username=       username,
            password=       password)
        self.IDMAN = IdentityManagerService(
            abb=            'idman',
            dir=            'idman',
            artifact_name=  'identitymanager',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    'identitymanager-init.conf',
            deployment_time=self.deploy_time.IDMAN_DEPLOY_TIME.value,
            certificates=   3,
            java_version=   self.cenm_java_version)
        self.IDMAN_ANGEL = IdentityManagerAngelService(
            abb=            'idman-angel',
            dir=            'idman',
            artifact_name=  'angel',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    'identitymanager-init.conf',
            deployment_time=self.deploy_time.ANGEL_DEPLOY_TIME.value,
            certificates=   3,
            java_version=   self.cenm_java_version)
        self.CRR_TOOL = CrrToolService(
            abb=            'crr-tool',
            dir=            'idman',
            artifact_name=  'crr-submission-tool',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/tools',
            username=       username,
            password=       password)
        self.NMAP = NetworkMapService(
            abb=            'nmap',
            dir=            'nmap',
            artifact_name=  'networkmap',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    'networkmap-init.conf',
            deployment_time=self.deploy_time.NMAP_DEPLOY_TIME.value,
            certificates=   4,
            java_version=   self.cenm_java_version)
        self.NMAP_ANGEL = NetworkMapAngelService(
            abb=            'nmap-angel',
            dir=            'nmap',
            artifact_name=  'angel',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    'networkmap-init.conf',
            deployment_time=self.deploy_time.ANGEL_DEPLOY_TIME.value,
            certificates=   4,
            java_version=   self.cenm_java_version)
        self.NOTARY = NotaryService(
            abb=            'notary',
            dir=            'notary',
            artifact_name=  'corda',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.corda_package}',
            username=       username,
            password=       password,
            config_file=    'notary.conf',
            deployment_time=self.deploy_time.NOTARY_DEPLOY_TIME.value,
            certificates=   1,
            java_version=   self.corda_java_version)
        self.NODE = NodeService(
            abb=            'node',
            dir=            'node',
            artifact_name=  'corda',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.corda_package}',
            username=       username,
            password=       password,
            config_file=    'node.conf',
            deployment_time=self.deploy_time.NODE_DEPLOY_TIME.value,
            certificates=   1,
            java_version=   self.corda_java_version)
        self.NODE_HA_TOOLS = CordaToolsHaUtilitiesService(
            abb=            'ha-utuilities',
            dir=            'node',
            artifact_name=  'corda-tools-ha-utilities',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.corda_package}',
            username=       username,
            password=       password,
            config_file=    None,
            deployment_time=None,
            java_version=   self.corda_java_version)
        self.FINANCE_CONTRACTS_CORDAPP = FinanceContractsCordapp(
            abb=            'finance-contracts',
            dir=            'node',
            artifact_name=  'corda-finance-contracts',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.cordapp_package}',
            username=       username,
            password=       password)
        self.FINANCE_WORKFLOWS_CORDAPP = FinanceWorkflowsCordapp(
            abb=            'finance-workflows',
            dir=            'node',
            artifact_name=  'corda-finance-workflows',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.cordapp_package}',
            username=       username,
            password=       password)
        self.CORDA_SHELL = CordaShellService(
            abb=            'shell',
            dir=            'node',
            artifact_name=  'corda-shell',
            version=        corda_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.corda_package}',
            username=       username,
            password=       password)
        self.PKI = PkiToolService(
            abb=            'pki',
            dir=            'pki',
            artifact_name=  'pki-tool',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/tools',
            username=       username,
            password=       password,
            config_file=    'pki.conf',
            deployment_time=None,
            java_version=   self.cenm_java_version)
        self.SIGNER = SignerService(
            abb=            'signer',
            dir=            'signer',
            artifact_name=  'signer',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    'signer.conf',
            deployment_time=self.deploy_time.SIGNER_DEPLOY_TIME.value,
            certificates=   6,
            java_version=   self.cenm_java_version)
        self.SIGNER_CA_PLUGIN = SignerPluginCAService(
            abb=            'signer-ca-plugin',
            dir=            'signer',
            artifact_name=  'signing-service-example-plugin-ca',
            version=        cenm_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.enm_package}/signing-service-plugins',
            username=       username,
            password=       password)
        self.SIGNER_NONCA_PLUGIN = SignerPluginNonCAService(
            abb=            'signer-nonca-plugin',
            dir=            'signer',
            artifact_name=  'signing-service-example-plugin-nonca',
            version=        cenm_version,
            ext=            'jar',
            url=            f'{self.base_url}/{self.enm_package}/signing-service-plugins',
            username=       username,
            password=       password)
        self.ZONE = ZoneService(
            abb=            'zone',
            dir=            'zone',
            artifact_name=  'zone',
            version=        cenm_version,
            ext=            'zip',
            url=            f'{self.base_url}/{self.enm_package}/services',
            username=       username,
            password=       password,
            config_file=    '',
            deployment_time=self.deploy_time.ZONE_DEPLOY_TIME.value,
            certificates=   2,
            java_version=   self.cenm_java_version)

        self.db_manager = DatabaseManager(self.get_database_services(), DownloadManager(username, password))
        self.config_manager = ConfigManager()
        self.deployment_manager = DeploymentManager(self.get_deployment_services(deploy_without_angel=deploy_without_angel))

    def _get_all_services(self) -> List[BaseService]:
        return [
            self.AUTH,
            self.CLIENT,
            self.AUTH_PLUGIN,
            self.GATEWAY,
            self.GATEWAY_PLUGIN,
            self.CLI,
            self.IDMAN,
            self.IDMAN_ANGEL,
            self.CRR_TOOL,
            self.NMAP,
            self.NMAP_ANGEL,
            self.NOTARY,
            self.NODE,
            self.NODE_HA_TOOLS,
            self.FINANCE_CONTRACTS_CORDAPP,
            self.FINANCE_WORKFLOWS_CORDAPP,
            self.CORDA_SHELL,
            self.PKI,
            self.SIGNER,
            self.SIGNER_CA_PLUGIN,
            self.SIGNER_NONCA_PLUGIN,
            self.ZONE,
            self.NODE_PLUGIN,
            self.AUTH_NODE_PLUGIN,
            self.FLOW_PLUGIN,
            self.AUTH_FLOW_PLUGIN
        ]

    def _get_node_manager(self) -> NodeManager:
        return NodeManager(self.NODE, self.node_count)

    def get_service(self, name: str) -> BaseService:
        for service in self._get_all_services():
            if service.artifact_name == name:
                return service
        raise ValueError(f'No service with name {name}')

    def get_deployment_services(self, pure_cenm: bool = False, deploy_without_angel: bool = False) -> List[DeploymentService]:
        """These services are returned in order they should be deployed

        For default deployments: do not change the order
        
        """
        if pure_cenm:
            if deploy_without_angel:
                return [
                    self.IDMAN,
                    self.SIGNER,
                    self.NMAP,
                    self.AUTH,
                    self.GATEWAY,
                    self.ZONE
                ]
            else:
                return [
                    self.AUTH,
                    self.GATEWAY,
                    self.ZONE,
                    self.IDMAN_ANGEL,
                    self.SIGNER,
                    self.NMAP_ANGEL
                ]
        else:
            if deploy_without_angel:
                return [
                    self.IDMAN,
                    self.SIGNER,
                    self.NOTARY, # Notary is not part of pure_cenm
                    self.NMAP,
                    self.AUTH,
                    self.GATEWAY,
                    self.ZONE
                ]
            else:
                # This is returned by default
                return [
                    self.AUTH,
                    self.GATEWAY,
                    self.ZONE,
                    self.IDMAN_ANGEL,
                    self.SIGNER,
                    self.NOTARY, # Notary is not part of pure_cenm
                    self.NMAP_ANGEL
                ]

    def get_database_services(self) -> List[BaseService]:
        return [service for service in self._get_all_services() if service.abb in self.db_services]

    def _raise_exception_group(self, errors: Dict[Tuple[str, str], Any]):
        if any(errors.values()):
            exceptions = []
            for (service, dir), error in errors.items():
                if error:
                    exceptions.append(ServiceError(service, dir))
            print("There were service that were not found, check the logs")
            raise ExceptionGroup("Combined service exceptions", exceptions)

    def download_all(self):
        # deprecated
        download_errors = {}
        for service in self._get_all_services():
            # deprecated
            download_errors[(f'{service.artifact_name}-{service.version}', service.dir)] = service.download()
        # this returns true or false depending on download error but return is not used
        self.db_manager.download()
        self.check_all()

    def check_all(self):
        check_errors = {}
        print("Validating services")
        for service in self._get_all_services():
            if (not service._check_presence()):
                check_errors[(f'{service.artifact_name}-{service.version}', service.dir)] = service.dir
                print(u'[\u274c] ' + f'{service.dir}/{service.artifact_name}-{service.version}')
            else:
                print(u'[\u2705] ' + f'{service.dir}/{service.artifact_name}-{service.version}')
        self._raise_exception_group(check_errors)
        print("Validating complete")

    def download_specific(self, services: List[str]):
        print("Downloading individual artifacts does not work with any other arguments, script will exit after downloading.")
        # deprecated
        download_errors = {}
        for service in services:
            try:
                service = self.get_service(service)
                # deprecated
                download_errors[(f'{service.artifact_name}-{service.version}', service.dir)] = service.download()
            except ValueError as e:
                # deprecated except: find a better way to handle this
                print(e)
                download_errors[service] = str(e)
        self.check_all()

    def deploy_all(self, health_check_frequency: int):
        self.check_all()
        self.config_manager.validate(self.get_deployment_services(deploy_without_angel=self.deploy_without_angel))
        self.PKI.validate_certificates(self.get_deployment_services(pure_cenm=True, deploy_without_angel=self.deploy_without_angel))
        self.deployment_manager.deploy_services(health_check_frequency)

    def deploy_nodes(self, health_check_frequency: int):
        node_manager = self._get_node_manager()
        self.config_manager.validate(node_manager.new_nodes)
        self.PKI.validate_certificates(node_manager.new_nodes)
        node_manager.deploy_nodes(health_check_frequency)

    def generate_certificates(self):
        self.check_all()
        self.config_manager.validate([*self.get_deployment_services(deploy_without_angel=self.deploy_without_angel), self.NODE, self.PKI])
        self.PKI.deploy()

    def clean_all(self,
        clean_deep: bool,
        clean_artifacts: bool,
        clean_certs: bool,
        clean_runtime: bool,
        clean_nodes: bool
    ):
        if clean_nodes:
            node_manager = self._get_node_manager()
            node_manager.clean_deployment_nodes(
                clean_deep,
                clean_artifacts,
                clean_certs,
                clean_runtime
            )
        else:
            for service in [*self.get_deployment_services(deploy_without_angel=self.deploy_without_angel), self.NODE, self.PKI]:
                if clean_deep:
                    service.clean_all()
                    continue
                if clean_artifacts:
                    service.clean_artifacts()
                if clean_certs:
                    service.clean_certificates()
                if clean_runtime:
                    service.clean_runtime()
            if any([clean_deep, clean_artifacts, clean_certs, clean_runtime]):
                self.sysi.remove(".logs/*", silent=True)
                self.sysi.remove(".tmp-*", silent=True)

    def clean_specific_artifacts(self, services: List[str]):
        print("Cleaning individual artifacts does not work with any other arguments, script will exit after downloading.")
        for service in services:
            try:
                service = self.get_service(service)
                service.clean_runtime()
                service.clean_artifacts()
            except ValueError as e:
                print(e)

    def versions(self):
        return self.printer.print_cenm_version()
