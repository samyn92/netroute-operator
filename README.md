## Features

* Simple, but powerful:
  * A full-featured Kubernetes operator managing Pod configuration definitions
  * Marshalling of resources' data to the handlers' kwargs.
  * Marshalling of handlers' results to the resources' statuses.
  * Publishing of logging messages as Kubernetes events linked to the resources.
* Supports Pod configuration definitions
  * Supports adding of IPv4 Routes
  * Supports adding of IPv6 Routes
  * Supports adding of VPP Routes

## Poetry
* ```poetry install``` -- install packages from pyproject.toml / poetry.lock
* ```poetry add {package_name}``` -- adds package to virtual environment
* ```poetry add -D {package_name}``` -- adds package to virtual environment (as development addon)
* ```poetry show --tree``` -- show packages with dependencies


## Usage

Deploy ```route-manager``` to the Kubernetes Cluster

```bash
$ kubectl apply -f kubernetes/crd.yaml
$ kubectl apply -f kubernetes/pod-route-manager.py
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: route-manager
spec:
  containers:
  - name: app
    image: route-manager:latest
    imagePullPolicy: Never
    env:
    - name: USE_INCLUSTER
      value: "False"
```

Following CRD can be used to add desired network routes to a ```targetPod``` and ```targetNamespace```

```bash
$ kubectl apply -f kubernetes/netroute.yaml
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
$ kubectl apply -f kubernetes/netroute.yaml
netroute.samy.nitsche.io/netroute-example-11 created
netroute.samy.nitsche.io/netroute-example-21 created
```

```bash
$ kubectl get netroutes
NAME                  READY   ROUTE                          APPLIED TO                   AGE
netroute-example-11   True    192.168.100.0/24 -> 10.1.0.1   Pod(default, busybox-test)   19s
netroute-example-21   True    192.168.150.0/24 -> 10.1.0.1   Pod(default, busybox-test)   19s

$ kubectl exec -it busybox-test -- /bin/bash
/ # route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.1.0.1        0.0.0.0         UG    0      0        0 eth0
10.1.0.0        0.0.0.0         255.255.0.0     U     0      0        0 eth0
192.168.100.0   10.1.0.1        255.255.255.0   UG    0      0        0 eth0
192.168.150.0   10.1.0.1        255.255.255.0   UG    0      0        0 eth0
/ # 

```
