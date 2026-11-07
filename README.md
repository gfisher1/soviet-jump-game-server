# Soviet Jump Game — Server

A self-hosted replacement for the dead online services of **Soviet Jump Game**
(Steam AppID `1072710`, by Fantastic Passion / Game Grumps).

Ships as a Docker-friendly **FastAPI** service that implements the game's custom
backend ("SovietAPI"), plus tooling to run the retail game as a headless server.

This repo is the counterpart to **[soviet-jump-game-patch](../soviet-jump-game-patch)**
(which points the client here).

## Status

| Piece | State |
| --- | --- |
| Mock backend (`/authenticate`, `/server/*`, `/player/ingame/*`) | ✅ implemented |
| **Server browser** (`/servers` + heartbeat registry + static servers) | ✅ implemented |
| Docker image + compose | ✅ |
| Headless game-server launcher | ✅ (uses your retail files) |
| Client ↔ server tie-in (`ApiBaseUrl`, console browser, direct connect) | ✅ in the patch repo |
| Auto server registration (heartbeat) | ✅ client-side sender in the patch repo |
| Full online matchmaking (PlayFab QoS + join) | 🚧 roadmap — see `docs/PROTOCOL.md` §4 |

> Offline single-player is already fully working via the patch repo alone
> (`PRACTICE` starts a local server). This repo adds the server list/browser and the
> pieces needed for hosted games.

## Server browser

The backend keeps a live registry of game servers:

* `POST /server/heartbeat` — a host advertises itself (the patch sends this
  automatically for locally-hosted matches). The source IP is used if the body's
  `Address` is empty.
* `GET /servers` — the list shown by the in-game browser (`sjg-servers`).
* Servers idle for 20s are pruned.
* **Static servers** can be configured without any heartbeat:

```bash
export SJG_STATIC_SERVERS="192.168.1.50:42010:Comrade's LAN Server,10.0.0.9:42011"
```

Then the in-game browser lists them and `sjg-join <n>` connects.

## Protocol

The full reverse-engineered client ⇄ server contract lives in
[`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## Quick start

```bash
# Backend
docker compose -f docker/docker-compose.yml up --build
# -> http://localhost:8080

# Health check
curl -s http://localhost:8080/health
curl -s http://localhost:8080/server/regions
```

Then point the patched client at it. In
`BepInEx/config/games.gfi.sjg.patch.cfg`:

```ini
[Server]
ApiBaseUrl = http://127.0.0.1:8080/
```

## Configuration (env)

| Var | Default | Meaning |
| --- | --- | --- |
| `SJG_PUBLIC_HOST` | `127.0.0.1` | Address handed to clients for the game server. |
| `SJG_GAME_PORT` | `42010` | UDP port of the game server. |
| `SJG_ACCOUNT_GROUP` | `Administrator` | `ApiAccountType` returned by `/authenticate`. |
| `SJG_JWT_SECRET` | `sjg-local-secret` | HS256 secret for the issued token. |

## Layout

```
app/            FastAPI backend
docker/         Dockerfile + docker-compose.yml
gameserver/     headless game-server launcher + notes
docs/PROTOCOL.md
```

## Legal / disclaimer

Reverse-engineered for interoperability and preservation, with the developer's
permission, using a legally purchased copy. **No game assets or binaries are
included** — you must own the game.

## License

MIT — see [LICENSE](LICENSE).
