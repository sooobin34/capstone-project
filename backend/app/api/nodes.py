from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.iot_node import IotNode
from app.schemas.iot_node import IotNodeCreate
from app.utils.response import success_response

router = APIRouter(prefix="/nodes", tags=["Nodes"])


@router.post("")
def create_node(payload: IotNodeCreate, db: Session = Depends(get_db)):
    existing_node = db.query(IotNode).filter(IotNode.mac_address == payload.mac_address).first()
    if existing_node:
        raise HTTPException(status_code=400, detail="이미 등록된 mac_address입니다.")

    node = IotNode(
        mac_address=payload.mac_address,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location_desc=payload.location_desc,
        is_active=payload.is_active,
    )

    db.add(node)
    db.commit()
    db.refresh(node)

    return success_response(node, "노드 등록 성공")


@router.get("")
def get_nodes(db: Session = Depends(get_db)):
    nodes = db.query(IotNode).order_by(IotNode.id.asc()).all()
    return success_response(nodes, "노드 목록 조회 성공")