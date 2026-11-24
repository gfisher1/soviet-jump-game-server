# Soviet Jump Game — Server

A self-hosted replacement for the dead online services of **Soviet Jump Game**
(Steam AppID `1072710`, by Fantastic Passion / Game Grumps).

Ships as a **FastAPI** service that implements the game's custom backend
("SovietAPI") plus a **live server registry / browser**, and tooling to run the retail
game as a headless server. Runs on **Windows**, **Linux**, and **Docker**.

This repo is the counterpart to **[soviet-jump-game-patch](../soviet-jump-game-patch)**
(which points the client here).

## Status

| Piece | State |
| --- | --- |
| Mock backend (`/authenticate`, `/server/*`, `/player/ingame/*`) | ✅ |
| **Server browser** (`/servers` + heartbeat registry + static servers) | ✅ |
| Docker image + compose | ✅ |
| Headless game-server launcher | ✅ (uses your retail files) |
| Client ↔ server tie-in (`ApiBaseUrl`, console browser, direct connect) | ✅ in the patch repo |
| Auto server registration (heartbeat) | ✅ sender in the patch repo |
| Full online matchmaking (PlayFab QoS + join) | 🚧 roadmap — see [`docs/PROTOCOL.md`](docs/PROTOCOL.md) §4 |

> Offline single-player is fully working with the patch repo alone. This repo adds the
> server list/browser and the pieces needed for hosted games.

## Quick start — Linux / macOS

```bash
./run.sh                      # http://localhost:8080
curl -s http://localhost:8080/servers
```

## Quick start — Windows

```powershell
.\run.ps1                     # http://localhost:8080
Invoke-RestMethod http://localhost:8080/servers
```

## Quick start — Docker

```bash
docker compose -f docker/docker-compose.yml up --build
```

Then point the patched client at it — set `Server.ApiBaseUrl = http://<host>:8080/` in the
patch's `games.gfi.sjg.patch.cfg`, and use `sjg-refresh` / `sjg-servers` in-game.

## Prebuilt image (CI)

Every push to `main` and every `v*` tag builds and publishes
`git.gfi.sh/gfisher/soviet-jump-game-server:latest` to the Gitea container registry
(see [`.gitea/workflows/publish-docker.yml`](.gitea/workflows/publish-docker.yml)).

Each `v*` release also attaches a `docker load`-able tarball, for hosts that cannot reach
the registry (`<host>` with no route to `git.gfi.sh`) — copy it over and:

```bash
docker load -i soviet-jump-game-server-v1.0.0.tar.gz
```

That loads `git.gfi.sh/gfisher/soviet-jump-game-server:v1.0.0` and `:latest`.

---

## Server browser

The backend keeps a live registry of game servers:

* `POST /server/heartbeat` — a host advertises itself. The patch sends this automatically
  for matches you host (`RegisterWithServer = true`). The source IP is used if the body's
  `Address` is empty.
* `GET /servers` — the list shown by the in-game browser (`sjg-servers`).
* Servers idle for 20s are pruned.

### Static servers (no heartbeat needed)

Useful for fixed boxes / LAN / testing. Set `SJG_STATIC_SERVERS`:

```bash
# Linux/macOS
export SJG_STATIC_SERVERS="192.168.1.50:42010:Comrade's LAN Server,10.0.0.9:42011"
./run.sh
```

```powershell
# Windows
$env:SJG_STATIC_SERVERS = "192.168.1.50:42010:Comrade's LAN Server,10.0.0.9:42011"
.\run.ps1
```

Format: `host:port[:Name]` entries separated by `,` or `;`. They always appear in
`/servers`, and `sjg-join <n>` connects to them.

---

## Configuration (env)

| Var | Default | Meaning |
| --- | --- | --- |
| `SJG_PUBLIC_HOST` | `127.0.0.1` | Address handed to clients for the game server. |
| `SJG_GAME_PORT` | `42010` | UDP port of the game server. |
| `SJG_ACCOUNT_GROUP` | `Administrator` | `ApiAccountType` returned by `/authenticate`. |
| `SJG_JWT_SECRET` | `sjg-local-secret` | HS256 secret for the issued token. |
| `SJG_STATIC_SERVERS` | *(empty)* | Always-listed servers: `host:port[:Name],…`. |
| `HOST` / `PORT` | `0.0.0.0` / `8080` | Listen address/port (run scripts). |

## Protocol

The full reverse-engineered client ⇄ server contract is in
[`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## Headless game server

The "server" is the retail game run headless (`-batchmode`). See
[`gameserver/README.md`](gameserver/README.md) and [`gameserver/run-headless.sh`](gameserver/run-headless.sh).

## API endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/authenticate` | Login; returns `{token, group}` |
| GET | `/server/regions` | Region list |
| GET | `/servers` | **Server browser list** |
| POST | `/server/heartbeat` | Register a server |
| POST | `/server/private/create` · GET `/server/private/connect/{code}` | Private matches |
| GET | `/server/public/{region}` | Public matchmaking |
| GET | `/player/ingame/{playfabId}` | In-game check |
| GET | `/health` | Liveness |

## Layout

```
app/            FastAPI backend
docker/         Dockerfile + docker-compose.yml
gameserver/     headless game-server launcher + notes
config/         env example
scripts/        release helper used by CI
.gitea/workflows  CI: builds/pushes the image, publishes releases on v* tags
docs/PROTOCOL.md
run.sh run.ps1  quick-start scripts
```

## Legal / disclaimer

Reverse-engineered for interoperability and preservation, with the developer's
permission, using a legally purchased copy. **No game assets or binaries are included** —
you must own the game.

## License

MIT — see [LICENSE](LICENSE).
