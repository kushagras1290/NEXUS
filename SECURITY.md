# Security

Do not open public issues for suspected vulnerabilities. Report privately to the repository owner.

Production deployments must use OIDC, HTTPS, a real secrets manager, restricted network policies, encrypted storage, hardened OpenSearch/Qdrant credentials, and an explicit CORS allow-list. The development header-auth mode is intentionally rejected by startup validation when `NEXUS_ENV=production`.
