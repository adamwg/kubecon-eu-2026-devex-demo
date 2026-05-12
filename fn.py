"""A Crossplane composition function."""

import grpc
from crossplane.function import logging, response, resource
from crossplane.function.proto.v1 import run_function_pb2 as fnv1
from crossplane.function.proto.v1 import run_function_pb2_grpc as grpcv1

from models.com.example.platform.webapp import v1alpha1
from models.io.k8s.api.apps import v1 as appsv1
from models.io.k8s.api.core import v1 as corev1
from models.io.k8s.apimachinery.pkg.apis.core.meta import v1 as metav1
from models.io.k8s.apimachinery.pkg.util import intstr

class FunctionRunner(grpcv1.FunctionRunnerService):
    """A FunctionRunner handles gRPC RunFunctionRequests."""

    def __init__(self):
        """Create a new FunctionRunner."""
        self.log = logging.get_logger()

    async def RunFunction(
        self, req: fnv1.RunFunctionRequest, _: grpc.aio.ServicerContext
    ) -> fnv1.RunFunctionResponse:
        """Run the function."""
        log = self.log.bind(tag=req.meta.tag)
        log.info("Running function")

        rsp = response.to(req)

        xr = v1alpha1.WebApp(**resource.struct_to_dict(req.observed.composite.resource))

        assert xr.metadata is not None
        assert xr.metadata.name is not None
        assert xr.spec.ports is not None

        labels = {"app.kubernetes.io/name": xr.metadata.name}
        ports = xr.spec.ports

        dply = appsv1.Deployment(
            metadata=metav1.ObjectMeta(
                labels=labels,
            ),
            spec=appsv1.DeploymentSpec(
                selector=metav1.LabelSelector(
                    matchLabels=labels,
                ),
                replicas=xr.spec.replicas,
                template=corev1.PodTemplateSpec(
                    metadata=metav1.ObjectMeta(
                        labels=labels,
                    ),
                    spec=corev1.PodSpec(
                        containers=[
                            corev1.Container(
                                name="app",
                                image=xr.spec.image,
                                ports=[corev1.ContainerPort(containerPort=p) for p in ports],
                            )
                        ]
                    ),
                ),
            ),
        )

        resource.update(rsp.desired.resources["deployment"], dply)

        svc = corev1.Service(
            metadata=metav1.ObjectMeta(
                labels=labels,
            ),
            spec=corev1.ServiceSpec(
                ports=[corev1.ServicePort(port=p, targetPort=intstr.IntOrString(p)) for p in ports],
                selector=labels,
            ),
        )

        resource.update(rsp.desired.resources["service"], svc)

        return rsp
