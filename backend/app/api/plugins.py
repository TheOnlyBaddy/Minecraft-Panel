import os
import re
import zipfile
import shutil
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.api.deps import require_admin
from app.services.config_service import config_service
from app.services.audit_service import audit_service
from app.models.user import User

router = APIRouter(prefix="/server/plugins", tags=["plugins"])



def parse_plugin_yml(content: str) -> Dict[str, Any]:
    """Simple parser for YAML formatted plugin.yml files in plugins."""
    info = {}
    for line in content.splitlines():
        # Remove comments
        line = line.split('#')[0].strip()
        if not line:
            continue
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            # Clean string quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            
            # Extract basic keys
            if key == "authors" or key == "author":
                if val.startswith('[') and val.endswith(']'):
                    val = [x.strip() for x in val[1:-1].split(',')]
                else:
                    val = [val] if val else []
                info["authors"] = val
            else:
                info[key] = val
    return info

def get_plugin_metadata(jar_path: str) -> Dict[str, Any]:
    """Retrieve metadata by parsing plugin.yml inside the jar file."""
    default_meta = {
        "name": os.path.splitext(os.path.basename(jar_path))[0],
        "version": "Unknown",
        "description": "No description provided.",
        "authors": [],
        "website": ""
    }
    try:
        if not zipfile.is_zipfile(jar_path):
            return default_meta
        with zipfile.ZipFile(jar_path, 'r') as jar:
            if "plugin.yml" in jar.namelist():
                content = jar.read("plugin.yml").decode("utf-8", errors="ignore")
                meta = parse_plugin_yml(content)
                if "name" in meta:
                    default_meta["name"] = meta["name"]
                if "version" in meta:
                    default_meta["version"] = meta["version"]
                if "description" in meta:
                    default_meta["description"] = meta["description"]
                if "authors" in meta:
                    default_meta["authors"] = meta["authors"]
                elif "author" in meta:
                    default_meta["authors"] = [meta["author"]]
                if "website" in meta:
                    default_meta["website"] = meta["website"]
    except Exception:
        pass
    return default_meta

@router.get("")
async def list_plugins(current_user: User = Depends(require_admin)):
    try:
        plugins_dir = os.path.join(settings.MINECRAFT_SERVER_DIR, "plugins")
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
            
        results = []
        for entry in os.scandir(plugins_dir):
            if entry.is_file() and entry.name.endswith(".jar"):
                meta = get_plugin_metadata(entry.path)
                results.append({
                    "file_name": entry.name,
                    "name": meta["name"],
                    "version": meta["version"],
                    "description": meta["description"],
                    "authors": meta["authors"],
                    "website": meta["website"],
                    "size_bytes": entry.stat().st_size
                })
        results.sort(key=lambda x: x["name"].lower())
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list plugins: {str(e)}"
        )



@router.delete("")
async def uninstall_plugin(
    request: Request,
    file_name: str = Query(..., description="Plugin jar filename to delete"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        if not file_name.endswith(".jar"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .jar files can be uninstalled."
            )
        
        target_path = config_service.safe_resolve_path(os.path.join("plugins", file_name))
        
        if not os.path.exists(target_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin file {file_name} not found."
            )
            
        os.remove(target_path)
        
        plugin_name_slug = os.path.splitext(file_name)[0]
        plugins_dir = os.path.dirname(target_path)
        
        folders_to_check = [plugin_name_slug]
        for sep in ['-', '_']:
            if sep in plugin_name_slug:
                prefix = plugin_name_slug.split(sep)[0]
                if prefix and len(prefix) > 2:
                    folders_to_check.append(prefix)
                    
        deleted_folders = []
        for folder in folders_to_check:
            resolved_folder_path = config_service.safe_resolve_path(os.path.join("plugins", folder))
            if os.path.exists(resolved_folder_path) and os.path.isdir(resolved_folder_path):
                shutil.rmtree(resolved_folder_path)
                deleted_folders.append(folder)
                break
                
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="UNINSTALL_PLUGIN",
            target=f"plugin:{file_name}",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"file_name": file_name, "deleted_folders": deleted_folders}
        )
        return {
            "status": "success",
            "detail": f"Plugin {file_name} and its configuration uninstalled successfully"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plugin deletion failed: {str(e)}"
        )

@router.post("/upload")
async def upload_plugin_file(
    request: Request,
    file: UploadFile = File(..., description="The plugin .jar file to upload"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        if not file.filename.endswith(".jar"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .jar files can be uploaded as plugins."
            )
        
        filename = os.path.basename(file.filename)
        if not re.match(r'^[a-zA-Z0-9_\-\.\s]+$', filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Use only alphanumeric characters, spaces, dots, dashes, and underscores."
            )
            
        target_path = config_service.safe_resolve_path(os.path.join("plugins", filename))
        
        plugins_dir = os.path.dirname(target_path)
        os.makedirs(plugins_dir, exist_ok=True)
        
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        plugin_name_slug = os.path.splitext(filename)[0]
        await audit_service.log(
            db=db,
            user_id=current_user.id,
            action="UPLOAD_PLUGIN",
            target=f"plugin:{plugin_name_slug}",
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={"filename": filename}
        )
        
        return {"status": "success", "detail": f"Plugin {filename} uploaded successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plugin upload failed: {str(e)}"
        )
