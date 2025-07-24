# server/dashboard/websocket.py
"""
WebSocket manager pentru notificări real-time.
"""

from __future__ import annotations
from fastapi import WebSocket, WebSocketDisconnect, Query, Depends, status
from fastapi.exceptions import WebSocketException
from typing import Dict, Set, Optional
import json
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from cfg import get_db, SECRET_KEY, ALGORITHM
from models import Staff


# În metoda connect, elimină try/except care verifică client_state
async def connect(self, websocket: WebSocket, staff_id: int):
    """Conectează un staff member."""
    async with self._lock:
        if staff_id not in self.active_connections:
            self.active_connections[staff_id] = set()
        self.active_connections[staff_id].add(websocket)

    print(f"Manager: Added connection for staff {staff_id}")


class ConnectionManager:
    """Manager pentru conexiuni WebSocket active."""

    def __init__(self):
        # staff_id -> set of websockets
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, staff_id: int):
        """Conectează un staff member."""
        # NU mai face accept aici - se face în endpoint

        async with self._lock:
            if staff_id not in self.active_connections:
                self.active_connections[staff_id] = set()
            self.active_connections[staff_id].add(websocket)

        # Trimite confirmare DOAR dacă conexiunea e deschisă
        try:
            if websocket.client_state.value == 1:  # CONNECTED
                await websocket.send_json({
                    "type": "connection",
                    "status": "connected",
                    "staff_id": staff_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as e:
            print(f"Error sending connection confirmation: {e}")
            # Remove conexiunea dacă nu merge
            await self.disconnect(websocket, staff_id)



    async def disconnect(self, websocket: WebSocket, staff_id: int):
        """Deconectează un staff member."""
        async with self._lock:
            if staff_id in self.active_connections:
                self.active_connections[staff_id].discard(websocket)
                if not self.active_connections[staff_id]:
                    del self.active_connections[staff_id]

    async def send_to_staff(self, staff_id: int, message: dict):
        """Trimite mesaj către un staff specific."""
        if staff_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[staff_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)

            # Curăță conexiunile moarte
            for conn in dead_connections:
                await self.disconnect(conn, staff_id)

    async def broadcast_to_all(self, message: dict):
        """Trimite mesaj către toți staff conectați."""
        tasks = []
        for staff_id in self.active_connections:
            tasks.append(self.send_to_staff(staff_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_order_notification(self, order_data: dict):
        """Trimite notificare pentru comandă nouă."""
        message = {
            "type": "notification",
            "notification_type": "new_order",
            "data": {
                "order_id": order_data.get("id"),
                "order_number": order_data.get("order_number"),
                "client_name": order_data.get("client_name"),
                "total_amount": order_data.get("total_amount"),
                "message": f"Comandă nouă #{order_data.get('order_number')}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_all(message)

    async def send_request_notification(self, request_data: dict):
        """Trimite notificare pentru cerere nouă."""

        print(f"WS Manager - Sending request notification: {request_data}")  # Debug

        message = {
            "type": "notification",
            "notification_type": "new_request",
            "data": {
                "request_id": request_data.get("id"),
                "request_type": request_data.get("request_type"),
                "client_name": request_data.get("client_name"),
                "message": f"Cerere nouă: {request_data.get('request_type')}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        print(f"WS Manager - Active connections: {len(self.active_connections)}")  # Debug
        await self.broadcast_to_all(message)



    def get_connections_count(self) -> dict:
        """Returnează numărul de conexiuni active."""
        return {
            "total_staff": len(self.active_connections),
            "total_connections": sum(len(conns) for conns in self.active_connections.values())
        }

    async def send_status_update(self, status_data: dict):
        """Trimite notificare pentru schimbare status comandă."""
        message = {
            "type": "notification",
            "notification_type": "order_status_changed",
            "data": {
                "order_id": status_data.get("order_id"),
                "order_number": status_data.get("order_number"),
                "old_status": status_data.get("old_status"),
                "new_status": status_data.get("new_status"),
                "message": f"Comanda #{status_data.get('order_number')} - status: {status_data.get('new_status')}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.broadcast_to_all(message)


# Instanță globală
notification_manager = ConnectionManager()


# async def get_current_staff_ws(
#         websocket: WebSocket,
#         token: Optional[str] = Query(None),
#         db: AsyncSession = Depends(get_db)
# ) -> Optional[Staff]:
#     """
#     Verifică autentificarea pentru WebSocket.
#     Token-ul vine ca query parameter.
#     """
#     if not token:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         staff_id = payload.get("sub")
#         if not staff_id:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#         staff_id = int(staff_id)
#
#         # Get staff from DB
#         from sqlalchemy import select
#         result = await db.execute(
#             select(Staff).where(Staff.id == staff_id)
#         )
#         staff = result.scalar_one_or_none()
#
#         if not staff or not staff.is_active:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#         return staff
#
#     except (JWTError, ValueError):
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


# async def get_current_staff_ws(
#         websocket: WebSocket,
#         token: Optional[str] = Query(None),
#         db: AsyncSession = Depends(get_db)
# ) -> Optional[Staff]:
#     """
#     Verifică autentificarea pentru WebSocket.
#     Token-ul vine ca query parameter.
#     """
#     print(f"WS Auth - Token received: {token[:20] if token else 'None'}...")  # Debug
#
#     if not token:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#     try:
#         # Decodează token-ul direct, fără OAuth2PasswordBearer
#         # from jose import jwt
#         # from cfg import SECRET_KEY, ALGORITHM
#
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         staff_id = payload.get("sub")
#         print(f"WS Auth - Staff ID from token: {staff_id}")  # Debug
#
#         if not staff_id:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#         staff_id = int(staff_id)
#
#         # Get staff from DB
#         from sqlalchemy import select
#         from models import Staff
#
#         result = await db.execute(
#             select(Staff).where(Staff.id == staff_id)
#         )
#         staff = result.scalar_one_or_none()
#
#         print(f"WS Auth - Staff found: {staff.email if staff else 'None'}")  # Debug
#
#         if not staff or not staff.is_active:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
#
#         return staff
#
#     except Exception as e:
#         print(f"WS Auth - Error: {type(e).__name__}: {e}")  # Debug
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#         raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)


async def get_current_staff_ws(
        websocket: WebSocket,
        token: Optional[str] = Query(None),
        # NU folosi db: AsyncSession = Depends(get_db) aici!
) -> Optional[Staff]:
    """
    Verifică autentificarea pentru WebSocket.
    """
    print(f"WS Auth - Token received: {token[:20] if token else 'None'}...")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        staff_id = payload.get("sub")
        print(f"WS Auth - Staff ID from token: {staff_id}")

        if not staff_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        staff_id = int(staff_id)

        # Folosește context manager pentru DB
        from cfg import get_db_context

        async with get_db_context() as db:
            result = await db.execute(
                select(Staff).where(Staff.id == staff_id)
            )
            staff = result.scalar_one_or_none()

        print(f"WS Auth - Staff found: {staff.email if staff else 'None'}")

        if not staff or not staff.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

        return staff

    except Exception as e:
        print(f"WS Auth - Error: {type(e).__name__}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)



