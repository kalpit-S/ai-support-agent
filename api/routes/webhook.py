"""
Webhook endpoints for receiving SMS and Email messages.

SECURITY NOTE: In production, these endpoints should verify request signatures:
- Twilio SMS: Validate X-Twilio-Signature header using twilio.request_validator
- SendGrid Email: Validate webhook signatures or use signed event webhooks
This demo omits signature verification for simplicity.
"""
import uuid
import time
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import redis

from database import get_db
from models import Customer, Message
from config import settings


router = APIRouter()


class SMSWebhookRequest(BaseModel):
    """Incoming SMS webhook payload."""
    from_number: str = Field(alias="from")
    body: str

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "from_number": "+15551234567",
                "body": "Hi, I need help with my billing"
            }
        }


class SMSWebhookResponse(BaseModel):
    status: str
    message_id: int
    customer_id: int
    batch_id: str


class EmailWebhookRequest(BaseModel):
    """Incoming Email webhook payload."""
    from_email: str
    body: str
    subject: str = ""

    class Config:
        json_schema_extra = {
            "example": {
                "from_email": "customer@example.com",
                "subject": "Help with API integration",
                "body": "Hi, I'm having trouble setting up webhooks..."
            }
        }


class EmailWebhookResponse(BaseModel):
    status: str
    message_id: int
    customer_id: int
    batch_id: str


def get_redis():
    return redis.from_url(settings.redis_url, decode_responses=True)


@router.post("/sms", response_model=SMSWebhookResponse)
def receive_sms(payload: SMSWebhookRequest, db: Session = Depends(get_db)):
    """Receive an inbound SMS message."""
    # Find customer by phone number first
    customer = db.query(Customer).filter(Customer.phone_number == payload.from_number).first()

    if not customer:
        # For demo: check if there's a customer without phone but with demo email
        # This links SMS to existing email customer for cross-channel demo
        demo_email = "kal@example.com"
        customer = db.query(Customer).filter(
            Customer.email == demo_email,
            Customer.phone_number.is_(None)
        ).first()

        if customer:
            # Link phone to existing email customer
            customer.phone_number = payload.from_number
            db.commit()
        else:
            # Create new customer
            customer = Customer(phone_number=payload.from_number, extracted_data={})
            db.add(customer)
            db.commit()
            db.refresh(customer)

    # Get or create batch ID for this customer
    r = get_redis()
    batch_key = f"batch:customer:{customer.id}"

    existing_batch_id = r.get(f"{batch_key}:id")
    batch_id = existing_batch_id if existing_batch_id else str(uuid.uuid4())

    if not existing_batch_id:
        r.set(f"{batch_key}:id", batch_id)

    # Create the message record
    message = Message(
        customer_id=customer.id,
        direction="inbound",
        channel="sms",
        content=payload.body,
        batch_id=uuid.UUID(batch_id),
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Add message to batch in Redis
    r.rpush(batch_key, message.id)
    r.set(f"{batch_key}:id", batch_id)
    r.set(f"{batch_key}:updated", time.time())

    return SMSWebhookResponse(
        status="received",
        message_id=message.id,
        customer_id=customer.id,
        batch_id=batch_id,
    )


@router.post("/email", response_model=EmailWebhookResponse)
def receive_email(payload: EmailWebhookRequest, db: Session = Depends(get_db)):
    """Receive an inbound Email message."""
    # Find customer by email first
    customer = db.query(Customer).filter(Customer.email == payload.from_email).first()

    if not customer:
        # For demo: check if there's a customer without email but with demo phone
        # This links email to existing SMS customer for cross-channel demo
        demo_phone = "+15551234567"
        customer = db.query(Customer).filter(
            Customer.phone_number == demo_phone,
            Customer.email.is_(None)
        ).first()

        if customer:
            # Link email to existing phone customer
            customer.email = payload.from_email
            db.commit()
        else:
            # Create new customer
            customer = Customer(email=payload.from_email, extracted_data={})
            db.add(customer)
            db.commit()
            db.refresh(customer)

    # Get or create batch ID for this customer
    r = get_redis()
    batch_key = f"batch:customer:{customer.id}"

    existing_batch_id = r.get(f"{batch_key}:id")
    batch_id = existing_batch_id if existing_batch_id else str(uuid.uuid4())

    if not existing_batch_id:
        r.set(f"{batch_key}:id", batch_id)

    # Create the message record
    message = Message(
        customer_id=customer.id,
        direction="inbound",
        channel="email",
        content=payload.body,
        batch_id=uuid.UUID(batch_id),
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Add message to batch in Redis
    r.rpush(batch_key, message.id)
    r.set(f"{batch_key}:id", batch_id)
    r.set(f"{batch_key}:updated", time.time())

    return EmailWebhookResponse(
        status="received",
        message_id=message.id,
        customer_id=customer.id,
        batch_id=batch_id,
    )
