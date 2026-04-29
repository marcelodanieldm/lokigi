from __future__ import annotations

from urllib.parse import parse_qs

import socketio


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socketio_app = socketio.ASGIApp(sio)


def _room_for_user(user_id: str) -> str:
    return f"starter-user:{user_id}"


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None) -> bool:
    query = parse_qs(environ.get("QUERY_STRING", ""))
    user_id = (auth or {}).get("user_id") or (query.get("user_id") or [None])[0]
    if not user_id:
        return False
    await sio.save_session(sid, {"user_id": str(user_id)})
    await sio.enter_room(sid, _room_for_user(str(user_id)))
    return True


@sio.event
async def disconnect(sid: str) -> None:
    session = await sio.get_session(sid)
    user_id = session.get("user_id") if session else None
    if user_id:
        await sio.leave_room(sid, _room_for_user(str(user_id)))


async def emit_new_review_ready(
    *,
    user_id: str,
    review_pk: str,
    author: str,
    comment: str,
) -> None:
    snippet = (comment or "").strip()
    if len(snippet) > 120:
        snippet = snippet[:117].rstrip() + "..."
    await sio.emit(
        "new_review_ready",
        {
            "review_pk": review_pk,
            "author": author,
            "comment_snippet": snippet,
        },
        room=_room_for_user(user_id),
    )