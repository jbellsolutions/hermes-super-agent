# Agent Zero Runtime

Super Agent adds Agent Zero as a visual/autonomous runtime on top of Agent OS.

## Local contract

- Agent Zero is a Docker service bound to `127.0.0.1:5080`.
- A0 connects the Agent Zero container/UI to the Mac host.
- Codex is exposed on the host through `/Users/home/.local/bin/codex` so Agent Zero can invoke the coding engine through A0.

## Use when

- A browser-visible autonomous interface is useful.
- A workflow benefits from watching the agent operate in a UI.
- You want Agent Zero to coordinate with local files/commands through A0.

## Do not use when

- A direct Hermes tool call or Codex CLI run is simpler.
- The task requires secrets that should not be exposed into a browser session.
- The task can be handled as a deterministic script or test command.
