# Soviet Jump Game — Server

A self-hosted replacement for the dead online services of **Soviet Jump Game**
(Steam AppID `1072710`, by Fantastic Passion / Game Grumps).

Ships as **one image with two roles**:

* **`sjg-api`** — a **FastAPI** service implementing the game's custom backend ("SovietAPI")
  plus the live **server registry** (the server browser).
* **`sjg-gameserver`** — the retail game itself run **headless under Wine**: this *is* the
  playable server. It registers itself with the backend and fills empty slots with bots.

Runs on **Windows**, **Linux**, and **Docker**.

This repo is the counterpart to
**[soviet-jump-game-patch](https://github.com/gfisher1/soviet-jump-game-patch)** (which points
the client here).

> **No game code is shipped.** The gameserver role needs your own legally-purchased copy of
> the game, mounted into the container. Everything else is here.

## Quick start (Docker)

```bash
export SJG_GAME_DIR="/path/to/Soviet Jump Game"   # your retail copy
export SJG_PUBLIC_HOST="sjg.example.com"          # the address clients should use
docker compose -f docker/docker-compose.yml up --build
```

That starts both roles:

| Role | Port | What it is |
| --- | --- | --- |
| `sjg-api` | `8080/tcp` | Backend the patched client talks to |
| `sjg-gameserver` | `42010/udp` | The actual gameplay server (Bolt over UDP) |

### Letting players in

Clients need the
**[soviet-jump-game-patch](https://github.com/gfisher1/soviet-jump-game-patch)** plugin.
Its installer asks the player to choose a play mode:

| Mode | What **MATCHMAKING** does |
| --- | --- |
| **online** (default) | Refreshes the server list, joins the first server it finds, and falls back to a local bot match if the backend is unreachable. |
| **offline** | Hosts a local bot match on the player's own PC — no server, no account, no internet. |

Point clients at your server with `Server.ApiBaseUrl` (the default is the public
`sjg.dnd.wtf`). With the patch installed, players **just click MATCHMAKING** — no console,
no hotkeys.

## Quick start (without Docker)

```bash
./run.sh        # Linux / macOS -> http://localhost:8080   (backend only)
.\run.ps1       # Windows
```

The gameplay server is the retail game run headless — see
[`gameserver/README.md`](gameserver/README.md).

## Status

| Piece | State |
| --- | --- |
| Mock backend (`/authenticate`, `/server/*`, `/player/ingame/*`) | ✅ |
| **Server browser** (`/servers` + heartbeat registry + static servers) | ✅ |
| **One combined image** (backend + headless gameserver) | ✅ |
| Headless game-server launcher (bring your own files) | ✅ |
| Auto server registration (heartbeat) | ✅ sent by the patch, from any host |
| Client PlayFab QoS stub → public matchmaking completes | ✅ in the patch repo |
| Bot backfill (a lone player never waits) | ✅ in the patch repo |
| Client ↔ server tie-in (`ApiBaseUrl`, auto-connect) | ✅ in the patch repo |
| Full online matchmaking roadmap | ✅ done — see [`docs/PROTOCOL.md`](docs/PROTOCOL.md) §4 |

## Prebuilt image (CI)

Every push to `main` and every `v*` tag builds and publishes
`git.gfi.sh/gfisher/soviet-jump-game-server:latest` to the Gitea container registry (see
[`.gitea/workflows/publish-docker.yml`](.gitea/workflows/publish-docker.yml)). The GitHub
mirror is at [github.com/gfisher1/soviet-jump-game-server](https://github.com/gfisher1/soviet-jump-game-server).

Each `v*` release also attaches a `docker load`-able tarball, for hosts that cannot reach the
registry — copy it over and:

```bash
docker load -i soviet-jump-game-server-v1.0.0.tar.gz
```

That loads `git.gfi.sh/gfisher/soviet-jump-game-server:v1.0.0` and `:latest`.

## Documentation

| Page | What's in it |
| --- | --- |
| [Configuration](https://github.com/gfisher1/soviet-jump-game-server/wiki/Configuration) | Environment variables |
| [Deployment](https://github.com/gfisher1/soviet-jump-game-server/wiki/Deployment) | Docker, compose, the game-files volume, the prebuilt image |
| [API](https://github.com/gfisher1/soviet-jump-game-server/wiki/API) | HTTP endpoints |
| [Static servers](https://github.com/gfisher1/soviet-jump-game-server/wiki/Static-Servers) | `SJG_STATIC_SERVERS` |
| [Headless server](https://github.com/gfisher1/soviet-jump-game-server/wiki/Headless-Server) | Run the retail game as a server |
| [Protocol](https://github.com/gfisher1/soviet-jump-game-server/wiki/Protocol) | Client ⇄ server contract |
| [Troubleshooting](https://github.com/gfisher1/soviet-jump-game-server/wiki/Troubleshooting) | Common problems |

## Layout

```
app/              FastAPI backend
docker/           Dockerfile (combined image) + docker-compose.yml + headless launcher
gameserver/       headless game-server notes + helper launcher
config/           env example
scripts/          release helper used by CI
.gitea/workflows  CI: builds/pushes the image, publishes releases on v* tags
docs/PROTOCOL.md
run.sh run.ps1    quick-start scripts (backend only)
```

## AI notice

This project - the backend, the Docker image and the release tooling - was built by
**opencode**, an AI coding agent, using **DeepSeek V4.1** as the model. Every change was
authored, built, deployed and tested by that agent.

## Legal / disclaimer

Reverse-engineered for interoperability and preservation, with the developer's permission,
using a legally purchased copy. **No game assets or binaries are included** — you must own
the game.

## License

MIT — see [LICENSE](LICENSE).
