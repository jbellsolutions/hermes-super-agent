"""openswarm runtime: multi-agent deliverable production + fleet management.

Wraps vendor/openswarm. Owns a fleet of forked OpenSwarm instances, one per
business purpose. Each member runs in its own folder, on its own port, with
its own .env and vault attribution. See manifest.yaml.
"""
