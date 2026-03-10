from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import List
import phonenumbers


# =====================================================
# Invoice Item (Input)
# =====================================================
class InvoiceItemCreate(BaseModel):
    product_id: UUID
    quantity: int


# =====================================================
# Invoice Create (Input)
# =====================================================
class InvoiceCreate(BaseModel):
    customer_name: str
    customer_phone: str | None = None
    items: List[InvoiceItemCreate]

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        try:
            # If no country code, assume India (change if needed)
            if not value.startswith("+"):
                parsed_number = phonenumbers.parse(value, "IN")
            else:
                parsed_number = phonenumbers.parse(value, None)

            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError("Invalid phone number")

            # Convert to international E.164 format
            return phonenumbers.format_number(
                parsed_number,
                phonenumbers.PhoneNumberFormat.E164
            )

        except Exception:
            raise ValueError("Invalid phone number format")


# =====================================================
# Invoice Response (Output)
# =====================================================
class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    customer_name: str
    customer_phone: str | None
    total_amount: float
    payment_status: str

    class Config:
        from_attributes = True

