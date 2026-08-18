import datetime

from bot.services.submission_service import SubmissionService


async def check_spam(
    submission_service: SubmissionService,
    user_id: int,
    max_submissions: int = 5,
    period_seconds: int = 60,
) -> bool:
    """Return True if the user has exceeded the submission rate limit.

    Default: maximum 5 submissions per 60 seconds.
    """
    since = datetime.datetime.utcnow() - datetime.timedelta(seconds=period_seconds)
    count = await submission_service.get_submission_count_since(user_id, since)
    return count >= max_submissions
