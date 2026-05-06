"""Port allocator for the OpenSwarm fleet.

Range is [8080..8099] by default. The allocator probes `bind` before returning
so a port that's used by something outside the registry is skipped.
"""
from __future__ import annotations

import os
import socket

from . import registry

PORT_LOW = int(os.environ.get("OPENSWARM_PORT_LOW", "8080"))
PORT_HIGH = int(os.environ.get("OPENSWARM_PORT_HIGH", "8099"))


def _bindable(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def allocate(swarm_name: str) -> int:
    """Return a free port in range, never colliding with registry or live OS state.

    Does NOT mutate the registry. Caller is responsible for persisting the port
    via registry.add/update.
    """
    used = registry.used_ports()
    for port in range(PORT_LOW, PORT_HIGH + 1):
        if port in used:
            continue
        if not _bindable(port):
            continue
        return port
    raise RuntimeError(
        f"no free ports in [{PORT_LOW}..{PORT_HIGH}] for swarm {swarm_name!r}"
    )
