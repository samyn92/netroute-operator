
## Introduction

This is a Kubernetes operator written in Python, designed to reconcile network routes on containers. This operator ensures all network routes are correctly configured and in a desired state within your Kubernetes environment.

This can be helpful in environments where you need to use Multus for support of multiple network interfaces on pods.
## Features

- Verifies the state of network routes (```route -n```) in each container and reconciles if required.
  * Supports adding of IPv4 Routes
  * Supports adding of IPv6 Routes

## Installation & Development

### Pre-requisites

- Python 3.11+
- Kubernetes cluster

Clone the repository to your local machine:
```bash
$ git clone https://github.com/samyn92/netroute-operator
```

Install the required Python packages:
```bash
$ poetry install
```

Start the Server:
```bash
$ poetry run kopf run src/server.py
```

## Usage

Deploy ```netroute-operator``` to the Kubernetes Cluster
```bash
$ kubectl apply -f deploy/crd.yaml
$ kubectl apply -f deploy/rbac.yaml
$ kubectl apply -f deploy/deployment.py
```

Following CR can be used to add desired network routes to a ```targetPod``` running in a ```targetNamespace```

```bash
$ kubectl apply -f deploy/netroute.yaml
```

```yaml
apiVersion: samy.nitsche.io/v1
kind: netroute
metadata:
  name: netroute-example-2
spec:
  network: 192.168.150.0/24
  gateway: 10.1.0.1
  targetNamespace: default
  targetPod: busybox-test
  prune: True
```

If ```prune``` set to ```False```, the Pod Route will not be removed (even if you delete the ressource)
```bash
$ kubectl apply -f deploy/netroute.yaml
netroute.samy.nitsche.io/netroute-example-11 created
netroute.samy.nitsche.io/netroute-example-21 created
```

```bash
$ kubectl get netroutes
NAME                  READY   ROUTE                          APPLIED TO                   AGE
netroute-example-11   True    192.168.100.0/24 -> 10.1.0.1   Pod(default, busybox-test)   19s
netroute-example-21   True    192.168.150.0/24 -> 10.1.0.1   Pod(default, busybox-test)   19s
```
```bash
$ kubectl exec -it busybox-test -- route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.1.0.1        0.0.0.0         UG    0      0        0 eth0
10.1.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
192.168.100.0   10.1.0.1        255.255.255.0   UG    0      0        0 eth0
192.168.150.0   10.1.0.1        255.255.255.0   UG    0      0        0 eth0
```
