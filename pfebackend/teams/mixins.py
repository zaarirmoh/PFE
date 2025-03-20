

class TeamRequestStatusMixin:
    """
    Mixin for models that require status tracking (invitations, join requests).
    """
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_DECLINED = 'declined'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_EXPIRED, 'Expired'),
        (STATUS_CANCELLED, 'Cancelled'),
    )