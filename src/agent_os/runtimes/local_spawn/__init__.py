"""Local-spawn runtime — spawn a Hermes superagent as a Docker container.

The Kaioken counterpart to vps_spawn. Same shape, same A2A contract,
but the spawned process lives in a container on the user's laptop
instead of a $24/mo DigitalOcean droplet.

This runtime is registered in job_router._ASYNC_RUNTIMES and selected
by route() when HERMES_MODE=kaioken AND the job tags include
`spawn-superagent` or `vps-spawn`.
"""
