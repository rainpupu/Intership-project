from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.entity.db_models import Cat, CloudAdoptionOrder, User


def _external_cat_id(cat: Cat) -> str:
    return cat.code or str(cat.id)


def _supporter_name(user: User | None) -> str:
    if user is None:
        return "匿名用户"
    return user.nickname or user.phone or user.username or f"用户 {user.id}"


def _order_to_dict(order: CloudAdoptionOrder) -> dict:
    cat = order.cat
    return {
        "id": str(order.id),
        "orderNo": order.order_no,
        "catId": _external_cat_id(cat) if cat else str(order.cat_id),
        "catName": cat.name if cat else "未知猫咪",
        "catCode": cat.code if cat else str(order.cat_id),
        "catCoverImage": cat.cover_image if cat else "",
        "userId": str(order.user_id or ""),
        "supporterName": order.supporter_name or _supporter_name(order.user),
        "giftId": order.gift_id,
        "giftCategory": order.gift_category,
        "giftName": order.gift_name,
        "giftDescription": order.gift_description or "",
        "giftIcon": order.gift_icon or "",
        "quantity": order.quantity,
        "unitPrice": order.unit_price,
        "totalAmount": order.total_amount,
        "paymentMethod": order.payment_method,
        "status": order.status,
        "createdAt": order.created_at.isoformat() if order.created_at else None,
    }


class CloudAdoptionService:
    @staticmethod
    def create_order(db: Session, payload: dict, current_user: User) -> dict:
        cat_id = payload.get("cat_id")
        filters = [Cat.code == str(cat_id)]
        if str(cat_id).isdigit():
            filters.append(Cat.id == int(cat_id))
        cat = db.query(Cat).filter(or_(*filters)).first()
        if cat is None:
            raise HTTPException(status_code=404, detail="猫咪档案不存在")

        quantity = int(payload.get("quantity") or 1)
        unit_price = int(payload.get("unit_price") or 0)
        order = CloudAdoptionOrder(
            order_no=f"CA{datetime.now():%Y%m%d%H%M%S%f}",
            cat_id=cat.id,
            user_id=current_user.id,
            supporter_name=_supporter_name(current_user),
            gift_id=payload["gift_id"],
            gift_category=payload["gift_category"],
            gift_name=payload["gift_name"],
            gift_description=payload.get("gift_description") or "",
            gift_icon=payload.get("gift_icon") or "",
            quantity=quantity,
            unit_price=unit_price,
            total_amount=quantity * unit_price,
            payment_method=payload["payment_method"],
            status="已记录",
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return _order_to_dict(order)

    @staticmethod
    def list_orders(db: Session) -> list[dict]:
        orders = (
            db.query(CloudAdoptionOrder)
            .options(joinedload(CloudAdoptionOrder.cat), joinedload(CloudAdoptionOrder.user))
            .order_by(CloudAdoptionOrder.created_at.desc(), CloudAdoptionOrder.id.desc())
            .all()
        )
        return [_order_to_dict(order) for order in orders]


cloud_adoption_service = CloudAdoptionService()
