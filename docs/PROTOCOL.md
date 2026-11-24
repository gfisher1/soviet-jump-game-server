# Client ⇄ Server protocol (reverse-engineered)

Everything here was recovered by decompiling `SovietJumpGame_Data/Managed/Scripts.dll`
(Unity 2019.4.10f1, Mono). It is the contract the **patch** and the **server** share.

## 1. The original (dead) chain

```
Steam (Facepunch.Steamworks, AppID 1072710)
   │  GetAuthSessionTicket
   ▼
PlayFab  PlayFabClientAPI.LoginWithSteam(...)      → dead: "API usage limits for the title"
   │  SessionTicket
   ▼
api.fantasticpassion.games  POST /authenticate      → dead: domain gone
```

Menu gate (`OptionsMenu`/`TitleMenu` state machine, `WaitingForAuth`):

```csharp
if ((PlayFabManager.AuthenticationError == null && ForceUpdatePlayFab.Initialized) || SkipAuth)
    -> MainMenu
```

`ForceUpdatePlayFab.AuthenticationRoutine` blocks forever until
`PlayFabManager.CurrentPlayer != null && PlayFabManager.TitleData.Initialized`.

## 2. Custom backend ("SovietAPI") contract

Base URL: `https://api.fantasticpassion.games` (`EPB.Networking.Backend.SovietAPI.BASE_API_URL`).

Headers set on every request:

| Header | Value |
| --- | --- |
| `X-API-Key` | `1164952a-ef7a-470b-a22a-f60966c81482` |
| `X-FP-Authentication` | the JWT from `/authenticate` (once known) |
| `X-SJG-Version` | client build date |
| `Content-Type` | `text/plain` or `application/json` (depends on body) |

| Method | Path | Body | Response |
| --- | --- | --- | --- |
| POST | `/authenticate` | PlayFab session ticket (raw text) | `{"token":"<jwt>","group":"Normal\|VIP\|Administrator"}` |
| GET | `/server/regions` | – | `["USSR","Development", ...]` (ServerRegion enum names) |
| POST | `/server/private/create` | private code (text) | `MinimalServerInstance` |
| GET | `/server/private/connect/{code}` | – | `MinimalServerInstance` |
| GET | `/server/public/{region}?auto={bool}` | – | `MinimalServerInstance` |
| POST | `/server/heartbeat` | `ServerInstance` (json) | – |
| GET | `/player/ingame/{playfabId}` | – | `true`/`false` |

`MinimalServerInstance`:

```json
{ "Success": true, "ServerId": "ABC123", "IP": "127.0.0.1", "Port": 42010,
  "PlayerCount": 1, "Hostname": null, "ConnectToken": "<opaque>" }
```

`ServerRegion` enum: `Unknown, AustraliaEast, AustraliaSoutheast, BrazilSouth, CentralUs,
EastAsia, EastUs, EastUs2, JapanEast, JapanWest, NorthCentralUs, NorthEurope,
SouthCentralUs, SoutheastAsia, WestEurope, WestUs, ChinaEast2, ChinaNorth2,
SouthAfricaNorth, Development, USSR`.

The JWT payload decodes to `ApiUser { PlayFabId, MasterAccountId, SteamId, AccountType }`.
The client decodes it **without verifying** (`JWT_SECRET_KEY` ships empty), so any
HS256 JWT whose payload is that JSON is accepted.

## 3. Game server / transport (Bolt)

- The client's networking is **Photon Bolt over the game's own UdpKit transport**, and
  `NetworkCallbacks.BoltStartBegin` installs the **local UDP platform**:
  `BoltLauncher.SetUdpPlatform(BoltPro.DotNetPlatform)` — i.e. **plain UDP, no Photon cloud**.
- Matchmaking: `SovietAPI.JoinPublicMatch(region)` → `MinimalServerInstance` →
  `BoltPro.Connect(new UdpEndPoint(IP, Port), authToken)`.
- Private: `POST /server/private/create` then connect to the returned IP:Port with the code.
- **Offline practice** (`TitleMain.Practice`): the client calls
  `BoltLauncher.StartServer(UdpEndPoint.Any, "Soviet Jump Game Tutorial")` — a purely local
  server. This is why the patch alone already gives a playable game.
- Headless server: run the game with `-batchmode` (or `-nographics`, or a `~HeadlessDebug.txt`).
  `Bolt.Samples.HeadlessServer.HeadlessServerManager` then loads a map from
  `PlayFabManager.TitleData.MapNames[MapIndex]` and `BoltMatchmaking.CreateSession(...)`.

`AuthProtocolToken` (sent to the game server as the connection token):
`{ PlayFabId, PlayFabToken, AuthToken, ConnectToken, Code, LobbyId }`.

## 4. Online-style play: these are now implemented

All three pieces below are shipped — client side in the
[soviet-jump-game-patch](https://github.com/gfisher1/soviet-jump-game-patch) plugin, server
side in this repo.

1. **PlayFab QoS** — `MatchConnection.ConnectToMatchmaking` starts with
   `new PlayFabQosApi().GetQosResultAsync()`, which throws with no PlayFab. The patch stubs it
   (`Patches.QosResultAsync_Prefix`, returning an empty `QosResult`), so the join path
   (`SovietAPI.JoinPublicMatch` → `BoltPro.Connect`) completes against this backend. Emulating
   `ListQosServersForTitle` is therefore not required.
2. **Server registration / port** — the shipped client build has no heartbeat caller
   (`SovietAPI.SendServerHeartbeat` is unused), but the plugin adds one: any host that is
   serving Bolt — including the headless gameserver, where the plugin is loaded too — POSTs
   `POST /server/heartbeat` every 5 s. The backend prunes entries idle for 20 s. A fixed
   `SJG_STATIC_SERVERS` listing is still available as a fallback.
3. **A player-bearing game server** — run the retail game headless (see
   [`../gameserver/README.md`](../gameserver/README.md)); it accepts the client's
   `AuthProtocolToken` and Bolt spawns the joining player. Empty slots are backfilled with bots
   (`BotCount − (humans − 1)`) so a lone player is never left waiting.
