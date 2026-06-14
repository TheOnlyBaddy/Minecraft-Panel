import os
import json
import asyncio
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import settings
from app.models.setting import Setting

CONFIG_VALIDATION_RULES = {
    # Booleans
    "allow-flight": bool,
    "allow-nether": bool,
    "enable-command-block": bool,
    "enable-query": bool,
    "enable-rcon": bool,
    "force-gamemode": bool,
    "generate-structures": bool,
    "hardcore": bool,
    "online-mode": bool,
    "prevent-proxy-connections": bool,
    "pvp": bool,
    "require-resource-pack": bool,
    "snooper-enabled": bool,
    "spawn-animals": bool,
    "spawn-monsters": bool,
    "spawn-npcs": bool,
    "use-native-transport": bool,
    "white-list": bool,
    # Strings with options
    "gamemode": str,
    "difficulty": str,
    # Integers
    "max-build-height": int,
    "max-players": int,
    "max-world-size": int,
    "network-compression-threshold": int,
    "op-permission-level": int,
    "player-idle-timeout": int,
    "server-port": int,
    "spawn-protection": int,
    "view-distance": int,
}

class ConfigService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ConfigService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def safe_resolve_path(self, filename: str) -> str:
        server_dir = os.path.abspath(settings.MINECRAFT_SERVER_DIR)
        target_path = os.path.abspath(os.path.join(server_dir, filename))
        if not target_path.startswith(server_dir):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Path traversal attempt detected."
            )
        return target_path

    def parse_properties(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {}
        
        config = {}
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if '=' in stripped:
                    key, val = stripped.split('=', 1)
                    key = key.strip()
                    val = val.strip()

                    # Convert types
                    if val.lower() == 'true':
                        config[key] = True
                    elif val.lower() == 'false':
                        config[key] = False
                    else:
                        try:
                            config[key] = int(val)
                        except ValueError:
                            config[key] = val
        return config

    def validate_properties(self, config: dict) -> dict:
        validated = {}
        for key, val in config.items():
            # Check validation rules
            if key in CONFIG_VALIDATION_RULES:
                rule_type = CONFIG_VALIDATION_RULES[key]
                
                # Validation for booleans
                if rule_type is bool:
                    if isinstance(val, bool):
                        validated[key] = val
                    elif str(val).lower() in ('true', 'false'):
                        validated[key] = str(val).lower() == 'true'
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field '{key}' must be a boolean."
                        )
                
                # Validation for integers
                elif rule_type is int:
                    try:
                        int_val = int(val)
                        validated[key] = int_val
                    except (ValueError, TypeError):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field '{key}' must be an integer."
                        )
                    
                    # Specific constraints
                    if key == "max-players" and (int_val < 1 or int_val > 1000):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="max-players must be between 1 and 1000."
                        )
                    if key == "server-port" and (int_val < 1 or int_val > 65535):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="server-port must be between 1 and 65535."
                        )
                    if key == "view-distance" and (int_val < 2 or int_val > 32):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="view-distance must be between 2 and 32."
                        )
                    if int_val < 0 and key not in ("server-port", "max-players", "view-distance"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Field '{key}' must be non-negative."
                        )
                elif rule_type is str:
                    str_val = str(val).strip().lower()
                    if key == "gamemode" and str_val not in ("survival", "creative", "adventure", "spectator"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="gamemode must be one of: survival, creative, adventure, spectator."
                        )
                    if key == "difficulty" and str_val not in ("peaceful", "easy", "normal", "hard"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="difficulty must be one of: peaceful, easy, normal, hard."
                        )
                    validated[key] = str_val
            else:
                # String properties (no strict type validation, just cast to string)
                validated[key] = str(val)

        return validated

    async def get_config(self) -> dict:
        filepath = self.safe_resolve_path("server.properties")
        # Parse from disk in a separate thread
        return await asyncio.to_thread(self.parse_properties, filepath)

    async def save_config(self, db: AsyncSession, config: dict, user_id: int | None = None) -> dict:
        # 1. Validate the submitted updates
        validated_updates = self.validate_properties(config)

        # 2. Get absolute target path
        filepath = self.safe_resolve_path("server.properties")
        tmp_filepath = filepath + ".tmp"

        # 3. Read current configurations and merge
        current_config = await self.get_config()
        merged_config = {**current_config, **validated_updates}

        # 4. Generate text lines and write to .tmp file atomically in separate thread
        def write_tmp_properties(tmp_path: str, merged: dict):
            with open(tmp_path, 'w', encoding='utf-8') as f:
                f.write("# Minecraft server properties\n")
                f.write("# Generated by Antigravity Panel\n")
                for k, v in sorted(merged.items()):
                    # Format booleans as lowercase strings true/false
                    if isinstance(v, bool):
                        f.write(f"{k}={str(v).lower()}\n")
                    else:
                        f.write(f"{k}={v}\n")

        await asyncio.to_thread(write_tmp_properties, tmp_filepath, merged_config)
        
        # 5. Swap files (Atomic replace with direct write fallback for Windows/OneDrive locks)
        try:
            await asyncio.to_thread(os.replace, tmp_filepath, filepath)
        except (PermissionError, OSError) as e:
            # Fallback to direct write if rename is locked (e.g., by OneDrive syncing the temp file)
            def write_direct(path: str, merged: dict):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("# Minecraft server properties\n")
                    f.write("# Generated by Antigravity Panel\n")
                    for k, v in sorted(merged.items()):
                        if isinstance(v, bool):
                            f.write(f"{k}={str(v).lower()}\n")
                        else:
                            f.write(f"{k}={v}\n")
            await asyncio.to_thread(write_direct, filepath, merged_config)
            # Clean up the temp file if it remains
            try:
                if os.path.exists(tmp_filepath):
                    os.remove(tmp_filepath)
            except Exception:
                pass

        # 6. Cache state in database settings table
        # Check if setting already exists
        result = await db.execute(select(Setting).where(Setting.key == "server.properties"))
        setting_record = result.scalars().first()

        if setting_record:
            setting_record.value_json = json.dumps(merged_config)
            setting_record.updated_by = user_id
        else:
            setting_record = Setting(
                key="server.properties",
                value_json=json.dumps(merged_config),
                updated_by=user_id
            )
            db.add(setting_record)

        await db.commit()
        await db.refresh(setting_record)

        return merged_config

config_service = ConfigService()
