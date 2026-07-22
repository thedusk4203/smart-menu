from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlmodel import Session

from app.core.exceptions import ConflictError, NotFoundError


MAX_CONVERSATIONS = 10
MAX_TURNS = 20
CONVERSATION_RETENTION_DAYS = 30


def make_conversation_title(message: str) -> str:
    normalized = " ".join(message.split())
    if len(normalized) <= 80:
        return normalized
    return normalized[:77].rstrip() + "..."


class ConversationStore:
    """Kho lịch sử chat của người dùng, độc lập với AI request logs."""

    def __init__(self, session: Session, actor_id: int | None = None) -> None:
        self.session = session
        self.actor_id = actor_id

    def _set_actor(self) -> None:
        if self.actor_id is not None:
            self.session.execute(
                text("SELECT set_config('app.current_user_id', :actor_id, true)"),
                {"actor_id": str(self.actor_id)},
            )

    def list_for_user(self, user_id: int) -> list[dict[str, Any]]:
        self._set_actor()
        rows = self.session.execute(
            text(
                """SELECT c.id, c.title, c.mode, COUNT(t.id)::integer AS turn_count,
                          (SELECT LEFT(COALESCE(NULLIF(last_turn.assistant_content, ''),
                                                last_turn.user_content), 160)
                             FROM ai_conversation_turns last_turn
                            WHERE last_turn.conversation_id = c.id
                            ORDER BY last_turn.turn_number DESC LIMIT 1)
                              AS last_message_preview,
                          c.created_at, c.updated_at
                     FROM ai_conversations c
                     LEFT JOIN ai_conversation_turns t ON t.conversation_id = c.id
                    WHERE c.user_id = :user_id
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC, c.id DESC
                    LIMIT :limit"""
            ),
            {"user_id": user_id, "limit": MAX_CONVERSATIONS},
        ).mappings().all()
        return [dict(row) for row in rows]

    def get_for_user(self, conversation_id: int, user_id: int) -> dict[str, Any]:
        self._set_actor()
        conversation = self._owned_conversation(conversation_id, user_id)
        turns = self.session.execute(
            text(
                """SELECT id, turn_number, user_content, assistant_content, status,
                          personalization_used, grounding_mode, citations,
                          created_at, updated_at
                     FROM ai_conversation_turns
                    WHERE conversation_id = :conversation_id
                    ORDER BY turn_number"""
            ),
            {"conversation_id": conversation_id},
        ).mappings().all()
        result = dict(conversation)
        result["turns"] = [dict(row) for row in turns]
        result["turn_count"] = len(turns)
        last_message = (
            (turns[-1]["assistant_content"] or turns[-1]["user_content"]) if turns else None
        )
        result["last_message_preview"] = last_message[:160] if last_message else None
        return result

    def delete_for_user(self, conversation_id: int, user_id: int) -> None:
        self._set_actor()
        deleted = self.session.execute(
            text(
                "DELETE FROM ai_conversations WHERE id=:id AND user_id=:user_id RETURNING id"
            ),
            {"id": conversation_id, "user_id": user_id},
        ).scalar_one_or_none()
        if deleted is None:
            self.session.rollback()
            raise NotFoundError("Không tìm thấy cuộc hội thoại.")
        self.session.commit()

    def mode_for_user(self, conversation_id: int, user_id: int) -> str:
        self._set_actor()
        return str(self._owned_conversation(conversation_id, user_id)["mode"])

    def start_turn(
        self,
        *,
        user_id: int,
        message: str,
        conversation_id: int | None,
        mode: str = "general",
    ) -> tuple[int, dict[str, Any]]:
        self._set_actor()
        if conversation_id is None:
            # Advisory lock avoids requiring AI state role to read/write business users.
            self.session.execute(
                text("SELECT pg_advisory_xact_lock(7411, :user_id)"),
                {"user_id": user_id},
            )
            count = self.session.execute(
                text("SELECT COUNT(*) FROM ai_conversations WHERE user_id=:user_id"),
                {"user_id": user_id},
            ).scalar_one()
            if count >= MAX_CONVERSATIONS:
                self.session.rollback()
                raise ConflictError(
                    "Bạn đã lưu đủ 10 cuộc hội thoại. Hãy xóa một cuộc trước khi tạo mới."
                )
            conversation_id = int(
                self.session.execute(
                    text(
                        """INSERT INTO ai_conversations (user_id, title, mode)
                           VALUES (:user_id, :title, :mode) RETURNING id"""
                    ),
                    {
                        "user_id": user_id,
                        "title": make_conversation_title(message),
                        "mode": mode,
                    },
                ).scalar_one()
            )
        else:
            owned = self._lock_owned_conversation(conversation_id, user_id)
            if str(owned["mode"]) != mode:
                self.session.rollback()
                raise ConflictError(
                    "Không thể đổi chế độ của cuộc hội thoại đang có. Hãy tạo cuộc mới."
                )

        latest = self.session.execute(
            text(
                """SELECT id, status FROM ai_conversation_turns
                    WHERE conversation_id=:conversation_id
                    ORDER BY turn_number DESC LIMIT 1"""
            ),
            {"conversation_id": conversation_id},
        ).mappings().first()
        if latest and latest["status"] != "completed":
            self.session.rollback()
            detail = (
                "Menuto đang trả lời câu hỏi gần nhất."
                if latest["status"] == "pending"
                else "Hãy retry câu hỏi gần nhất trước khi tiếp tục cuộc hội thoại."
            )
            raise ConflictError(detail)

        turn_count = int(
            self.session.execute(
                text(
                    "SELECT COUNT(*) FROM ai_conversation_turns WHERE conversation_id=:id"
                ),
                {"id": conversation_id},
            ).scalar_one()
        )
        if turn_count >= MAX_TURNS:
            self.session.rollback()
            raise ConflictError(
                "Cuộc hội thoại đã đạt giới hạn 20 câu. Hãy bắt đầu cuộc mới."
            )

        turn = self.session.execute(
            text(
                """INSERT INTO ai_conversation_turns
                       (conversation_id, turn_number, user_content, status)
                   VALUES (:conversation_id, :turn_number, :message, 'pending')
                   RETURNING id, turn_number, user_content, assistant_content, status,
                             personalization_used, grounding_mode, citations,
                             created_at, updated_at"""
            ),
            {
                "conversation_id": conversation_id,
                "turn_number": turn_count + 1,
                "message": message,
            },
        ).mappings().one()
        self._touch(conversation_id)
        self.session.commit()
        return conversation_id, dict(turn)

    def prepare_retry(
        self, *, conversation_id: int, turn_id: int, user_id: int
    ) -> dict[str, Any]:
        self._set_actor()
        owned = self._lock_owned_conversation(conversation_id, user_id)
        latest = self.session.execute(
            text(
                """SELECT id, turn_number, user_content, assistant_content, status,
                          personalization_used, grounding_mode, citations,
                          created_at, updated_at
                     FROM ai_conversation_turns
                    WHERE conversation_id=:conversation_id
                    ORDER BY turn_number DESC LIMIT 1
                    FOR UPDATE"""
            ),
            {"conversation_id": conversation_id},
        ).mappings().first()
        if latest is None or int(latest["id"]) != turn_id:
            self.session.rollback()
            raise ConflictError("Chỉ có thể retry câu hỏi gần nhất trong cuộc hội thoại.")
        if latest["status"] == "pending":
            self.session.rollback()
            raise ConflictError("Menuto đang xử lý câu hỏi này.")
        pending = self.session.execute(
            text(
                """UPDATE ai_conversation_turns
                      SET status='pending', updated_at=NOW()
                    WHERE id=:id
                    RETURNING id, turn_number, user_content, assistant_content, status,
                              personalization_used, grounding_mode, citations,
                              created_at, updated_at"""
            ),
            {"id": turn_id},
        ).mappings().one()
        self._touch(conversation_id)
        self.session.commit()
        result = dict(pending)
        result["conversation_mode"] = str(owned["mode"])
        return result

    def completed_turns_before(
        self, *, conversation_id: int, turn_number: int
    ) -> list[dict[str, Any]]:
        self._set_actor()
        rows = self.session.execute(
            text(
                """SELECT id, turn_number, user_content, assistant_content, status,
                          personalization_used, grounding_mode, citations,
                          created_at, updated_at
                     FROM ai_conversation_turns
                    WHERE conversation_id=:conversation_id
                      AND turn_number < :turn_number
                      AND status='completed'
                      AND assistant_content IS NOT NULL
                    ORDER BY turn_number"""
            ),
            {"conversation_id": conversation_id, "turn_number": turn_number},
        ).mappings().all()
        return [dict(row) for row in rows]

    def complete_turn(
        self, *, conversation_id: int, turn_id: int, assistant_content: str,
        personalization_used: bool = False, grounding_mode: str = "none",
        citations: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        self._set_actor()
        turn = self.session.execute(
            text(
                """UPDATE ai_conversation_turns
                      SET assistant_content=:content, status='completed', updated_at=NOW(),
                          personalization_used=:personalization_used,
                          grounding_mode=:grounding_mode,
                          citations=CAST(:citations AS JSONB)
                    WHERE id=:turn_id AND conversation_id=:conversation_id
                    RETURNING id, turn_number, user_content, assistant_content, status,
                              personalization_used, grounding_mode, citations,
                              created_at, updated_at"""
            ),
            {
                "turn_id": turn_id,
                "conversation_id": conversation_id,
                "content": assistant_content,
                "personalization_used": personalization_used,
                "grounding_mode": grounding_mode,
                "citations": json.dumps(citations or []),
            },
        ).mappings().one()
        self._touch(conversation_id)
        self.session.commit()
        return dict(turn)

    def fail_turn(
        self,
        *,
        conversation_id: int,
        turn_id: int,
    ) -> None:
        self._set_actor()
        self.session.execute(
            text(
                """UPDATE ai_conversation_turns SET status=:status, updated_at=NOW()
                    WHERE id=:turn_id AND conversation_id=:conversation_id"""
            ),
            {
                "status": "failed",
                "turn_id": turn_id,
                "conversation_id": conversation_id,
            },
        )
        self._touch(conversation_id)
        self.session.commit()

    def purge_expired(self) -> int:
        """Xóa toàn bộ conversation không hoạt động quá 30 ngày.

        Foreign key `ON DELETE CASCADE` đảm bảo các turns liên quan cũng bị xóa.
        Method này được gọi bởi lifecycle nền và ngay trước các thao tác đọc/ghi
        để bản ghi quá hạn không thể xuất hiện lại giữa hai lần chạy job.
        """
        deleted = self.session.execute(
            text(
                """DELETE FROM ai_conversations
                     WHERE updated_at < NOW() - make_interval(days => :retention_days)
                 RETURNING id"""
            ),
            {"retention_days": CONVERSATION_RETENTION_DAYS},
        ).scalars().all()
        self.session.commit()
        return len(deleted)

    def _owned_conversation(self, conversation_id: int, user_id: int):
        row = self.session.execute(
            text(
                """SELECT id, title, mode, created_at, updated_at
                     FROM ai_conversations WHERE id=:id AND user_id=:user_id"""
            ),
            {"id": conversation_id, "user_id": user_id},
        ).mappings().first()
        if row is None:
            raise NotFoundError("Không tìm thấy cuộc hội thoại.")
        return row

    def _lock_owned_conversation(self, conversation_id: int, user_id: int):
        row = self.session.execute(
            text(
                "SELECT id, mode FROM ai_conversations WHERE id=:id AND user_id=:user_id FOR UPDATE"
            ),
            {"id": conversation_id, "user_id": user_id},
        ).mappings().first()
        if row is None:
            self.session.rollback()
            raise NotFoundError("Không tìm thấy cuộc hội thoại.")
        return row

    def _touch(self, conversation_id: int) -> None:
        self.session.execute(
            text("UPDATE ai_conversations SET updated_at=NOW() WHERE id=:id"),
            {"id": conversation_id},
        )
