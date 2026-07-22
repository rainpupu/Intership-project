from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CloudAdoptionOrderCreate(BaseModel):
    cat_id: str = Field(..., alias="catId")
    gift_id: str = Field(..., alias="giftId")
    gift_category: str = Field(..., alias="giftCategory")
    gift_name: str = Field(..., alias="giftName")
    gift_description: str = Field(default="", alias="giftDescription")
    gift_icon: str = Field(default="", alias="giftIcon")
    quantity: int = Field(default=1, ge=1, le=99)
    unit_price: int = Field(..., alias="unitPrice", ge=0)
    payment_method: str = Field(..., alias="paymentMethod")

    model_config = {"populate_by_name": True}


class CloudAdoptionOrderResponse(BaseModel):
    id: str
    order_no: str = Field(..., alias="orderNo")
    cat_id: str = Field(..., alias="catId")
    cat_name: str = Field(..., alias="catName")
    cat_code: str = Field(..., alias="catCode")
    cat_cover_image: str = Field(default="", alias="catCoverImage")
    user_id: str = Field(default="", alias="userId")
    supporter_name: str = Field(default="匿名用户", alias="supporterName")
    gift_id: str = Field(..., alias="giftId")
    gift_category: str = Field(..., alias="giftCategory")
    gift_name: str = Field(..., alias="giftName")
    gift_description: str = Field(default="", alias="giftDescription")
    gift_icon: str = Field(default="", alias="giftIcon")
    quantity: int
    unit_price: int = Field(..., alias="unitPrice")
    total_amount: int = Field(..., alias="totalAmount")
    payment_method: str = Field(..., alias="paymentMethod")
    status: str
    created_at: datetime = Field(..., alias="createdAt")

    model_config = {"populate_by_name": True}
