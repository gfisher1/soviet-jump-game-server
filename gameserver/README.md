# Game server

The "server" in Soviet Jump Game is the retail game itself, run headless. There is no
separate dedicated-server binary in the shipped build.

## How it works

* `Packages.dll` → `Headless.IsHeadless()` is true when launched with `-batchmode`,
  `-nographics`, or when a `~HeadlessDebug.txt` file sits next to the exe.
* `Bolt.Samples.HeadlessServer.HeadlessServerManager` then loads a map from
  `PlayFabManager.TitleData.MapNames[MapIndex]` and creates a Bolt session.
* Networking uses the game's own **local UDP** transport
  (`BoltLauncher.SetUdpPlatform(BoltPro.DotNetPlatform)`), not the Photon cloud.

## Running it

```bash
# game files are yours; not shipped in this repo
./run-headless.sh "/path/to/Soviet Jump Game"
```

Run it alongside the backend (`docker compose up`) and point the client patch's
`ApiBaseUrl` at the backend.

## Remaining work (not done yet)

The shipped client build does **not** call `SovietAPI.SendServerHeartbeat`, so a headless
server does not announce its `IP:Port` to the backend by itself. To make
public/private matchmaking resolve to your server, one of:

1. Run the headless server on a **fixed** UDP port and have the backend return that
   `IP:Port` from `/server/public/{region}` (static config — simplest).
2. Add a small **server-side plugin component** (in the patch repo) that, once Bolt is
   serving, POSTs its endpoint to `/server/heartbeat` so the backend can hand it out.

Also required on the client side for the matchmaking path:

* Stub/emulate the **PlayFab QoS** step (`PlayFabQosApi.GetQosResultAsync`) that runs
  before `JoinPublicMatch`.

See `../docs/PROTOCOL.md` for the full contract.
