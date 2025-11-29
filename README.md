# Sahool Final Integrated V130 (One-file bundle)

This one ZIP includes:
- V47 original monolith (as V47_original.zip)
- Multi-repo platform scaffold (multi-repo/)
- Gateway-edge V62 (proxies+nanos+caching+limiting)
- Agent AI V70 (multi-repo/agent-ai)
- Sangfor SKE deployment assets V120 (V120_deploy/)

Next:
1. Split `multi-repo/*` folders into separate git repos.
2. Move real code from V47 into the appropriate repos (geo/imagery/etc.) if not already.
3. Build/push images, then deploy with Helm from V120_deploy/helm.