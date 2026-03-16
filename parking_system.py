"""
Smart Parking Management System
Backend Engine - Python Core Logic
"""

import json
import uuid
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
TOTAL_SLOTS = 20
RATE_PER_HOUR = 40.0          # ₹ per hour
FIRST_HOUR_RATE = 50.0        # ₹ for the first hour
GRACE_PERIOD_MINUTES = 15     # free grace period on exit


# ─────────────────────────────────────────────
#  Data Models (plain dicts for JSON-friendly I/O)
# ─────────────────────────────────────────────
def make_slot(slot_id: int) -> dict:
    return {
        "slot_id": slot_id,
        "slot_label": f"P{slot_id:02d}",
        "status": "available",          # available | occupied
        "vehicle_number": None,
        "entry_time": None,
        "ticket_id": None,
    }


def make_ticket(ticket_id: str, vehicle_number: str,
                slot_id: int, entry_time: str) -> dict:
    return {
        "ticket_id": ticket_id,
        "vehicle_number": vehicle_number.upper().strip(),
        "slot_id": slot_id,
        "slot_label": f"P{slot_id:02d}",
        "entry_time": entry_time,
        "exit_time": None,
        "duration_minutes": None,
        "fee": None,
        "status": "active",             # active | completed
    }


# ─────────────────────────────────────────────
#  Core Parking Manager
# ─────────────────────────────────────────────
class ParkingManager:
    def __init__(self, total_slots: int = TOTAL_SLOTS):
        self.slots: dict[int, dict] = {
            i: make_slot(i) for i in range(1, total_slots + 1)
        }
        self.tickets: dict[str, dict] = {}

    # ── Helpers ──────────────────────────────
    def _nearest_available_slot(self) -> Optional[int]:
        """Return the lowest-numbered free slot (nearest to entrance)."""
        for slot_id in sorted(self.slots):
            if self.slots[slot_id]["status"] == "available":
                return slot_id
        return None

    def _calculate_fee(self, duration_minutes: float) -> float:
        """Tiered fee: first-hour flat rate, then per-hour."""
        if duration_minutes <= GRACE_PERIOD_MINUTES:
            return 0.0
        hours = duration_minutes / 60
        if hours <= 1:
            return FIRST_HOUR_RATE
        extra_hours = hours - 1
        return round(FIRST_HOUR_RATE + extra_hours * RATE_PER_HOUR, 2)

    # ── Public API ───────────────────────────
    def park_vehicle(self, vehicle_number: str,
                     entry_time_str: Optional[str] = None) -> dict:
        """
        Allocate the nearest slot to a vehicle.
        Returns a result dict with success/error and ticket details.
        """
        vehicle_number = vehicle_number.upper().strip()

        # Duplicate check
        for t in self.tickets.values():
            if t["vehicle_number"] == vehicle_number and t["status"] == "active":
                return {"success": False,
                        "error": f"Vehicle {vehicle_number} is already parked.",
                        "ticket": t}

        slot_id = self._nearest_available_slot()
        if slot_id is None:
            return {"success": False,
                    "error": "Parking lot is full. No available slots.",
                    "ticket": None}

        entry_time = entry_time_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ticket_id = str(uuid.uuid4())[:8].upper()
        ticket = make_ticket(ticket_id, vehicle_number, slot_id, entry_time)

        # Update slot
        self.slots[slot_id].update({
            "status": "occupied",
            "vehicle_number": vehicle_number,
            "entry_time": entry_time,
            "ticket_id": ticket_id,
        })
        self.tickets[ticket_id] = ticket

        return {"success": True, "ticket": ticket,
                "message": f"Vehicle parked at slot {ticket['slot_label']}"}

    def release_vehicle(self, vehicle_number: str,
                        exit_time_str: Optional[str] = None) -> dict:
        """
        Process vehicle exit: calculate duration and fee.
        """
        vehicle_number = vehicle_number.upper().strip()

        active_ticket = next(
            (t for t in self.tickets.values()
             if t["vehicle_number"] == vehicle_number and t["status"] == "active"),
            None
        )
        if not active_ticket:
            return {"success": False,
                    "error": f"No active parking record for {vehicle_number}.",
                    "ticket": None}

        exit_time_str = exit_time_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry_dt = datetime.strptime(active_ticket["entry_time"], "%Y-%m-%d %H:%M:%S")
        exit_dt  = datetime.strptime(exit_time_str, "%Y-%m-%d %H:%M:%S")

        if exit_dt < entry_dt:
            return {"success": False,
                    "error": "Exit time cannot be before entry time.",
                    "ticket": None}

        duration_minutes = (exit_dt - entry_dt).total_seconds() / 60
        fee = self._calculate_fee(duration_minutes)

        active_ticket.update({
            "exit_time": exit_time_str,
            "duration_minutes": round(duration_minutes, 2),
            "fee": fee,
            "status": "completed",
        })

        # Free the slot
        slot_id = active_ticket["slot_id"]
        self.slots[slot_id].update({
            "status": "available",
            "vehicle_number": None,
            "entry_time": None,
            "ticket_id": None,
        })

        hours = int(duration_minutes // 60)
        mins  = int(duration_minutes % 60)
        return {
            "success": True,
            "ticket": active_ticket,
            "message": (f"Vehicle {vehicle_number} exited from slot "
                        f"{active_ticket['slot_label']}. "
                        f"Duration: {hours}h {mins}m. Fee: ₹{fee:.2f}")
        }

    def get_slot_status(self) -> list[dict]:
        return list(self.slots.values())

    def get_statistics(self) -> dict:
        total   = len(self.slots)
        occupied = sum(1 for s in self.slots.values() if s["status"] == "occupied")
        available = total - occupied
        completed = [t for t in self.tickets.values() if t["status"] == "completed"]
        revenue = sum(t["fee"] for t in completed if t["fee"] is not None)
        return {
            "total_slots": total,
            "occupied": occupied,
            "available": available,
            "occupancy_pct": round(occupied / total * 100, 1),
            "total_vehicles_served": len(completed),
            "total_revenue": round(revenue, 2),
        }

    def get_active_tickets(self) -> list[dict]:
        return [t for t in self.tickets.values() if t["status"] == "active"]

    def get_all_tickets(self) -> list[dict]:
        return list(self.tickets.values())

    # ── Serialisation ────────────────────────
    def to_json(self) -> str:
        return json.dumps({
            "slots": self.slots,
            "tickets": self.tickets,
        }, indent=2)

    @classmethod
    def from_json(cls, data: str) -> "ParkingManager":
        obj = json.loads(data)
        pm = cls.__new__(cls)
        pm.slots   = {int(k): v for k, v in obj["slots"].items()}
        pm.tickets = obj["tickets"]
        return pm


# ─────────────────────────────────────────────
#  Flask REST API
# ─────────────────────────────────────────────
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS

    app = Flask(__name__)
    CORS(app)
    manager = ParkingManager()

    @app.route("/api/park", methods=["POST"])
    def api_park():
        data = request.get_json() or {}
        vehicle = data.get("vehicle_number", "").strip()
        entry   = data.get("entry_time")
        if not vehicle:
            return jsonify({"success": False, "error": "vehicle_number is required"}), 400
        return jsonify(manager.park_vehicle(vehicle, entry))

    @app.route("/api/exit", methods=["POST"])
    def api_exit():
        data = request.get_json() or {}
        vehicle = data.get("vehicle_number", "").strip()
        exit_t  = data.get("exit_time")
        if not vehicle:
            return jsonify({"success": False, "error": "vehicle_number is required"}), 400
        return jsonify(manager.release_vehicle(vehicle, exit_t))

    @app.route("/api/slots", methods=["GET"])
    def api_slots():
        return jsonify(manager.get_slot_status())

    @app.route("/api/stats", methods=["GET"])
    def api_stats():
        return jsonify(manager.get_statistics())

    @app.route("/api/tickets", methods=["GET"])
    def api_tickets():
        status = request.args.get("status", "all")
        if status == "active":
            return jsonify(manager.get_active_tickets())
        return jsonify(manager.get_all_tickets())

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({"status": "ok"})

except ImportError:
    # Flask not installed – backend logic still usable standalone
    pass


# ─────────────────────────────────────────────
#  CLI Demo
# ─────────────────────────────────────────────
if __name__ == "__main__":
    pm = ParkingManager(total_slots=10)

    print("=" * 55)
    print("   SMART PARKING MANAGEMENT SYSTEM — Demo Run")
    print("=" * 55)

    demos = [
        ("TN38AB1234", "2025-01-15 09:00:00"),
        ("KA01CD5678", "2025-01-15 09:15:00"),
        ("MH12EF9012", "2025-01-15 09:30:00"),
        ("DL07GH3456", "2025-01-15 10:00:00"),
    ]

    print("\n📥  VEHICLE ENTRY")
    for vno, etime in demos:
        r = pm.park_vehicle(vno, etime)
        print(f"  {r['message'] if r['success'] else r['error']}")

    print("\n🚗  SLOT STATUS")
    for s in pm.get_slot_status():
        tag = "🔴 OCCUPIED " if s["status"] == "occupied" else "🟢 AVAILABLE"
        veh = f"  ← {s['vehicle_number']}" if s["vehicle_number"] else ""
        print(f"  [{s['slot_label']}] {tag}{veh}")

    print("\n📤  VEHICLE EXIT")
    exits = [
        ("TN38AB1234", "2025-01-15 11:30:00"),
        ("KA01CD5678", "2025-01-15 13:45:00"),
    ]
    for vno, etime in exits:
        r = pm.release_vehicle(vno, etime)
        print(f"  {r['message'] if r['success'] else r['error']}")

    stats = pm.get_statistics()
    print("\n📊  STATISTICS")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print("=" * 55)
