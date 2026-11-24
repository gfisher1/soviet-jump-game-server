# Headless game server

Soviet Jump Game has **no separate dedicated-server binary**: the "server" *is* the retail
game, run headless. This folder holds the launcher and the notes.

> **No game files are shipped with this repo.** You must own the game and mount your copy in.

## The short version

The combined image already contains a launcher, so the usual way to run a server is just
[`docker/docker-compose.yml`](../docker/docker-compose.yml):

```bash
export SJG_GAME_DIR="/path/to/Soviet Jump Game"
export SJG_PUBLIC_HOST="sjg.example.com"
docker compose -f docker/docker-compose.yml up --build
```

That starts the backend (`8080/tcp`) and the headless gameserver (`42010/udp`) together.

## What "headless" means

`Headless.IsHeadless()` (in `Packages.dll`) returns true when the game is launched with
`-batchmode`, `-nographics`, or when a `~HeadlessDebug.txt` file sits next to the executable.
The game then boots `Bolt.Samples.HeadlessServer.HeadlessServerManager`, which loads a map
from `PlayFabManager.TitleData.MapNames[MapIndex]` and creates a Bolt session.

Networking is the game's own **local UDP transport** (`BoltLauncher.SetUdpPlatform(BoltPro.DotNetPlatform)`)
— plain UDP, not the Photon cloud. See [`../docs/PROTOCOL.md`](../docs/PROTOCOL.md) §3.

## Running it by hand (no Docker)

[`run-headless.sh`](run-headless.sh) launches the retail game under Wine:

```bash
./run-headless.sh "/path/to/Soviet Jump Game" "Soviet Jump Game Map A"
```

Environment it sets: `WINEPREFIX` (default `$HOME/.sjg-wine`), `WINEDLLOVERRIDES="winhttp=n,b"`
(needed for the BepInEx loader), `WINEDEBUG=-all`.

## How players find it

1. **Registration.** The patch plugin sends `POST /server/heartbeat` every 5 s for any host
   it sees serving Bolt — including a headless server, because the plugin is loaded there too
   (BepInEx is part of the game folder). The backend prunes entries idle for 20 s.
2. **Discovery.** Patched clients `GET /servers`, pick a server, and `BoltPro.ConnectDirect`
   to its UDP address.
3. **No waiting.** The patch's bot backfill keeps the lobby filled: it targets
   `BotCount − (humans − 1)` bots, so a lone player is immediately in a full match and bots
   yield their slots as real players join.

Prefer a fixed, heartbeat-free listing (a locked-down box, a LAN, testing)? Set
`SJG_STATIC_SERVERS` on the backend instead — see
[Static servers](https://github.com/gfisher1/soviet-jump-game-server/wiki/Static-Servers).
