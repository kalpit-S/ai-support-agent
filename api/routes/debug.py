from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import Customer, KnowledgeBaseArticle, Message, Ticket


router = APIRouter()


class MessageResponse(BaseModel):
    id: int
    customer_id: int
    direction: str
    channel: str = "sms"
    content: str
    batch_id: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerResponse(BaseModel):
    id: int
    phone_number: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    account_tier: Optional[str] = None
    extracted_data: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerWithMessagesResponse(CustomerResponse):
    messages: List[MessageResponse] = Field(default_factory=list)


class ArticleResponse(BaseModel):
    id: int
    article_id: str
    title: str
    content: str
    article_metadata: dict
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class TicketResponse(BaseModel):
    id: int
    customer_id: int
    article_id: Optional[int] = None
    status: str
    issue_type: Optional[str] = None
    severity: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(db: Session = Depends(get_db), limit: int = 100):
    """List all customers."""
    return db.query(Customer).limit(limit).all()


@router.get("/customers/{customer_id}", response_model=CustomerWithMessagesResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    """Get a specific customer with their messages."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    messages = [
        MessageResponse(
            id=msg.id,
            customer_id=msg.customer_id,
            direction=msg.direction,
            channel=msg.channel,
            content=msg.content,
            batch_id=str(msg.batch_id) if msg.batch_id else None,
            metadata=msg.message_metadata if hasattr(msg, 'message_metadata') else None,
            created_at=msg.created_at,
        )
        for msg in customer.messages
    ]

    return CustomerWithMessagesResponse(
        id=customer.id,
        phone_number=customer.phone_number,
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        company_name=customer.company_name,
        account_tier=customer.account_tier,
        extracted_data=customer.extracted_data,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
        messages=messages,
    )


@router.get("/messages/{customer_id}", response_model=List[MessageResponse])
def get_customer_messages(customer_id: int, db: Session = Depends(get_db), limit: int = 100):
    """Get messages for a specific customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    messages = db.query(Message).filter(
        Message.customer_id == customer_id
    ).order_by(Message.created_at).limit(limit).all()

    return [
        MessageResponse(
            id=msg.id,
            customer_id=msg.customer_id,
            direction=msg.direction,
            channel=msg.channel,
            content=msg.content,
            batch_id=str(msg.batch_id) if msg.batch_id else None,
            metadata=msg.message_metadata if hasattr(msg, 'message_metadata') else None,
            created_at=msg.created_at,
        )
        for msg in messages
    ]


@router.get("/articles", response_model=List[ArticleResponse])
def list_articles(db: Session = Depends(get_db), status: Optional[str] = None):
    """List all knowledge base articles."""
    query = db.query(KnowledgeBaseArticle)
    if status:
        query = query.filter(KnowledgeBaseArticle.status == status)
    return query.all()


@router.get("/articles/{article_id}", response_model=ArticleResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Get a specific article by ID."""
    article = db.query(KnowledgeBaseArticle).filter(KnowledgeBaseArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@router.get("/tickets/{customer_id}", response_model=List[TicketResponse])
def get_customer_tickets(customer_id: int, db: Session = Depends(get_db)):
    """Get all tickets for a customer."""
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return db.query(Ticket).filter(
        Ticket.customer_id == customer_id
    ).all()
