"""前端工具函数：API 调用封装。"""

import httpx

API_BASE = "http://localhost:8000/api"


def api_get(path: str):
    resp = httpx.get(f"{API_BASE}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, json_data: dict | None = None, files: dict | None = None):
    resp = httpx.post(f"{API_BASE}{path}", json=json_data, files=files, timeout=120)
    resp.raise_for_status()
    return resp.json()


def api_patch(path: str, json_data: dict):
    resp = httpx.patch(f"{API_BASE}{path}", json=json_data, timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_delete(path: str):
    resp = httpx.delete(f"{API_BASE}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()
