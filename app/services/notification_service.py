from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import NotificationListResponse, NotificationResponse, NotificationUnreadCountResponse


class NotificationService:
    _instance: NotificationService | None = None
    _in_memory_notifications: list[dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> NotificationService:
        if cls._instance is None:
            cls._instance = NotificationService()
        return cls._instance

    def _to_response(self, item: Notification | dict[str, Any]) -> NotificationResponse:
        if isinstance(item, Notification):
            meta_dict = {}
            if item.metadata_json:
                try:
                    meta_dict = json.loads(item.metadata_json)
                except Exception:
                    pass
            created_str = item.created_at.isoformat() if hasattr(item.created_at, "isoformat") else str(item.created_at)
            return NotificationResponse(
                id=item.id,
                type=item.type,
                title=item.title,
                message=item.message,
                priority=item.priority,
                is_read=item.is_read,
                created_at=created_str,
                action_url=item.action_url or "/dashboard",
                metadata=meta_dict,
            )
        else:
            return NotificationResponse(
                id=item["id"],
                type=item["type"],
                title=item["title"],
                message=item["message"],
                priority=item["priority"],
                is_read=item["is_read"],
                created_at=item["created_at"],
                action_url=item.get("action_url", "/dashboard"),
                metadata=item.get("metadata", {}),
            )

    def create_notification(
        self,
        user_id: str,
        n_type: str,
        title: str,
        message: str,
        priority: str = "moderate",
        action_url: str = "/dashboard",
        metadata: dict[str, Any] | None = None,
        db: Session | None = None,
    ) -> NotificationResponse:
        nid = f"notif-{uuid4().hex[:10]}"
        meta_json = json.dumps(metadata or {})
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        if db is not None:
            obj = Notification(
                id=nid,
                user_id=user_id,
                type=n_type,
                title=title,
                message=message,
                priority=priority,
                is_read=False,
                action_url=action_url,
                metadata_json=meta_json,
                created_at=now_dt,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return self._to_response(obj)
        else:
            item = {
                "id": nid,
                "user_id": user_id,
                "type": n_type,
                "title": title,
                "message": message,
                "priority": priority,
                "is_read": False,
                "action_url": action_url,
                "metadata": metadata or {},
                "created_at": now_iso,
            }
            self._in_memory_notifications.append(item)
            return self._to_response(item)

    def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        db: Session | None = None,
    ) -> NotificationListResponse:
        if db is not None:
            query = db.query(Notification).filter(Notification.user_id == user_id)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            objs = query.order_by(Notification.created_at.desc()).limit(limit).all()
            
            total_count = db.query(Notification).filter(Notification.user_id == user_id).count()
            unread_count = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()
            
            res_items = [self._to_response(o) for o in objs]
            return NotificationListResponse(notifications=res_items, total_count=total_count, unread_count=unread_count)
        else:
            user_items = [n for n in self._in_memory_notifications if n["user_id"] == user_id]
            if unread_only:
                user_items = [n for n in user_items if not n["is_read"]]
            user_items.sort(key=lambda x: x["created_at"], reverse=True)
            
            total_count = len([n for n in self._in_memory_notifications if n["user_id"] == user_id])
            unread_count = len([n for n in self._in_memory_notifications if n["user_id"] == user_id and not n["is_read"]])
            
            res_items = [self._to_response(n) for n in user_items[:limit]]
            return NotificationListResponse(notifications=res_items, total_count=total_count, unread_count=unread_count)

    def get_notification(self, user_id: str, notification_id: str, db: Session | None = None) -> NotificationResponse:
        if db is not None:
            obj = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
            if not obj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            return self._to_response(obj)
        else:
            item = next((n for n in self._in_memory_notifications if n["id"] == notification_id and n["user_id"] == user_id), None)
            if not item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            return self._to_response(item)

    def mark_as_read(self, user_id: str, notification_id: str, db: Session | None = None) -> NotificationResponse:
        if db is not None:
            obj = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
            if not obj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            obj.is_read = True
            db.commit()
            db.refresh(obj)
            return self._to_response(obj)
        else:
            item = next((n for n in self._in_memory_notifications if n["id"] == notification_id and n["user_id"] == user_id), None)
            if not item:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            item["is_read"] = True
            return self._to_response(item)

    def mark_all_as_read(self, user_id: str, db: Session | None = None) -> NotificationUnreadCountResponse:
        if db is not None:
            db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({"is_read": True})
            db.commit()
            return NotificationUnreadCountResponse(unread_count=0)
        else:
            for n in self._in_memory_notifications:
                if n["user_id"] == user_id:
                    n["is_read"] = True
            return NotificationUnreadCountResponse(unread_count=0)

    def delete_notification(self, user_id: str, notification_id: str, db: Session | None = None) -> dict[str, str]:
        if db is not None:
            obj = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
            if not obj:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            db.delete(obj)
            db.commit()
            return {"status": "ok", "deleted_id": notification_id}
        else:
            idx = next((i for i, n in enumerate(self._in_memory_notifications) if n["id"] == notification_id and n["user_id"] == user_id), None)
            if idx is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification '{notification_id}' not found.")
            self._in_memory_notifications.pop(idx)
            return {"status": "ok", "deleted_id": notification_id}

    def get_unread_count(self, user_id: str, db: Session | None = None) -> NotificationUnreadCountResponse:
        if db is not None:
            cnt = db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).count()
            return NotificationUnreadCountResponse(unread_count=cnt)
        else:
            cnt = len([n for n in self._in_memory_notifications if n["user_id"] == user_id and not n["is_read"]])
            return NotificationUnreadCountResponse(unread_count=cnt)

    def clear_notifications(self, user_id: str | None = None) -> None:
        if user_id:
            self._in_memory_notifications = [n for n in self._in_memory_notifications if n["user_id"] != user_id]
        else:
            self._in_memory_notifications.clear()


notification_service = NotificationService.get_instance()
