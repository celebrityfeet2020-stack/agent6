"""
元提示词管理API (Meta Prompt Management API)
控制面板的核心功能 - 管理Agent的元提示词
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

router = APIRouter()

# 元提示词存储路径
META_PROMPTS_DIR = Path("/app/data/meta_prompts")
META_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
ACTIVE_PROMPT_FILE = META_PROMPTS_DIR / "active.json"


class MetaPrompt(BaseModel):
    """元提示词模型"""
    id: str = Field(..., description="唯一ID")
    name: str = Field(..., description="名称")
    content: str = Field(..., description="提示词内容")
    version: str = Field(default="1.0.0", description="版本号")
    is_active: bool = Field(default=False, description="是否激活")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    tags: List[str] = Field(default=[], description="标签")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class CreateMetaPromptRequest(BaseModel):
    """创建元提示词请求"""
    name: str = Field(..., description="名称")
    content: str = Field(..., description="提示词内容")
    version: str = Field(default="1.0.0", description="版本号")
    tags: List[str] = Field(default=[], description="标签")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class UpdateMetaPromptRequest(BaseModel):
    """更新元提示词请求"""
    name: Optional[str] = Field(None, description="名称")
    content: Optional[str] = Field(None, description="提示词内容")
    version: Optional[str] = Field(None, description="版本号")
    tags: Optional[List[str]] = Field(None, description="标签")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")


def _load_meta_prompt(prompt_id: str) -> Optional[MetaPrompt]:
    """加载指定ID的元提示词"""
    file_path = META_PROMPTS_DIR / f"{prompt_id}.json"
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return MetaPrompt(**data)
    except Exception as e:
        print(f"Error loading meta prompt {prompt_id}: {e}")
        return None


def _save_meta_prompt(prompt: MetaPrompt):
    """保存元提示词"""
    file_path = META_PROMPTS_DIR / f"{prompt.id}.json"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt.dict(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save meta prompt: {str(e)}")


def _delete_meta_prompt_file(prompt_id: str):
    """删除元提示词文件"""
    file_path = META_PROMPTS_DIR / f"{prompt_id}.json"
    if file_path.exists():
        file_path.unlink()


def _list_all_meta_prompts() -> List[MetaPrompt]:
    """列出所有元提示词"""
    prompts = []
    for file_path in META_PROMPTS_DIR.glob("*.json"):
        if file_path.name == "active.json":
            continue
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            prompts.append(MetaPrompt(**data))
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    # 按更新时间倒序排序
    prompts.sort(key=lambda p: p.updated_at, reverse=True)
    return prompts


def _get_active_prompt_id() -> Optional[str]:
    """获取当前激活的元提示词ID"""
    if not ACTIVE_PROMPT_FILE.exists():
        return None
    
    try:
        with open(ACTIVE_PROMPT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("active_id")
    except Exception:
        return None


def _set_active_prompt_id(prompt_id: Optional[str]):
    """设置当前激活的元提示词ID"""
    try:
        with open(ACTIVE_PROMPT_FILE, 'w', encoding='utf-8') as f:
            json.dump({"active_id": prompt_id, "updated_at": datetime.now().isoformat()}, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set active prompt: {str(e)}")


@router.post("/api/meta-prompts", response_model=MetaPrompt)
async def create_meta_prompt(request: CreateMetaPromptRequest):
    """创建新的元提示词"""
    # 生成唯一ID
    prompt_id = f"mp_{int(datetime.now().timestamp() * 1000)}"
    
    # 创建元提示词对象
    prompt = MetaPrompt(
        id=prompt_id,
        name=request.name,
        content=request.content,
        version=request.version,
        tags=request.tags,
        metadata=request.metadata
    )
    
    # 保存到文件
    _save_meta_prompt(prompt)
    
    return prompt


@router.get("/api/meta-prompts", response_model=List[MetaPrompt])
async def list_meta_prompts():
    """列出所有元提示词"""
    prompts = _list_all_meta_prompts()
    
    # 标记当前激活的提示词
    active_id = _get_active_prompt_id()
    if active_id:
        for prompt in prompts:
            prompt.is_active = (prompt.id == active_id)
    
    return prompts


@router.get("/api/meta-prompts/{prompt_id}", response_model=MetaPrompt)
async def get_meta_prompt(prompt_id: str):
    """获取指定ID的元提示词"""
    prompt = _load_meta_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Meta prompt {prompt_id} not found")
    
    # 检查是否为激活状态
    active_id = _get_active_prompt_id()
    prompt.is_active = (prompt.id == active_id)
    
    return prompt


@router.get("/api/meta-prompts/active/current", response_model=Optional[MetaPrompt])
async def get_active_meta_prompt():
    """获取当前激活的元提示词"""
    active_id = _get_active_prompt_id()
    
    if not active_id:
        return None
    
    prompt = _load_meta_prompt(active_id)
    if prompt:
        prompt.is_active = True
    
    return prompt


@router.put("/api/meta-prompts/{prompt_id}", response_model=MetaPrompt)
async def update_meta_prompt(prompt_id: str, request: UpdateMetaPromptRequest):
    """更新元提示词"""
    prompt = _load_meta_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Meta prompt {prompt_id} not found")
    
    # 更新字段
    if request.name is not None:
        prompt.name = request.name
    if request.content is not None:
        prompt.content = request.content
    if request.version is not None:
        prompt.version = request.version
    if request.tags is not None:
        prompt.tags = request.tags
    if request.metadata is not None:
        prompt.metadata = request.metadata
    
    # 更新时间戳
    prompt.updated_at = datetime.now().isoformat()
    
    # 保存
    _save_meta_prompt(prompt)
    
    return prompt


@router.delete("/api/meta-prompts/{prompt_id}")
async def delete_meta_prompt(prompt_id: str):
    """删除元提示词"""
    prompt = _load_meta_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Meta prompt {prompt_id} not found")
    
    # 如果是激活的提示词，先取消激活
    active_id = _get_active_prompt_id()
    if active_id == prompt_id:
        _set_active_prompt_id(None)
    
    # 删除文件
    _delete_meta_prompt_file(prompt_id)
    
    return {"success": True, "message": f"Meta prompt {prompt_id} deleted"}


@router.post("/api/meta-prompts/{prompt_id}/activate")
async def activate_meta_prompt(prompt_id: str):
    """激活指定的元提示词"""
    prompt = _load_meta_prompt(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Meta prompt {prompt_id} not found")
    
    # 取消之前激活的提示词
    old_active_id = _get_active_prompt_id()
    
    # 设置新的激活提示词
    _set_active_prompt_id(prompt_id)
    
    return {
        "success": True,
        "message": f"Meta prompt {prompt_id} activated",
        "previous_active_id": old_active_id,
        "current_active_id": prompt_id
    }


@router.post("/api/meta-prompts/deactivate")
async def deactivate_meta_prompt():
    """取消激活当前的元提示词"""
    old_active_id = _get_active_prompt_id()
    
    if not old_active_id:
        return {"success": True, "message": "No active meta prompt to deactivate"}
    
    _set_active_prompt_id(None)
    
    return {
        "success": True,
        "message": "Meta prompt deactivated",
        "previous_active_id": old_active_id
    }


@router.get("/api/meta-prompts/stats/summary")
async def get_meta_prompts_stats():
    """获取元提示词统计信息"""
    prompts = _list_all_meta_prompts()
    active_id = _get_active_prompt_id()
    
    # 按标签分组统计
    tags_count: Dict[str, int] = {}
    for prompt in prompts:
        for tag in prompt.tags:
            tags_count[tag] = tags_count.get(tag, 0) + 1
    
    return {
        "total_count": len(prompts),
        "active_id": active_id,
        "has_active": active_id is not None,
        "tags_distribution": tags_count,
        "latest_updated": prompts[0].updated_at if prompts else None
    }
