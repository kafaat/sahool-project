# Sangfor deployment notes

1. Registry: use Sangfor/Harbor private registry.
2. Storage: use Sangfor CSI (NFS/CEPH/local datastore).
3. Ingress: Nginx or Sangfor built-in; TLS via cert-manager if available.
4. Scaling: HPA for gateway-edge, imagery-core, agent-ai.