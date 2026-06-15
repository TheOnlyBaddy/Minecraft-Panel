import os
import re
import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Literal
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.config import settings
from app.api.deps import require_admin
from app.models.user import User

router = APIRouter(prefix="/server/players", tags=["players"])

class PlayerAddPayload(BaseModel):
    list_type: Literal["whitelist", "ops", "banned-players", "banned-ips"] = Field(..., description="Target list")
    username_or_ip: str = Field(..., description="Username or IP address to add")
    reason: str | None = Field("Banned by administrator", description="Reason (only for bans)")

class PlayerRemovePayload(BaseModel):
    list_type: Literal["whitelist", "ops", "banned-players", "banned-ips"] = Field(..., description="Target list")
    username_or_ip: str = Field(..., description="Username or IP address to remove")

def get_offline_uuid(username: str) -> str:
    hash_bytes = hashlib.md5(f"OfflinePlayer:{username}".encode('utf-8')).digest()
    hash_list = list(hash_bytes)
    hash_list[6] = (hash_list[6] & 0x0f) | 0x30  # Set version to 3
    hash_list[8] = (hash_list[8] & 0x3f) | 0x80  # Set variant to IETF
    return str(uuid.UUID(bytes=bytes(hash_list)))

async def resolve_uuid(username: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=2.0)
            if resp.status_code == 200:
                data = resp.json()
                raw_id = data["id"]
                return f"{raw_id[:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
    except Exception:
        pass
    return get_offline_uuid(username)

def get_file_path(list_type: str) -> str:
    mapping = {
        "whitelist": "whitelist.json",
        "ops": "ops.json",
        "banned-players": "banned-players.json",
        "banned-ips": "banned-ips.json"
    }
    return os.path.join(settings.MINECRAFT_SERVER_DIR, mapping[list_type])

def read_json_file(filepath: str) -> list:
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def write_json_file(filepath: str, data: list) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

MAPPING = {
    "whitelist": "whitelist.json",
    "ops": "ops.json",
    "banned-players": "banned-players.json",
    "banned-ips": "banned-ips.json"
}

async def read_player_list(list_type: str) -> list:
    if settings.is_remote_mode:
        from app.services.agent_coordinator import agent_coordinator
        filename = MAPPING[list_type]
        res = await agent_coordinator.send_request("read_file", {"path": filename})
        if res.get("status") == "success":
            try:
                return json.loads(res.get("content", "[]"))
            except Exception:
                return []
        return []
    
    filepath = get_file_path(list_type)
    return read_json_file(filepath)

async def write_player_list(list_type: str, data: list) -> None:
    if settings.is_remote_mode:
        from app.services.agent_coordinator import agent_coordinator
        filename = MAPPING[list_type]
        content = json.dumps(data, indent=2)
        res = await agent_coordinator.send_request("write_file", {"path": filename, "content": content})
        if res.get("status") == "error":
            raise HTTPException(status_code=400, detail=res.get("detail"))
        return
        
    filepath = get_file_path(list_type)
    write_json_file(filepath, data)

@router.get("/online")
async def get_online_players(
    current_user: User = Depends(require_admin)
):
    if settings.is_remote_mode:
        from app.services.metrics_service import metrics_service
        latest = metrics_service.latest_agent_metrics
        raw_players = latest.get("active_players_list", []) if latest else []
    else:
        from app.services.process_manager import process_manager
        raw_players = list(getattr(process_manager, "active_players_set", set()))
        
    # Return online players with offline UUIDs for frontend consistency, stripping any ANSI escape sequences
    clean_players = [re.sub(r'\x1B\s*(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', p) for p in raw_players]
    return [{"name": p, "uuid": get_offline_uuid(p)} for p in clean_players if p]

@router.get("")
async def get_player_list(
    list_type: Literal["whitelist", "ops", "banned-players", "banned-ips"],
    current_user: User = Depends(require_admin)
):
    return await read_player_list(list_type)

@router.post("/add")
async def add_player_to_list(
    payload: PlayerAddPayload,
    current_user: User = Depends(require_admin)
):
    data = await read_player_list(payload.list_type)
    val = payload.username_or_ip.strip()

    if not val:
        raise HTTPException(status_code=400, detail="Name or IP cannot be empty")

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if payload.list_type == "banned-ips":
        # Check if already present
        if any(item.get("ip") == val for item in data):
            return {"status": "success", "detail": f"IP {val} is already banned"}
        data.append({
            "ip": val,
            "created": timestamp,
            "source": current_user.username,
            "expires": "forever",
            "reason": payload.reason
        })
    else:
        # Resolve UUID for the player
        player_uuid = await resolve_uuid(val)
        
        # Check if already present
        if any(item.get("uuid") == player_uuid for item in data):
            return {"status": "success", "detail": f"Player {val} is already in the list"}

        if payload.list_type == "whitelist":
            data.append({
                "uuid": player_uuid,
                "name": val
            })
        elif payload.list_type == "ops":
            data.append({
                "uuid": player_uuid,
                "name": val,
                "level": 4,
                "bypassesPlayerLimit": False
            })
        elif payload.list_type == "banned-players":
            data.append({
                "uuid": player_uuid,
                "name": val,
                "created": timestamp,
                "source": current_user.username,
                "expires": "forever",
                "reason": payload.reason
            })

    await write_player_list(payload.list_type, data)
    return {"status": "success", "detail": f"Added {val} to {payload.list_type}"}

@router.post("/remove")
async def remove_player_from_list(
    payload: PlayerRemovePayload,
    current_user: User = Depends(require_admin)
):
    data = await read_player_list(payload.list_type)
    val = payload.username_or_ip.strip()

    if not val:
        raise HTTPException(status_code=400, detail="Name or IP cannot be empty")

    original_len = len(data)
    if payload.list_type == "banned-ips":
        data = [item for item in data if item.get("ip") != val]
    else:
        # We check both name and uuid (case insensitive for name)
        data = [item for item in data if item.get("name", "").lower() != val.lower() and item.get("uuid") != val]

    if len(data) == original_len:
        raise HTTPException(status_code=404, detail=f"Entry {val} not found in {payload.list_type}")

    await write_player_list(payload.list_type, data)
    return {"status": "success", "detail": f"Removed {val} from {payload.list_type}"}
