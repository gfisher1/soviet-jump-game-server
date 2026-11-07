"""
Soviet Jump Game - self-hosted backend.

Replaces the dead services the client talks to:

  * PlayFab                (login / title data / inventory / stats)   [stubbed client-side]
  * api.fantasticpassion.games   (matchmaking + server registry)      [this service]

This service implements the custom backend ("SovietAPI") contract that the client
uses.  See docs/PROTOCOL.md for the full reverse-engineered contract.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import time as _time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
PUBLIC_HOST = os.environ.get("SJG_PUBLIC_HOST", "127.0.0.1")
GAME_PORT = int(os.environ.get("SJG_GAME_PORT", "42010"))
JWT_SECRET = os.environ.get("SJG_JWT_SECRET", "sjg-local-secret")
DEFAULT_ACCOUNT_GROUP = os.environ.get("SJG_ACCOUNT_GROUP", "Administrator")

app = FastAPI(title="Soviet Jump Game - local backend", version="0.1.0")

# In-memory registry of game servers (populated via /server/heartbeat).
_servers: Dict[str, "ServerInstance"] = {}
_server_seen: Dict[str, float] = {}
SERVER_STALE_SECONDS = 20.0


def _static_servers() -> List["ServerInstance"]:
    """Servers always present in the browser, from SJG_STATIC_SERVERS.

    Format: 'host:port:Name, host2:port2, ...' (name optional).
    """
    raw = os.environ.get("SJG_STATIC_SERVERS", "").strip()
    out: List[ServerInstance] = []
    if not raw:
        return out
    for i, entry in enumerate(raw.replace(";", ",").split(",")):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(":")
        if len(parts) < 2:
            continue
        host = parts[0].strip()
        try:
            port = int(parts[1])
        except ValueError:
            continue
        name = parts[2].strip() if len(parts) > 2 else ("SJG Server " + str(i + 1))
        out.append(ServerInstance(
            SessionId="static-" + str(i),
            Address=host,
            Port=port,
            Region="USSR",
            State="AcceptingPlayers",
            Metadata={"Name": name, "MaxPlayers": 48, "Static": True},
        ))
    return out


class ServerListing(BaseModel):
    id: str
    name: str
    ip: str
    port: int
    players: int
    maxPlayers: int
    map: str = ""
    region: str = "USSR"
    private: bool = False
    password: bool = False


# --------------------------------------------------------------------------------------
# Models (mirror the client's C# DTOs)
# --------------------------------------------------------------------------------------
class ServerInstance(BaseModel):
    SessionId: str = ""
    Address: str = PUBLIC_HOST
    Port: int = GAME_PORT
    Players: List[str] = []
    Private: bool = False
    Code: Optional[str] = None
    Region: str = "USSR"
    State: str = "AcceptingPlayers"
    Production: bool = False
    Metadata: Dict[str, Any] = {}


class MinimalServerInstance(BaseModel):
    Success: bool = True
    ServerId: str = ""
    IP: str = PUBLIC_HOST
    Port: int = GAME_PORT
    PlayerCount: int = 0
    Hostname: Optional[str] = None
    ConnectToken: str = ""


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def make_jwt(playfab_id: str, group: str) -> str:
    """The client decodes this without verifying (no secret is shipped), it only reads
    the payload as an ApiUser. Still, produce a real HS256 JWT."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {
        "PlayFabId": playfab_id,
        "MasterAccountId": playfab_id,
        "SteamId": 0,
        "AccountType": group,
        "iat": now,
        "exp": now + 86400 * 365,
    }
    signing_input = _b64url(json.dumps(header, separators=(",", ":")).encode()) + "." + \
        _b64url(json.dumps(payload, separators=(",", ":")).encode())
    sig = hmac.new(JWT_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64url(sig)


def _minimal(inst: ServerInstance) -> MinimalServerInstance:
    return MinimalServerInstance(
        Success=True,
        ServerId=(inst.SessionId or str(uuid.uuid4()))[:6],
        IP=inst.Address or PUBLIC_HOST,
        Port=inst.Port,
        PlayerCount=len(inst.Players),
        Hostname=inst.Metadata.get("Environment", {}).get("fullyQualifiedDomainName")
        if isinstance(inst.Metadata.get("Environment"), dict) else None,
        ConnectToken=str(uuid.uuid4()),
    )


def configured_server() -> ServerInstance:
    """The statically-configured game server (see SJG_PUBLIC_HOST / SJG_GAME_PORT)."""
    for inst in _servers.values():
        if inst.State in ("AcceptingPlayers", "ConfiguringGame", "MatchRunning"):
            return inst
    return ServerInstance(
        SessionId="localdev",
        Address=PUBLIC_HOST,
        Port=GAME_PORT,
        State="AcceptingPlayers",
        Metadata={"Environment": {"fullyQualifiedDomainName": PUBLIC_HOST}},
    )


# --------------------------------------------------------------------------------------
# Endpoints (paths match the client's BASE_API_URL-relative calls)
# --------------------------------------------------------------------------------------
@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"


@app.post("/authenticate")
async def authenticate(request: Request) -> JSONResponse:
    """Body is the PlayFab session ticket (text). Response: {"token", "group"}."""
    _ = await request.body()
    playfab_id = "0FF1CE0000000001"
    return JSONResponse({"token": make_jwt(playfab_id, DEFAULT_ACCOUNT_GROUP),
                         "group": DEFAULT_ACCOUNT_GROUP})


@app.get("/server/regions")
async def regions() -> List[str]:
    # Values are ServerRegion enum names from the game.
    return ["USSR", "Development"]


@app.post("/server/private/create")
async def private_create(request: Request) -> MinimalServerInstance:
    code = (await request.body()).decode("utf-8", "ignore").strip() or str(uuid.uuid4())[:6]
    inst = configured_server()
    inst.Code = code
    inst.Private = True
    _servers[inst.SessionId] = inst
    return _minimal(inst)


@app.get("/server/private/connect/{code}")
async def private_connect(code: str) -> MinimalServerInstance:
    for inst in _servers.values():
        if (inst.Code or "").lower() == code.lower():
            return _minimal(inst)
    return _minimal(configured_server())


@app.get("/server/public/{region}")
async def public_match(region: str, auto: int = 0) -> MinimalServerInstance:
    _ = (region, auto)
    return _minimal(configured_server())


@app.post("/server/heartbeat")
async def heartbeat(inst: ServerInstance, request: Request) -> Dict[str, bool]:
    sid = inst.SessionId or str(uuid.uuid4())
    if not inst.Address or inst.Address in ("0.0.0.0", "::"):
        # Trust the source address of the heartbeat so hosts don't have to know their own IP.
        client = request.client
        if client is not None:
            inst.Address = client.host
    _servers[sid] = inst
    _server_seen[sid] = _time.time()
    return {"ok": True}


@app.get("/servers")
async def list_servers() -> List[ServerListing]:
    """Server browser: the list of currently-registered + configured game servers."""
    now = _time.time()
    out: List[ServerListing] = []

    def add(inst: ServerInstance) -> None:
        md = inst.Metadata or {}
        out.append(ServerListing(
            id=(inst.SessionId or "")[:8],
            name=str(md.get("Name") or md.get("RoomID") or ("SJG-" + (inst.SessionId or "")[:6])),
            ip=inst.Address,
            port=inst.Port,
            players=len(inst.Players or []),
            maxPlayers=int(md.get("MaxPlayers", 50) or 50),
            map=str(md.get("Map", "")),
            region=inst.Region,
            private=bool(inst.Private),
        ))

    for inst in _static_servers():
        add(inst)

    for sid, inst in list(_servers.items()):
        if now - _server_seen.get(sid, 0) > SERVER_STALE_SECONDS:
            _servers.pop(sid, None)
            _server_seen.pop(sid, None)
            continue
        add(inst)

    out.sort(key=lambda s: (s.private, -s.players))
    return out


@app.get("/player/ingame/{playfab_id}")
async def player_ingame(playfab_id: str) -> bool:
    _ = playfab_id
    return False
