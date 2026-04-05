import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib import parse, request

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import WechatIdentityPayload


@dataclass
class WechatSessionInfo:
    openid: str
    unionid: str | None = None


@dataclass
class WechatAccessTokenInfo:
    access_token: str
    expires_in: int


_access_token_cache: WechatAccessTokenInfo | None = None
_access_token_expires_at: datetime | None = None


def _ensure_wechat_credentials() -> None:
    if not settings.WECHAT_APP_ID or not settings.WECHAT_APP_SECRET:
        raise ValueError("WECHAT_APP_ID and WECHAT_APP_SECRET are required")


def _build_api_url(path: str, **params: str) -> str:
    query = parse.urlencode(params)
    return f"{settings.WECHAT_API_BASE_URL.rstrip('/')}{path}?{query}"


def _sync_request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url=url, method=method, data=data, headers=headers)
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


async def _request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    return await asyncio.to_thread(_sync_request_json, url, method, payload)


def resolve_wechat_identity(payload: WechatIdentityPayload) -> tuple[str, str | None]:
    # 兼容两种模式：
    # 1. 本地联调时由前端直接传 wechat_open_id；
    # 2. 生产接微信时由后端调用 code2Session 换取 openid。
    open_id = payload.wechat_open_id or f"mock-openid:{payload.code}"
    return open_id, payload.wechat_union_id


async def exchange_code_for_session(code: str) -> WechatSessionInfo:
    _ensure_wechat_credentials()
    url = _build_api_url(
        "/sns/jscode2session",
        appid=settings.WECHAT_APP_ID,
        secret=settings.WECHAT_APP_SECRET,
        js_code=code,
        grant_type="authorization_code",
    )
    body = await _request_json(url)
    if body.get("errcode"):
        raise ValueError(body.get("errmsg") or "Failed to exchange WeChat code")
    return WechatSessionInfo(
        openid=body["openid"],
        unionid=body.get("unionid"),
    )


async def resolve_wechat_identity_async(
    payload: WechatIdentityPayload,
) -> tuple[str, str | None]:
    if payload.wechat_open_id:
        return payload.wechat_open_id, payload.wechat_union_id
    if settings.WECHAT_LOGIN_USE_REAL_CODE2SESSION and payload.code:
        session_info = await exchange_code_for_session(payload.code)
        return session_info.openid, session_info.unionid
    return resolve_wechat_identity(payload)


async def get_wechat_access_token(force_refresh: bool = False) -> str:
    global _access_token_cache, _access_token_expires_at

    _ensure_wechat_credentials()
    now = datetime.now(timezone.utc)
    if (
        not force_refresh
        and _access_token_cache
        and _access_token_expires_at
        and _access_token_expires_at > now + timedelta(seconds=60)
    ):
        return _access_token_cache.access_token

    url = _build_api_url(
        "/cgi-bin/token",
        grant_type="client_credential",
        appid=settings.WECHAT_APP_ID,
        secret=settings.WECHAT_APP_SECRET,
    )
    body = await _request_json(url)
    if body.get("errcode"):
        raise ValueError(body.get("errmsg") or "Failed to fetch WeChat access token")

    _access_token_cache = WechatAccessTokenInfo(
        access_token=body["access_token"],
        expires_in=int(body.get("expires_in", 7200)),
    )
    _access_token_expires_at = now + timedelta(seconds=_access_token_cache.expires_in)
    return _access_token_cache.access_token


async def send_subscribe_message(
    openid: str,
    template_id: str,
    data: dict,
    page: str | None = None,
) -> dict:
    if not settings.WECHAT_ENABLED:
        raise ValueError("WECHAT_ENABLED is false")

    token = await get_wechat_access_token()
    payload = {
        "touser": openid,
        "template_id": template_id,
        "page": page or settings.WECHAT_SUBSCRIBE_PAGE,
        "data": data,
        "miniprogram_state": settings.WECHAT_SUBSCRIBE_MINIPROGRAM_STATE,
        "lang": settings.WECHAT_SUBSCRIBE_LANG,
    }

    async def _post(current_token: str) -> dict:
        url = _build_api_url("/cgi-bin/message/subscribe/send", access_token=current_token)
        return await _request_json(url, method="POST", payload=payload)

    body = await _post(token)
    if body.get("errcode") == 40001:
        token = await get_wechat_access_token(force_refresh=True)
        body = await _post(token)
    if body.get("errcode"):
        raise ValueError(body.get("errmsg") or "Failed to send WeChat subscribe message")
    return body


async def get_user_by_wechat_open_id(db: AsyncSession, wechat_open_id: str) -> User | None:
    result = await db.execute(select(User).where(User.wechat_open_id == wechat_open_id))
    return result.scalar_one_or_none()


async def bind_wechat_identity(
    db: AsyncSession,
    user: User,
    payload: WechatIdentityPayload,
) -> User:
    wechat_open_id, wechat_union_id = await resolve_wechat_identity_async(payload)
    existing_user = await get_user_by_wechat_open_id(db, wechat_open_id)
    if existing_user and existing_user.id != user.id:
        raise ValueError("This WeChat account is already bound to another user")

    user.wechat_open_id = wechat_open_id
    user.wechat_union_id = wechat_union_id
    user.wechat_bound_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user
