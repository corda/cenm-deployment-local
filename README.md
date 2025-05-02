# cenm-deployment-local

## &#9888; Important information for Java 17

This branch supports an experimental implementation for deployments on multiple Java versions. As this is an experimental feature this may not work as intended unless the setup is followed correctly.

### Java version setup

This implementation works by un-setting and setting the `JAVA_HOME` env var per service that is deployed on a separate process. To alter the `JAVA_HOME` path correctly your Java versions need to be installed in the same folder with the same name pattern, e.g.

```bash
$ ls /Library/Java/JavaVirtualMachines
zulu-8.jdk
zulu-17.jdk
```

This follows the pattern `zulu-<java-version-number>.jdk`.

You need to do this for all versions of Java that are required to run the services you need to deploy e.g. if you are running Java 8 services together with Java 17 services, you need to make sure both Java 8 and Java 17 JDK versions are installed with the correct naming convention before deploying.

### `JAVA_HOME`

Before deploying please make sure that your `JAVA_HOME` is being set correctly in your `.bashrc` (or equivalent), the script will not run without it. You can check if this is already being done by running:

```bash
echo $JAVA_HOME
/Library/Java/JavaVirtualMachines/zulu-8.jdk/Contents/Home
```

If this doesn't return anything then you need to export `JAVA_HOME` as an environment variable.

```bash
export JAVA_HOME='/Library/Java/JavaVirtualMachines/<java-install-folder-name>/Contents/Home'
```

It is recommended that you then add this line to your `.bashrc` corresponding to the java version you want to run by default in your terminal so you do not have to set this every time.

```bash
echo "export JAVA_HOME='/Library/Java/JavaVirtualMachines/<java-install-folder-name>/Contents/Home'" >> .bashrc
```

## Introduction

This is a complete Python framework for deploying an enterprise grade CENM deployment in a local environment for testing related purposes. This is the host repo to tie in separate CENM service config repos. Features of this framework include:

- Download CENM artifacts, including plugins, database drivers and Corda node CorDapps
- Generating a CENM PKI and distributing certificates to all CENM services.
- Quickly deploy and stop a complete CENM network

## Getting started

1. Clone this repo locally:

    ```shell
    git clone https://github.com/tomstark99/cenm-deployment-local.git
    ```

2. Copy and rename the `.env.template` file to `.env`, here you will fill in your credentials

    ```shell
    cd cenm-deployment-local && cp .env.template .env
    ```

3. Now open the `.env` file and fill in the config options (there are default versions already configured)

    ```shell
    ARTIFACTORY_USERNAME=<some>.<one>@r3.com
    ARTIFACTORY_API_KEY=<api_key>
    AUTH_VERSION=<auth_version>
    GATEWAY_VERSION=<gateway_version>
    CENM_VERSION=<cenm_version>
    NMS_VISUAL_VERSION=<nms_visual_version>
    NOTARY_VERSION=<corda_version>
    NODE_PLUGIN_VERSION=<node_management_plugin_version>
    FLOW_PLUGIN_VERSION=<flow_management_plugin_version>
    ```

    _Note: It is not recommended that you use a Corda version lower than 4.8.X these versions are no longer supported and might cause deployment problems._

4. The `pyhocon` package is required for this script to work, install this in your python installation using

    > <font color="orange">&#9888; If you have more than one python installation then your default `pip` command may default to a different installation than your default `python` or `python3` command. If this is the case you may get errors that the `pyhocon` package still couldn't be found after installing it. Make sure you use the correct pip command for the python installation.</font>

    ```shell
    pip install pyhocon
    ```

5. Once you have saved this file, you can run the Python script with the following options.

    ```
    $ python3 setup_script.py -h
    usage: setup_script.py [-h]
                           [--setup-dir-structure]
                           [--download-individual DOWNLOAD_INDIVIDUAL]
                           [--generate-certs]
                           [--run-default-deployment]
                           [--run-node-deployment RUN_NODE_DEPLOYMENT]
                           [--deploy-without-angel]
                           [--nodes]
                           [--clean-runtime]
                           [--clean-certs]
                           [--clean-artifacts]
                           [--deep-clean]
                           [--clean-individual-artifacts CLEAN_INDIVIDUAL_ARTIFACTS]
                           [--health-check-frequency HEALTH_CHECK_FREQUENCY]
                           [--validate]
                           [--version]

    A modular framework for local CENM deployments and testing.

    options:
    -h, --help            show this help message and exit
    --setup-dir-structure
                            Create directory structure for CENM deployment and download all current artifacts
    --download-individual DOWNLOAD_INDIVIDUAL
                            Download individual artifacts, use a comma separated string of artifacts to download e.g.
                            "pki-tool,identitymanager" to download the pki-tool and identitymanager artifacts
    --generate-certs      Generate certificates and distribute them to services
    --run-default-deployment
                            Runs a default deployment, following the steps from README
    --run-node-deployment RUN_NODE_DEPLOYMENT
                            Run node deployments for a given number of nodes
    --deploy-without-angel
                            Deploys services without the angel service
    --nodes               To be used together with clean arguments to specify cleaning for node directorie
    --clean-runtime       Remove all generated runtime files
    --clean-certs         Remove all generated certificates
    --clean-artifacts     Remove all downloaded artifacts
    --deep-clean          Remove all generated service folders
    --clean-individual-artifacts CLEAN_INDIVIDUAL_ARTIFACTS
                            Clean individual artifacts, use a comma separated string of artifacts to download e.g.
                            "pki-tool,identitymanager" to clean the pki-tool and identitymanager artifacts
    --health-check-frequency HEALTH_CHECK_FREQUENCY
                            Time to wait between each health check, default is 30 seconds
    --validate            Check which artifacts are present
    --version             Show current cenm version
    ```

### Setup Directory Structure

To set up your directory structure and certificates so that you can start your CENM deployment there are two commands in the script that can be run simultaneously:

```shell
python3 setup_script.py --setup-dir-structure --generate-certs
```

This will download all the correct config files into the correct directories as well as download all required CENM artifacts with the versions specified in `.env` file at the start. After this has completed you can move onto deploying your CENM network which can either be done automatically or manually. For automatically deploying a default CENM setup see the [One-line auto-deployment](#one-line-auto-deployment) section.

In most cases it is recommended to let the script deploy CENM for you, this way it is much less likely that something will go wrong. If however you need to change the order of deployment or tweak a config or database setup due to the testing circumstances you can manually deploy CENM using the steps in the [Deployment Order](#deployment-order) section.

## One-line auto-deployment

If you just need a default enterprise deployment of CENM then you can skip having to run the manual commands in the [Deployment Order](#deployment-order) section. This command can also be run together with the two commands from the section above, for a full 'one-line' deployment experience:

```shell
python3 setup_script.py --setup-dir-structure --generate-certs --run-default-deployment
```

You can also run this command after making any config adjustments and adding plugins that need testing for example:

```shell
python3 setup_script.py --clean-runtime --run-default-deployment
```

This runs all the commands from the [Deployment Order](#deployment-order) section in python subprocesses, the python program won't exit until you shut down the CENM deployment with a `Ctrl+C`.

A health check runs on the subprocesses every 30 seconds and will restart services if they become unhealthy.

### CENM Environment Re-deployment

Sometimes you may have missed something in your config or setup and need to re-deploy, or you want to shut down your existing network, do some changes and then deploy again.

You can stop a running CENM deployment with a keyboard interrupt `Ctrl+C`, this will gracefully stop all services and shutdown your network. If you then want to start the **same** network again with the same databases and registered nodes, you can do this by running:

```shell
python3 setup_script.py --run-default-deployment
```

without the `--clean-runtime` flag, this will start up your network and skip over any 'first-time' setup.

### Node and Flow Management Plugins

Configuration needs to be specified in gateway.conf for the node and flow management plugins. Currently the following
configuration has been specified in gateway.conf. This is the same in both private and public gateway directories.

```
node.management.plugin.middleware {
    rpcUsername ="testuser"
    rpcPassword ="password"
    rpcHost = "127.0.0.1"
    rpcPort = 60012
}

flow.management.plugin.middleware {
    rpcUsername ="testuser"
    rpcPassword ="password"
    rpcHost = "127.0.0.1"
    rpcPort = 60012
}
```
It would be a useful enhancement to this script to insert in gateway.conf the details of nodes this 
script spins up, if it does spin up any. This is not currently implemented. The gateway.conf by default is the
above, however it can also be manually edited.

## Deployment Order

CENM services should be deployed in a particular order, this being:

1. If you have not previously run the python scirpt with the `--generate-certs` flag then do this now
    
    ```shell
    python3 setup_script.py --generate-certs
    ```
    
    This will run the pki tool and copy the generated certificates into the correct locations for each service

2. Start the auth service

    ```shell
    java -jar accounts-application.jar \
        -f ./auth.conf \
        --initial-user-name admin \
        --initial-user-password p4ssWord \
        --keep-running \
        --verbose
    ```
    
3. Start the private gateway service

    ```shell
    java -jar gateway-service.jar -f private.conf
    ```

    > <font color="orange">&#9888; The public gateway service is optional and is not covered in the setup for this deployment. The public gateway service is intended for a real-world deployment where you want to provide gateway access for standard network users which doesn't include the user admin control options.
    > 
    > Step 6-9 of this guide are focused on auth/gateway setup where, for the purpose of this deployment only the private gateway is configured. The private gateway has all the functionality of the public one so unless you are doing specific public gateway testing it is recommended you ignore it.</font>

    You can deploy the public gateway in the same way as the private gateway:

    ```shell
    java -jar gateway-service.jar -f public.conf
    ```
    
4. Start the zone service

    ```shell
    java -jar zone.jar \
        --driver-class-name=org.h2.Driver \
        --jdbc-driver= \
        --user=zoneuser \
        --password=password \
        --url='jdbc:h2:file:./h2/zone-persistence;DB_CLOSE_ON_EXIT=FALSE;LOCK_TIMEOUT=10000;WRITE_DELAY=0;AUTO_SERVER_PORT=0' \
        --run-migration=true \
        --enm-listener-port=5061 \
        --admin-listener-port=5063 \
        --auth-host=127.0.0.1 \
        --auth-port=8081 \
        --auth-trust-store-location certificates/corda-ssl-trust-store.jks \
        --auth-trust-store-password trustpass \
        --auth-issuer "http://test" \
        --auth-leeway 5 \
        --tls=true \
        --tls-keystore=certificates/corda-ssl-identity-manager-keys.jks \
        --tls-keystore-password=password \
        --tls-truststore=certificates/corda-ssl-trust-store.jks \
        --tls-truststore-password=trustpass
    ```

5. Verify your gateway is up by navigating to http://localhost:8089 where you should see a login screen.

6. Run setupAuth initially to create users in the global zone:

    ```shell
    cd cenm-auth/setup-auth
    bash setupAuth.sh
    ```

    _Note: this script requires [jq](https://stedolan.github.io/jq/download/), a command line JSON processor that can be installed easily in various ways._

7. Set the identity manager config using the CENM CLI-tool

    Navigate to the cenm-tool directory

    ```shell
    cd cenm-gateway/cenm-tool
    ```

    First set your global zone config for identity manager:

    ```shell
    ./cenm context login -s http://127.0.0.1:8089 -u config-maintainer -p <password>
    ./cenm identity-manager config set-admin-address -a=127.0.0.1:5053
    ./cenm identity-manager config set -f=identitymanager-init.conf --zone-token
    ./cenm context logout http://127.0.0.1:8089
    ```

    _Note: Make a note of the token returned from the `--zone-token` command it is needed for the next step._

8. Start the Angel service for `IDENTITY_MANAGER`

    Using the zone token generated from the step above, start the Angel service for the Identity Manager.

    ```shell
    java -jar angel.jar \
        --jar-name=identitymanager.jar \
        --zone-host=127.0.0.1 \
        --zone-port=5061 \
        --token=<idman-zone-token> \
        --service=IDENTITY_MANAGER \
        --polling-interval=10 \
        --working-dir=./ \
        --tls=true \
        --tls-keystore=./certificates/corda-ssl-identity-manager-keys.jks \
        --tls-keystore-password=password \
        --tls-truststore=./certificates/corda-ssl-trust-store.jks \
        --tls-truststore-password=trustpass \
        --verbose
    ```
    
9. Start the signer service

    ```shell
    java -jar signer.jar -f signer.conf
    ```

    _Note: While the Signer can also be deployed using the Angel service this is not the default behavior of the CENM helm chat deployment and therefore is not covered in this guide._

10. Register the notary

    ```shell
    java -jar corda.jar initial-registration \
        -f notary.conf
        --network-root-truststore ./certificates/network-root-truststore.jks \
        --network-root-truststore-password trustpass
    ```
    
11. Update the `network-parameters-init.conf` file with the correct `nodeInfo`

    When the notary is registered with the network it generates a `nodeInfo-XXXXX...` file. The name of this file needs to replace the `INSERT_NODE_INFO_FILE_NAME_HERE` placeholder in the `cenm-nmap/network-parameters-init.conf` file e.g.
    
    ```properties
    notaries : [
        {
            notaryNodeInfoFile: "nodeInfo-DFD4D403F65EA6C9B33B653A8B855CB3C4F04D599B373E662EBD2146241219F2"
            validating = false
        }
    ]

    minimumPlatformVersion = 4
    maxMessageSize = 10485760
    maxTransactionSize = 10485760
    eventHorizonDays = 10 # Duration in days
    ```
    
    The `nodeInfo-XXXXX...` file should also be copied to the `cenm-nmap/` folder
    
    ```shell
    cp cenm-notary/nodeInfo-* cenm-nmap/
    ```
    
12. Set network parameters

    ```shell
    java -jar networkmap.jar \
        -f networkmap-init.conf \
        --set-network-parameters network-parameters-init.conf \
        --network-truststore ./certificates/network-root-truststore.jks \
        --truststore-password trustpass \
        --root-alias cordarootca
    ```

13. Create a 'Main' subzone

    Navigate to the cenm-tool directory

    ```shell
    cd cenm-gateway/cenm-tool
    ```

    To create a subzone, you need the `network-maintainer` login:

    ```shell
    ./cenm context login -s http://127.0.0.1:8089 -u network-maintainer -p <password>
    ./cenm zone create-subzone \
        --config-file=../../cenm-nmap/networkmap-init.conf \
        --network-map-address=127.0.0.1:20000 \
        --network-parameters=../../cenm-nmap/network-parameters-init.conf \
        --label=Main \
        --label-color='#941213' \
        --zone-token
    ./cenm context logout http://127.0.0.1:8089
    ```

    Make a note of the zone tokens that are returned in case you need it later (for example if you are using the angel service).

    Next set your signer config globally:

    ```shell
    ./cenm context login -s http://127.0.0.1:8089 -u config-maintainer -p <password>
    ./cenm signer config set-admin-address -a=127.0.0.1:5054
    ./cenm signer config set -f=signer.conf
    ```

    Get your subzone id:

    ```shell
    ./cenm zone get-subzones
    ```

    Set your network map config for the subzone and replace the `<SUBZONE_ID>` with the id returned from:

    ```shell
    ./cenm netmap config set -s <SUBZONE_ID> -f=networkmap-init.conf
    ./cenm context logout http://127.0.0.1:8089
    ```
    
    
14. Start the Angel service for `NETWORK_MAP`

    Using the zone token generated from the step above, start the Angel service for the Network Map.

    ```shell
    java -jar angel.jar \
    --jar-name=networkmap.jar \
    --zone-host=127.0.0.1 \
    --zone-port=5061 \
    --token=<nmap-zone-token> \
    --service=NETWORK_MAP \
    --polling-interval=10 \
    --working-dir=./ \
    --network-truststore=./certificates/network-root-truststore.jks \
    --truststore-password=trustpass \
    --root-alias=cordarootca \
    --network-parameters-file=network-parameters.conf \
    --tls=true \
    --tls-keystore=./certificates/corda-ssl-network-map-keys.jks \
    --tls-keystore-password=password \
    --tls-truststore=./certificates/corda-ssl-trust-store.jks \
    --tls-truststore-password=trustpass \
    --verbose
    ```
    
15. Start the notary

    ```shell
    java -jar corda.jar -f notary.conf
    ```
    
    _Note: you may have to wait while the network parameters that were set in step 5 are signed, this can take a few minutes._
    
16. To grant your users access to the new subzone, replace the `<SUBZONE_ID>` with the id returned from this command:

    ```shell
    ./cenm context login -s http://127.0.0.1:8089 -u config-maintainer -p <password>
    ./cenm zone get-subzones
    ```

    The user roles are located in the cenm-auth directory, in the example below the zone id is `1` which should be substituted `"s//<here>/g"` in the `perl` command below:

    ```shell
    cd cenm-auth/setup-auth/roles
    for file in *.json; do perl -i -pe "s/<SUBZONE_ID>/1/g" $file; done
    ```

    After this run setupAuth again:

    ```shell
    setupAuth.sh
    ```

    _Note: this script requires [jq](https://stedolan.github.io/jq/download/), a command line JSON processor that can be installed easily in various ways._
    

