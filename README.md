# KubeCon EU 2026 Crossplane DevEx Demo

This is the demo script and supporting files for the DevEx demo in the
Crossplane maintainer talk at KubeCon EU 2026.

## Setup

1. Clone my Crossplane fork, which includes WIP DevEx features in the CLI:

    ```shell
     git clone -b awg/devex-poc https://github.com/adamwg/crossplane.git
    ```

2. Install the Crossplane CLI (`crank`):

    ```shell
    cd crossplane && go install ./cmd/crank
    ```

## Demo Script

1. Show the help for the new features:

    ```shell
    crank beta project --help
    ```

2. Initialize an empty project:

    ```shell
    crank beta project init hello-amsterdam && cd hello-amsterdam
    ```

3. Explore the project!

4. Create an API using simpleschema:

    ```shell
    mkdir apis/webapps
    cat <<EOF >apis/webapps/schema.yaml
    apiVersion: platform.example.com/v1alpha1
    kind: WebApp
    spec:
      image: string | required=true description="OCI image for the webapp"
      replicas: integer | default=1 minimum=1 maximum=100
      ports: "[]integer | default=[80]"
    EOF
    ```

5. Generate an XRD from the example:

    ```shell
    crank beta xrd generate --from=simpleschema apis/webapps/schema.yaml
    cat apis/webapps/definition.yaml
    ```

6. Generate a composition to compose resources based on the XRD:

    ```shell
    crank beta composition generate apis/webapps/xrd.yaml
    cat apis/webapps/composition.yaml
    ```

7. Generate a composition function that we'll use to compose resources:

    ```shell
    crank beta function generate --language=python compose-webapp apis/webapps/composition.yaml
    ```

8. Add the core Kubernetes types as an API dependency, since we're going to
   compose k8s resources:

    ```shell
    crank beta dependency add --api k8s:v1.35.0
    ```

9. Fill in the function (by copying and pasting from `function.py`). Show that
   we get nice IDE features like mouse-over docs and completion.

10. Run the project and show what gets installed:

    ```shell
    crank beta project run
    ```

11. Create an example XR:

    ```shell
    mkdir examples/webapp
    cat <<EOF >examples/webapp/podinfo.yaml
    apiVersion: platform.example.com/v1alpha1
    kind: WebApp
    metadata:
      name: podinfo
      namespace: default
    spec:
      image: docker.io/stefanprodan/podinfo:6.11.0
      replicas: 3
      ports: [9898]
    EOF
    ```

12. Apply the example and see the composition work:

    ```shell
    kubectl apply -f examples/webapp/podinfo.yaml
    kubectl get webapp
    kubectl get deployment
    kubectl get service
    ```

13. Show the running composed application:

    ```shell
    kubectl port-forward svc/podinfo-... 9898 &
    open http://localhost:9898
    ```
