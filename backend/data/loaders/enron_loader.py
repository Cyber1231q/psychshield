"""Enron loader — provides benign email samples for evaluation.

The Enron corpus was unavailable for download, so this module provides
synthetic benign emails as a permanent fallback for training and evaluation.
"""

import logging

import pandas as pd

logger = logging.getLogger("psychshield")

SYNTHETIC_BENIGN: list[str] = [
    "Hi team, the project meeting is scheduled for Friday at 2pm. Please bring your progress reports.",
    "Reminder: Annual leave requests must be submitted by end of the month.",
    "The quarterly review is next week. Please prepare your department summaries.",
    "Just checking in on the status of the client deliverable. Let me know if you need support.",
    "Congratulations to everyone on completing the milestone. Great work this quarter.",
    "The conference room on the third floor is booked from 9am to 11am on Monday.",
    "Please find attached the updated project timeline for your review and feedback.",
    "Training session for the new HR system is scheduled for Tuesday afternoon.",
    "The new printer has been installed near reception on the second floor.",
    "Weekly update: upcoming deadlines and team announcements are listed below.",
    "Can we reschedule our 1-on-1 to Thursday? I have a conflict on Wednesday.",
    "The IT team will be performing maintenance on Sunday night from 10pm to 2am.",
    "Please submit your expense reports before the end of the financial quarter.",
    "The office will be closed on the public holiday next Monday.",
    "We are pleased to announce the promotion of three team members this month.",
    "The catering order for the board meeting has been confirmed for 12 people.",
    "Please review the attached policy document and confirm your acknowledgement.",
    "The monthly newsletter is attached. Key highlights are on page 2.",
    "Reminder to all staff: fire drill scheduled for Wednesday at 11am.",
    "The parking allocation for Q3 has been updated. Check the shared drive for details.",
    "The client presentation has been rescheduled to next Tuesday at 10am.",
    "Please ensure all project files are uploaded to the shared drive by Friday.",
    "The team lunch is confirmed for Thursday at 1pm at the usual restaurant.",
    "Kindly note that the system will be unavailable for scheduled maintenance tonight.",
    "Your timesheet for last week has been approved by your line manager.",
    "The budget proposal for Q4 has been reviewed and approved by finance.",
    "Please join us for the welcome reception for our new team members on Friday.",
    "The annual performance review cycle begins next month. Watch for calendar invites.",
    "The building access cards will be renewed during the first week of next month.",
    "All staff are reminded to complete the mandatory compliance training by Friday.",
]


def load_enron_dataframe(
    path: str = None,
    max_emails: int = 2000,
) -> pd.DataFrame:
    """Load benign email samples for evaluation.

    Args:
        path: Ignored (kept for interface compatibility).
        max_emails: Number of email samples to generate.

    Returns:
        DataFrame with columns: body, label, source.
    """
    logger.info(
        "Enron dataset not available — "
        "using synthetic benign emails as fallback"
    )
    emails = SYNTHETIC_BENIGN * (max_emails // len(SYNTHETIC_BENIGN) + 1)
    result = pd.DataFrame({
        "body": emails[:max_emails],
        "label": 0,
        "source": "synthetic_benign",
    })
    return result


def get_enron_stats() -> dict:
    """Return status information about the Enron dataset.

    Returns:
        Dict with availability status and notes.
    """
    return {
        "available": False,
        "source": "synthetic_benign",
        "count": len(SYNTHETIC_BENIGN),
        "note": "Enron corpus unavailable — synthetic benign emails used",
        "thesis_note": "GoEmotions dataset used for training (91.05% accuracy)",
    }
