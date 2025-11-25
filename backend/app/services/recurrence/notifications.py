# ---------------------
# Notifications (placeholder)
# ---------------------
def send_notification(user_id: int, message: str, *, task=None):
    """
    Hook for sending notifications. Replace with your real notification system.
    - In-app notifications: create Notification model entry
    - Emails: enqueue email job
    - Push: integrate push service

    Keep this lightweight: return True/False for success
    """
    # TODO: Replace with actual integration (database + email + websocket push)
    print(f"[NOTIFY] to user {user_id}: {message} (task={getattr(task,'id',None)})")
    return True
