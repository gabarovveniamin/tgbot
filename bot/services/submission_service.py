import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.media import Media
from bot.models.submission import Submission


class SubmissionService:
    """Service layer for submission-related database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_submission(self, user_id: int) -> Submission:
        """Create a new pending submission."""
        submission = Submission(user_id=user_id, status="pending")
        self.session.add(submission)
        await self.session.commit()
        await self.session.refresh(submission)
        return submission

    async def add_media(
        self,
        submission_id: int,
        file_id: str,
        media_type: str,
        caption: str | None = None,
    ) -> Media:
        """Attach a media item to a submission."""
        media = Media(
            submission_id=submission_id,
            file_id=file_id,
            media_type=media_type,
            caption=caption,
        )
        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)
        return media

    async def get_submission(self, submission_id: int) -> Submission | None:
        """Get a submission by ID (with media_items eagerly loaded)."""
        result = await self.session.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, submission_id: int, status: str) -> None:
        """Set the status of a submission (pending / published / rejected)."""
        result = await self.session.execute(
            select(Submission).where(Submission.id == submission_id)
        )
        submission = result.scalar_one_or_none()
        if submission:
            submission.status = status
            await self.session.commit()

    async def get_submission_count_since(
        self, user_id: int, since: datetime.datetime
    ) -> int:
        """Count submissions by a user created after *since*. Used for spam protection."""
        result = await self.session.execute(
            select(func.count(Submission.id)).where(
                Submission.user_id == user_id,
                Submission.created_at >= since,
            )
        )
        return result.scalar() or 0
