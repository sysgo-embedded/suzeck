## Cluster configuration

We need to expose metric endpoints to optimize what we can measure. configuration can be applied via the following command: 
```bash
kind create cluster --name kubernetes --image kindest/node:v1.35.0 --config cluster-configuration.yaml
```

The current configuration exposes metrics for the following Kubernetes metrics:
- **kube-apiserver**: `/metrics`
- **kube-controller-manager**: `/metrics`
- **kube-scheduler**: `/metrics`
- **etcd**: `/metrics` (on port `2381`)
- **kube-proxy**: `/metrics`

## Network configuration
`routingMode=native` with `kubeProxyReplacement=true` eliminates several layers of `NAT` and `iptables` that would otherwise murder performance.
```bash
cilium install --version 1.18.6 \
  --set ipam.mode=kubernetes \
  --set ipv4NativeRoutingCIDR=172.20.0.0/16 \
  --set routingMode=native \
  --set autoDirectNodeRoutes=true \
  --set endpointRoutes.enabled=true \
  --set kubeProxyReplacement=true \
  --set bpf.masquerade=true \
  --set hubble.enabled=true \
  --set prometheus.enabled=true \
  --set debug.enabled=true
```

## API Priority and Fairness
This gives monitoring tools dedicated API capacity so they don’t get starved during load spikes.

Read more here: [API Priority and Fairness](https://kubernetes.io/docs/concepts/cluster-administration/flow-control/) and [Flow control](https://kubernetes.io/docs/reference/debug-cluster/flow-control/).