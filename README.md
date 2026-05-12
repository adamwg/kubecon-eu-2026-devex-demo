# KubeCon EU 2026 Crossplane DevEx Demo

This is the demo script and supporting files for the DevEx demo in the
Crossplane maintainer talk at KubeCon EU 2026. It has been updated,
post-KubeCon, to reflect the state of the DevEx tooling as we add it to the
CLI. See git history for the historical demo.

## Setup

1. Clone [PR#10](https://github.com/crossplane/cli/pull/10) from the Crossplane
   CLI, which includes WIP DevEx features in the CLI, into an empty directory:

    ```shell
    git clone --revision refs/pull/10/head https://github.com/crossplane/cli.git crossplane-cli
    ```

2. Install the Crossplane CLI:

    ```shell
    cd crossplane-cli && go install ./cmd/crossplane
    ```

## Demo Script

1. Explore the help for the new features:

    ```shell
    crossplane --help
    crossplane project --help
    crossplane composition --help
    crossplane dependency --help
    crossplane function --help
    crossplane operation --help
    crossplane xrd --help
    ```

2. Initialize an empty project:

    ```shell
    crossplane project init hello-amsterdam && cd hello-amsterdam
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
      replicas: integer | default=1 minimum=1 maximum=100 description="Number of replicas to run"
      ports: "[]integer | default=[80] description=\"Ports to expose from the application container\""
    EOF
    ```

5. Generate an XRD from the example:

    ```shell
    crossplane xrd generate --from=simpleschema apis/webapps/schema.yaml
    echo
    echo "Here's what that command generated in apis/webapps/definition.yaml:"
    echo
    cat apis/webapps/definition.yaml
    ```

6. Generate a composition to compose resources based on the XRD:

    ```shell
    crossplane composition generate apis/webapps/definition.yaml
    echo
    echo "Here's what that command generated in apis/webapps/composition.yaml:"
    echo
    cat apis/webapps/composition.yaml
    ```

7. Add the core Kubernetes types as an API dependency, since we're going to
   compose k8s resources:

    ```shell
    crossplane dependency add k8s:v1.35.0
    echo
    echo "Here's what crossplane-project.yaml looks like after adding the dependency:"
    echo
    cat crossplane-project.yaml
    ```

8. Generate a composition function that we'll use to compose resources:

    ```shell
    crossplane function generate --language=python compose-webapp apis/webapps/composition.yaml
    echo
    echo "Here's what the composition looks like now:"
    echo
    cat apis/webapps/composition.yaml
    echo
    echo "And here's the new function, in functions/compose-webapp:"
    echo
    ls -l functions/compose-webapp
    ```

9. Write a function:
   1. Open the project in VSCode (`code .`).
   2. Create a Python venv using the `Create Environment` command in
      VSCode. Accept the defaults.
   3. Fill in the function by copying and pasting from `fn.py` into
      `function/fn.py`.
   4. Look at all the nice IDE features we get, like mouse-over docs and
      auto-completion.

10. Create an example XR:

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

11. Use render to show what the composition will produce:

    ```shell
    crossplane composition render --timeout=10m examples/webapp/podinfo.yaml apis/webapps/composition.yaml
    ```

12. Run the project and show what gets created:

    ```shell
    crossplane project run
    echo
    echo "That created a kind cluster for us:"
    echo
    kind get clusters
    echo
    echo "And also started a local registry in a container:"
    echo
    docker ps
    echo
    echo "Our configuration, and its embedded functions, are installed in the cluster:"
    echo
    kubectl get pkg
    echo
    echo "And the XRD we defined is available via the API server:"
    echo
    kubectl api-resources|grep example
    ```

13. Apply the example and see the composition work:

    ```shell
    kubectl apply -f examples/webapp/podinfo.yaml
    echo
    echo "Here's our webapp resource; let's wait for it to be ready:"
    echo
    kubectl get webapp
    kubectl wait --for=condition=ready=true webapp podinfo
    echo
    echo "We can see the deployment and service that were composed:"
    echo
    kubectl get deployment
    kubectl get service
    ```

14. Show the running composed application:

    ```shell
    kubectl port-forward svc/$(kubectl get svc -l crossplane.io/composite=podinfo -o jsonpath='{.items[0].metadata.name}') 9898 >/dev/null 2>&1 &
    open http://localhost:9898
    ```

15. Stop the local control plane and show the cleanup:

    ```shell
    # Shut down the port-forward from the previous step.
    kill %1
    # Stop the local dev environment.
    crossplane project stop
    kind get clusters
    docker ps
    ```
