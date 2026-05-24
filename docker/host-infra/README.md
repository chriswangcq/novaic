# NovAIC Host Infra

Host infra is the Docker-owned runtime package for the API machine.

This package owns API-host infrastructure services that are not nginx:

- Redis on `127.0.0.1:6379`
- coturn on TURN/STUN ports from the runtime `turnserver.conf`
- novaic-quic-service on UDP `443`

nginx intentionally remains host-managed because it is the public TCP `80/443`
ingress and certificate renewal boundary.

## Runtime Paths

- Compose package: `/opt/novaic/docker/host-infra`
- Compose env: `/opt/novaic/docker/host-infra.env`
- Redis data: `/opt/novaic/host-infra/redis`
- coturn config: `/opt/novaic/host-infra/coturn/turnserver.conf`
- TLS certificates: `/etc/letsencrypt` mounted read-only

The committed `turnserver.conf.example` is only a shape reference. The deploy
script copies the live `/etc/turnserver.conf` to the runtime path and never
commits TURN secrets.

## Deploy

```bash
./deploy host-infra
```

The deploy flow builds `novaic/quic-service:local`, saves/copies Redis RDB data,
copies coturn runtime config, disables the old host systemd services, starts the
Compose package, and verifies that Redis/coturn/QUIC listeners are Docker-owned.
