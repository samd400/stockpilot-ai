from app.models.alert import Alert

import uuid


def create_notification(db, user_id, phone_number, message):

    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        phone_number=phone_number,
        message=message,
        status="pending"
    )

    db.add(notification)
    db.commit()

    return notification
