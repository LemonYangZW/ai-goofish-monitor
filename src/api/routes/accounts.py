"""
闲鱼账号管理路由
"""
import json
import os
import re
import aiofiles
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from src.services.account_state_service import (
    account_state_dir,
    account_state_path,
    ensure_account_state_dir,
    normalize_state_path,
    to_filesystem_path,
)


router = APIRouter(prefix="/api/accounts", tags=["accounts"])

ACCOUNT_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,50}$")


class AccountCreate(BaseModel):
    name: str
    content: str


class AccountUpdate(BaseModel):
    content: str


def _state_dir() -> str:
    return account_state_dir()


def _ensure_state_dir(path: str) -> None:
    os.makedirs(to_filesystem_path(path), exist_ok=True)


def _validate_name(name: str) -> str:
    trimmed = name.strip()
    if not trimmed or not ACCOUNT_NAME_RE.match(trimmed):
        raise HTTPException(status_code=400, detail="账号名称只能包含字母、数字、下划线或短横线。")
    return trimmed


def _account_path(name: str) -> str:
    return account_state_path(name)


def _account_fs_path(name: str) -> str:
    return to_filesystem_path(_account_path(name))


def _validate_json(content: str) -> None:
    try:
        json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式。")


@router.get("", response_model=List[dict])
async def list_accounts():
    state_dir = _state_dir()
    fs_state_dir = to_filesystem_path(state_dir)
    if not os.path.isdir(fs_state_dir):
        return []
    files = [f for f in os.listdir(fs_state_dir) if f.endswith(".json")]
    accounts = []
    for filename in sorted(files):
        name = filename[:-5]
        accounts.append({
            "name": name,
            "path": normalize_state_path(f"{state_dir}/{filename}"),
        })
    return accounts


@router.get("/{name}", response_model=dict)
async def get_account(name: str):
    account_name = _validate_name(name)
    path = _account_path(account_name)
    fs_path = to_filesystem_path(path)
    if not os.path.exists(fs_path):
        raise HTTPException(status_code=404, detail="账号不存在")
    async with aiofiles.open(fs_path, "r", encoding="utf-8") as f:
        content = await f.read()
    return {"name": account_name, "path": path, "content": content}


@router.post("", response_model=dict)
async def create_account(data: AccountCreate):
    account_name = _validate_name(data.name)
    _validate_json(data.content)
    state_dir = _state_dir()
    _ensure_state_dir(state_dir)
    path = _account_path(account_name)
    fs_path = _account_fs_path(account_name)
    if os.path.exists(fs_path):
        raise HTTPException(status_code=409, detail="账号已存在")
    async with aiofiles.open(fs_path, "w", encoding="utf-8") as f:
        await f.write(data.content)
    return {"message": "账号已添加", "name": account_name, "path": path}


@router.put("/{name}", response_model=dict)
async def update_account(name: str, data: AccountUpdate):
    account_name = _validate_name(name)
    _validate_json(data.content)
    ensure_account_state_dir()
    path = _account_path(account_name)
    fs_path = _account_fs_path(account_name)
    if not os.path.exists(fs_path):
        raise HTTPException(status_code=404, detail="账号不存在")
    async with aiofiles.open(fs_path, "w", encoding="utf-8") as f:
        await f.write(data.content)
    return {"message": "账号已更新", "name": account_name, "path": path}


@router.delete("/{name}", response_model=dict)
async def delete_account(name: str):
    account_name = _validate_name(name)
    path = _account_path(account_name)
    fs_path = to_filesystem_path(path)
    if not os.path.exists(fs_path):
        raise HTTPException(status_code=404, detail="账号不存在")
    os.remove(fs_path)
    return {"message": "账号已删除"}
