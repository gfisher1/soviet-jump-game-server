# Soviet Jump Game — Server

A self-hosted replacement for the dead online services of **Soviet Jump Game**
(Steam AppID `1072710`, by Fantastic Passion / Game Grumps).

Ships as a **FastAPI** service that implements the game's custom backend ("SovietAPI") plus
a **live server registry** (the server browser), and tooling to run the retail game as a
headless server. Runs on **Windows**, **Linux**, and **Docker**.

This repo is the counterpart to
**[soviet-jump-game-patch](https://git.gfi.sh/gfisher/soviet-jump-game-patch)** (which points
the client here).

## Quick start

```bash
./run.sh                                                 # Linux / macOS -> http://localhost:8080
.\run.ps1                                                # Windows
docker compose -f docker/docker-compose.yml up --build   # Docker
```

Then point the patched client at it: set `Server.ApiBaseUrl = http://<host>:8080/` in the
patch's `games.gfi.sjg.patch.cfg` (the patch installer asks for this too, and defaults to
`sjg.dnd.wtf`).

## Status

| Piece | State |
| --- | --- |
| Mock backend (`/authenticate`, `/server/*`, `/player/ingame/*`) | ✅ |
| **Server browser** (`/servers` + heartbeat registry + static servers) | ✅ |
| Docker image + compose | ✅ |
| Headless game-server launcher | ✅ (uses your retail files) |
| Client ↔ server tie-in (`ApiBaseUrl`, direct connect) | ✅ in the patch repo |
| Auto server registration (heartbeat) | ✅ sender in the patch repo |
| Full online matchmaking (PlayFab QoS + join) | 🚧 roadmap — see [`docs/PROTOCOL.md`](docs/PROTOCOL.md) §4 |

> Offline single-player works with the patch repo alone. This repo adds the server
> list/browser and the pieces needed for hosted games.

## Prebuilt image (CI)

Every push to `main` and every `v*` tag builds and publishes
`git.gfi.sh/gfisher/soviet-jump-game-server:latest` to the Gitea container registry (see
[`.gitea/workflows/publish-docker.yml`](.gitea/workflows/publish-docker.yml)).

Each `v*` release also attaches a `docker load`-able tarball, for hosts that cannot reach the
registry — copy it over and:

```bash
docker load -i soviet-jump-game-server-v1.0.0.tar.gz
```

That loads `git.gfi.sh/gfisher/soviet-jump-game-server:v1.0.0` and `:latest`.

## Documentation

| Page | What's in it |
| --- | --- |
| [Configuration](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Configuration) | Environment variables |
| [Deployment](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Deployment) | Docker, compose, the prebuilt image |
| [API](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/API) | HTTP endpoints |
| [Static servers](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Static-Servers) | `SJG_STATIC_SERVERS` |
| [Headless server](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Headless-Server) | Run the retail game as a server |
| [Protocol](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Protocol) | Client ⇄ server contract |
| [Troubleshooting](https://git.gfi.sh/gfisher/soviet-jump-game-server/wiki/Troubleshooting) | Common problems |

## Layout

```
app/              FastAPI backend
docker/           Dockerfile + docker-compose.yml
gameserver/       headless game-server launcher + notes
config/           env example
scripts/          release helper used by CI
.gitea/workflows  CI: builds/pushes the image, publishes releases on v* tags
docs/PROTOCOL.md
run.sh run.ps1    quick-start scripts
```

## Legal / disclaimer

Reverse-engineered for interoperability and preservation, with the developer's permission,
using a legally purchased copy. **No game assets or binaries are included** — you must own
the game.

## License

MIT — see [LICENSE](LICENSE).
