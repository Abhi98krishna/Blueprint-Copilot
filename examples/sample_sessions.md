# Sample Sessions

## Guided session: simple 2-service blueprint spec

**User:** What kind of application is this blueprint for?

**Blueprint Buddy:** Patterns from dsl-samples:

```
class lamp_v4_bp(Blueprint):
    """Application entry point: http://<haproxy_address>,
    HA Proxy Stats: http://<haproxy_address>:8080/stats"""

    services = [AHV_MySQLService, AHV_ApachePHPService, AHV_HAProxyService]
    packages = [AHV_MySQLPackage, AHV_ApachePHPPackage, AHV_HAProxyPackage, CENTOS_7_CLOUD]
    substrates = [MySQLSubstrate, AHV_ApachePHPSubstrate, AHV_HAProxySubstrate]
    profiles = [Default]
    credentials = [default_credential]
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L354-L362]

**User:** List the main components/services (comma-separated).

**Blueprint Buddy:** Patterns from dsl-samples:

```
class AHV_MySQLService(Service):
    """Service definition for our MySQL server"""

class AHV_ApachePHPService(Service):
    """Similar to the MySQL server, this is the definition for our Apache PHP
    server.  All VM specs are provided the same way, but note the Apache PHP
    servers have an explicit dependency on the MySQL server"""
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L39-L59]

**User:** Any dependencies between components? (comma-separated, e.g. web->db)

**Blueprint Buddy:** Patterns from dsl-samples:

```
class AHV_ApachePHPService(Service):
    ...
    dependencies = [ref(AHV_MySQLService)]
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L51-L62]

**User:** What runtime inputs/variables should users provide? (comma-separated)

**Blueprint Buddy:** Patterns from dsl-samples:

```
class DefaultProfile(Profile):
    # Deployments under this profile
    deployments = [NginxDeployment]

    # Profile Variables
    INSTANCE_PUBLIC_KEY = Variable.Simple(read_local_file(
        os.path.join("keys",
                     "centos_pub")), runtime=True)
    HOSTNAME = Variable.Simple("nginx-server", runtime=True)
```
[data/dsl-samples/nginx-with-php72/web.py:L114-L123]

**User:** Any day-2 actions to support? (comma-separated)

**Blueprint Buddy:** Patterns from dsl-samples:

```
class Default(Profile):
    ...
    @action
    def ScaleOut():
        """Profile action for scaling out our web servers"""
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L249-L262]

**User:** Target environment label (e.g., AHV, ESXi, AWS)?

**Blueprint Buddy:** Patterns from dsl-samples:

```
class MySQLSubstrate(Substrate):
    ...
    os_type = "Linux"
    provider_type = "AHV_VM"
    provider_spec = read_ahv_spec(
        "specs/ahv/ahv-mysql-spec.yaml", disk_packages={1: CENTOS_7_CLOUD}
    )
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L151-L162]

## Ask mode: Q&A with citations

**User:** Where do sample blueprints define profile variables?

**Blueprint Buddy:**

```
class DefaultProfile(Profile):

    # Deployments under this profile
    deployments = [NginxDeployment]

    # Profile Variables
    INSTANCE_PUBLIC_KEY = Variable.Simple(read_local_file(
        os.path.join("keys",
                     "centos_pub")), runtime=True)
    HOSTNAME = Variable.Simple("nginx-server", runtime=True)
    ENABLE_ACCESS_LOG = Variable.WithOptions.Predefined.string(
        ["yes", "no"], default="no", is_mandatory=True, runtime=True
    )
    STATIC_EXPIRATION_DAYS = Variable.Simple("365", runtime=True)
```
[data/dsl-samples/nginx-with-php72/web.py:L114-L127]

**User:** Is there an example of a service dependency?

**Blueprint Buddy:**

```
class AHV_ApachePHPService(Service):
    ...
    dependencies = [ref(AHV_MySQLService)]
```
[data/dsl-samples/lamp-v4/lamp-v4.py:L51-L62]
