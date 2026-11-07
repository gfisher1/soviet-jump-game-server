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
async def heartbeat(inst: ServerInstance) -> Dict[str, bool]:
    _servers[inst.SessionId or str(uuid.uuid4())] = inst
    return {"ok": True}


@app.get("/player/ingame/{playfab_id}")
async def player_ingame(playfab_id: str) -> bool:
    _ = playfab_id
    return False
