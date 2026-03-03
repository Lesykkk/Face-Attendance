"""
Seed script — fills the database with sample data via API.

Usage:
  1. Create admin first:  docker exec -it <container> python scripts/create_admin.py
  2. Run this script:     docker exec -it <container> python scripts/seed_data.py

  Or run locally:         python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from core.database import async_session_factory, engine
from core.security import hash_password, hash_api_key
from models.admin import Admin
from models.building import Building
from models.room import Room
from models.edge_node import EdgeNode
from models.camera import Camera
from models.person import Person, PersonRole
from models.session import Session, SessionMember


# ── Sample Data ──

BUILDINGS = ["А", "Б", "Головний"]

ROOMS = {
    "А": ["101", "102", "201", "202", "214", "301"],
    "Б": ["110", "111", "210", "215"],
    "Головний": ["1", "2", "100", "200", "301"],
}

PERSONS = [
    {"full_name": "Шевченко Олександр Іванович", "person_code": "STU-0001", "role": PersonRole.STUDENT},
    {"full_name": "Коваленко Марія Петрівна", "person_code": "STU-0002", "role": PersonRole.STUDENT},
    {"full_name": "Бондаренко Андрій Сергійович", "person_code": "STU-0003", "role": PersonRole.STUDENT},
    {"full_name": "Ткаченко Юлія Олексіївна", "person_code": "STU-0004", "role": PersonRole.STUDENT},
    {"full_name": "Мельник Дмитро Васильович", "person_code": "STU-0005", "role": PersonRole.STUDENT},
    {"full_name": "Кравченко Анна Миколаївна", "person_code": "STU-0006", "role": PersonRole.STUDENT},
    {"full_name": "Олійник Максим Ігорович", "person_code": "STU-0007", "role": PersonRole.STUDENT},
    {"full_name": "Поліщук Вікторія Романівна", "person_code": "STU-0008", "role": PersonRole.STUDENT},
    {"full_name": "Савченко Артем Олегович", "person_code": "STU-0009", "role": PersonRole.STUDENT},
    {"full_name": "Литвиненко Катерина Андріївна", "person_code": "STU-0010", "role": PersonRole.STUDENT},
    {"full_name": "Іванов Петро Григорович", "person_code": "TCH-0001", "role": PersonRole.TEACHER},
    {"full_name": "Петренко Наталія Вікторівна", "person_code": "TCH-0002", "role": PersonRole.TEACHER},
    {"full_name": "Сидоренко Василь Андрійович", "person_code": "TCH-0003", "role": PersonRole.TEACHER},
]

# Tomorrow's schedule
TOMORROW = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

SESSIONS = [
    {
        "external_id": f"SCH-{TOMORROW.strftime('%Y%m%d')}-001",
        "building": "А",
        "room": "214",
        "subject": "Математичний аналіз",
        "start_hour": 8, "start_min": 30,
        "end_hour": 10, "end_min": 5,
        "student_codes": ["STU-0001", "STU-0002", "STU-0003", "STU-0004", "STU-0005"],
    },
    {
        "external_id": f"SCH-{TOMORROW.strftime('%Y%m%d')}-002",
        "building": "А",
        "room": "201",
        "subject": "Фізика",
        "start_hour": 10, "start_min": 20,
        "end_hour": 11, "end_min": 55,
        "student_codes": ["STU-0001", "STU-0003", "STU-0006", "STU-0007", "STU-0008"],
    },
    {
        "external_id": f"SCH-{TOMORROW.strftime('%Y%m%d')}-003",
        "building": "Б",
        "room": "110",
        "subject": "Програмування",
        "start_hour": 8, "start_min": 30,
        "end_hour": 10, "end_min": 5,
        "student_codes": ["STU-0005", "STU-0006", "STU-0007", "STU-0008", "STU-0009", "STU-0010"],
    },
    {
        "external_id": f"SCH-{TOMORROW.strftime('%Y%m%d')}-004",
        "building": "Головний",
        "room": "200",
        "subject": "Історія України",
        "start_hour": 12, "start_min": 20,
        "end_hour": 13, "end_min": 55,
        "student_codes": ["STU-0002", "STU-0004", "STU-0009", "STU-0010"],
    },
]

EDGE_NODES = {
    "А": {"name": "Edge Node A", "api_key": "test-edge-api-key-A"},
    "Б": {"name": "Edge Node Б", "api_key": "test-edge-api-key-B"},
    "Головний": {"name": "Edge Node Main", "api_key": "test-edge-api-key-Main"},
}

CAMERAS = [
    {"building": "А", "room": "214", "rtsp_url": "rtsp://192.168.1.10/stream1"},
    {"building": "А", "room": "201", "rtsp_url": "rtsp://192.168.1.11/stream1"},
    {"building": "Б", "room": "110", "rtsp_url": "rtsp://192.168.2.10/stream1"},
    {"building": "Головний", "room": "200", "rtsp_url": "rtsp://192.168.3.10/stream1"},
]


async def main():
    async with async_session_factory() as db:
        # ── Buildings ──
        print("Creating buildings...")
        building_map = {}
        for name in BUILDINGS:
            b = Building(name=name)
            db.add(b)
            await db.flush()
            building_map[name] = b
            print(f"  ✓ {name} ({b.id})")

        # ── Rooms ──
        print("\nCreating rooms...")
        room_map = {}
        for building_name, room_names in ROOMS.items():
            for room_name in room_names:
                r = Room(building_id=building_map[building_name].id, name=room_name)
                db.add(r)
                await db.flush()
                room_map[(building_name, room_name)] = r
                print(f"  ✓ {building_name}/{room_name} ({r.id})")

        # ── Persons (without embeddings — no photos in seed) ──
        print("\nCreating persons...")
        person_map = {}
        for p in PERSONS:
            person = Person(full_name=p["full_name"], person_code=p["person_code"], role=p["role"])
            db.add(person)
            await db.flush()
            person_map[p["person_code"]] = person
            print(f"  ✓ {p['full_name']} [{p['person_code']}] ({person.id})")

        # ── Edge Nodes (one per building) ──
        print("\nCreating edge nodes...")
        node_map = {}
        for building_name, node_info in EDGE_NODES.items():
            node = EdgeNode(
                name=node_info["name"],
                api_key_hash=hash_api_key(node_info["api_key"]),
                building_id=building_map[building_name].id,
            )
            db.add(node)
            await db.flush()
            node_map[building_name] = node
            print(f"  ✓ {node.name} → Building {building_name} ({node.id})")
            print(f"    API Key: {node_info['api_key']}")

        # ── Cameras ──
        print("\nCreating cameras...")
        for cam in CAMERAS:
            room = room_map[(cam["building"], cam["room"])]
            node = node_map[cam["building"]]
            camera = Camera(room_id=room.id, edge_node_id=node.id, rtsp_url=cam["rtsp_url"])
            db.add(camera)
            await db.flush()
            print(f"  ✓ {cam['building']}/{cam['room']} → {cam['rtsp_url']} ({camera.id})")

        # ── Sessions ──
        print("\nCreating sessions...")
        for s in SESSIONS:
            room = room_map[(s["building"], s["room"])]
            session = Session(
                external_id=s["external_id"],
                room_id=room.id,
                subject=s["subject"],
                start_time=TOMORROW.replace(hour=s["start_hour"], minute=s["start_min"]),
                end_time=TOMORROW.replace(hour=s["end_hour"], minute=s["end_min"]),
            )
            db.add(session)
            await db.flush()

            for code in s["student_codes"]:
                db.add(SessionMember(session_id=session.id, person_id=person_map[code].id))

            print(f"  ✓ {s['subject']} ({s['building']}/{s['room']}) "
                  f"{s['start_hour']}:{s['start_min']:02d}-{s['end_hour']}:{s['end_min']:02d} "
                  f"[{len(s['student_codes'])} students]")

        await db.commit()

    await engine.dispose()
    print("\n✅ Seed data created successfully!")
    print("\nEdge Node API Keys:")
    for building_name, node_info in EDGE_NODES.items():
        print(f"  {building_name}: {node_info['api_key']}")


if __name__ == "__main__":
    asyncio.run(main())
