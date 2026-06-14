import os
import shutil
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.config import settings
from app.api.deps import require_admin
from app.services.config_service import config_service
from app.models.user import User

router = APIRouter(prefix="/server/files", tags=["files"])

class FileWritePayload(BaseModel):
    path: str = Field(..., description="File path relative to server directory")
    content: str = Field(..., description="Text content to write")

# Allowed extensions for viewing and editing
TEXT_EXTENSIONS = (
    ".properties", ".yml", ".yaml", ".json", ".txt", ".conf", 
    ".log", ".sh", ".py", ".xml", ".jsonld"
)

@router.get("/list")
async def list_files(
    path: str = Query("", description="Relative folder path"),
    current_user: User = Depends(require_admin)
):
    try:
        # Resolve target directory path safely
        target_dir = config_service.safe_resolve_path(path)
        
        if not os.path.exists(target_dir):
            raise HTTPException(status_code=404, detail="Directory not found")
        if not os.path.isdir(target_dir):
            raise HTTPException(status_code=400, detail="Path is not a directory")

        results = []
        for entry in os.scandir(target_dir):
            stat = entry.stat()
            # Determine if we can edit this file type
            is_editable = entry.name.endswith(TEXT_EXTENSIONS) if entry.is_file() else False
            
            results.append({
                "name": entry.name,
                "isDir": entry.is_dir(),
                "sizeBytes": stat.st_size if entry.is_file() else 0,
                "lastModified": stat.st_mtime,
                "isEditable": is_editable
            })
            
        # Sort directories first, then alphabetically
        results.sort(key=lambda x: (not x["isDir"], x["name"].lower()))
        return results
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list directory contents: {str(e)}"
        )

@router.get("/read")
async def read_file_content(
    path: str = Query(..., description="Relative file path"),
    current_user: User = Depends(require_admin)
):
    try:
        target_file = config_service.safe_resolve_path(path)
        
        if not os.path.exists(target_file):
            raise HTTPException(status_code=404, detail="File not found")
        if os.path.isdir(target_file):
            raise HTTPException(status_code=400, detail="Path is a directory, not a file")
            
        # Ensure it's a readable text extension or file type
        if not path.endswith(TEXT_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only text files and configuration files are viewable."
            )

        # Check file size (limit to 5MB to avoid memory issues)
        if os.path.getsize(target_file) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is too large to display (limit 5MB)."
            )

        with open(target_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"content": content}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )

@router.post("/write")
async def write_file_content(
    payload: FileWritePayload,
    current_user: User = Depends(require_admin)
):
    try:
        target_file = config_service.safe_resolve_path(payload.path)
        
        # Protect paper.jar from being overwritten
        if payload.path.strip().endswith(settings.MINECRAFT_JAR_NAME):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Modifying the main server JAR file is forbidden."
            )

        # Ensure it's a text extension
        if not payload.path.endswith(TEXT_EXTENSIONS):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Writing to non-text or binary files is forbidden."
            )

        os.makedirs(os.path.dirname(target_file), exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(payload.content)
            
        return {"status": "success", "detail": "File saved successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file: {str(e)}"
        )

@router.delete("/delete")
async def delete_file_or_dir(
    path: str = Query(..., description="Relative path to delete"),
    current_user: User = Depends(require_admin)
):
    try:
        target_path = config_service.safe_resolve_path(path)
        
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail="File or directory not found")

        # Protect paper.jar
        if path.strip().endswith(settings.MINECRAFT_JAR_NAME):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Deleting the main server JAR file is forbidden."
            )

        if os.path.isdir(target_path):
            # Safe check: do not delete the parent server directory itself!
            if target_path == os.path.abspath(settings.MINECRAFT_SERVER_DIR):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Deleting the main server directory is forbidden."
                )
            shutil.rmtree(target_path)
        else:
            os.remove(target_path)

        return {"status": "success", "detail": f"Successfully deleted {path}"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resource: {str(e)}"
        )
