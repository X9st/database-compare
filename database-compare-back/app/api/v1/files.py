"""文件下载API"""
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

EXPORT_DIR = Path("data/exports").resolve()


@router.get("/download/{filename}")
async def download_file(filename: str):
    """下载导出文件"""
    safe_name = Path(filename).name
    if safe_name != filename:
        raise HTTPException(status_code=400, detail="非法文件名")

    file_path = (EXPORT_DIR / safe_name).resolve()
    if EXPORT_DIR not in file_path.parents:
        raise HTTPException(status_code=403, detail="非法访问路径")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(file_path),
        filename=safe_name,
        media_type="application/octet-stream"
    )
