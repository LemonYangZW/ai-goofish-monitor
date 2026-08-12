"""
登录状态管理路由
"""
import os
import json
import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.services.account_state_service import (
    default_account_state_path,
    ensure_account_state_dir,
    to_filesystem_path,
)


router = APIRouter(prefix="/api/login-state", tags=["login-state"])


class LoginStateUpdate(BaseModel):
    """登录状态更新模型"""
    content: str


@router.post("", response_model=dict)
async def update_login_state(
    data: LoginStateUpdate,
):
    """接收前端发送的登录状态JSON字符串，并保存为账号管理的默认账号。"""
    state_file = default_account_state_path()
    fs_state_file = to_filesystem_path(state_file)

    try:
        # 验证是否是有效的JSON
        json.loads(data.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式。")

    try:
        ensure_account_state_dir()
        async with aiofiles.open(fs_state_file, 'w', encoding='utf-8') as f:
            await f.write(data.content)
        return {
            "message": f"登录状态已保存到账号管理默认账号 '{state_file}'。",
            "path": state_file,
            "account": "default",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入登录状态文件时出错: {e}")


@router.delete("", response_model=dict)
async def delete_login_state():
    """删除账号管理中的默认登录状态文件。"""
    state_file = default_account_state_path()
    fs_state_file = to_filesystem_path(state_file)

    if os.path.exists(fs_state_file):
        try:
            os.remove(fs_state_file)
            return {"message": "默认账号登录状态已成功删除。", "path": state_file}
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"删除登录状态文件时出错: {e}")

    return {"message": "登录状态文件不存在，无需删除。"}
