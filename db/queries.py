
from datetime import date, datetime
from math import atan2, cos, radians, sin, sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session
from db.schemas import User, Role, Task, Group, Grade, GroupChat, School
from db.engine import engine
from typing import Any

from excel.get_data_from_file import get_data

DEFAULT_SCHOOLS = [
    {"region": "Toshkent", "province": "Toshkent shahri", "name": "Toshkent 1-maktab", "latitude": 41.3111, "longitude": 69.2401},
    {"region": "Toshkent", "province": "Toshkent shahri", "name": "Toshkent 5-maktab", "latitude": 41.3200, "longitude": 69.2550},
    {"region": "Toshkent", "province": "Toshkent viloyati", "name": "Chinoz tumani 1-maktab", "latitude": 41.0720, "longitude": 69.4340},
    {"region": "Samarqand", "province": "Samarqand viloyati", "name": "Samarqand 2-maktab", "latitude": 39.6550, "longitude": 66.9597},
    {"region": "Farg'ona", "province": "Farg'ona viloyati", "name": "Farg'ona 7-maktab", "latitude": 40.3864, "longitude": 71.7846},
    {"region": "Namangan", "province": "Namangan viloyati", "name": "Namangan 3-maktab", "latitude": 41.0003, "longitude": 71.6680},
]


def create_user(chat_id: int, data: dict[str, Any]):
    with Session(engine) as session:
        user = User(
            chat_id=chat_id,
            auto_send=data.get("auto_send", False),
            sms_service=data.get("sms_service", False),
            school_id=data.get("school_id"),
            tables=[],
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def create_role(user_id: int):
    with Session(engine) as session:
        role = Role(role="user", user_id=user_id)
        session.add(role)
        session.commit()
        return role


def get_user(chat_id: int) -> User:
    with Session(engine) as session:
        statement = select(User).where(User.chat_id == chat_id)
        result = session.execute(statement)
        user = result.scalar_one_or_none()
        if user is not None:
            session.refresh(user)
        return user


def get_grades() -> list[Grade]:
    with Session(engine) as session:
        return list(session.scalars(select(Grade).order_by(Grade.grade)))


def get_groups(grade_id: int | None = None) -> list[Group]:
    with Session(engine) as session:
        statement = select(Group).order_by(Group.name)
        if grade_id is not None:
            statement = statement.where(Group.grade == grade_id)
        return list(session.scalars(statement))


def get_group(group_id: int) -> Group | None:
    with Session(engine) as session:
        return session.get(Group, group_id)


def get_schools(region: str | None = None, province: str | None = None) -> list[School]:
    with Session(engine) as session:
        statement = select(School).order_by(School.name)
        if region is not None:
            statement = statement.where(School.region == region)
        if province is not None:
            statement = statement.where(School.province == province)
        return list(session.scalars(statement))


def get_school_by_id(school_id: int) -> School | None:
    with Session(engine) as session:
        return session.get(School, school_id)


def get_school_regions() -> list[str]:
    with Session(engine) as session:
        rows = session.scalars(select(School.region).distinct().order_by(School.region)).all()
        return list(rows)


def get_school_provinces(region: str | None = None) -> list[str]:
    with Session(engine) as session:
        statement = select(School.province).distinct().order_by(School.province)
        if region is not None:
            statement = statement.where(School.region == region)
        rows = session.scalars(statement).all()
        return list(rows)


def find_nearby_schools(latitude: float, longitude: float, radius_km: float = 25.0) -> list[School]:
    with Session(engine) as session:
        schools = list(session.scalars(select(School)))

    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        earth_radius_km = 6371.0
        phi1, phi2 = radians(lat1), radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return earth_radius_km * c

    nearby = []
    for school in schools:
        if school.latitude is None or school.longitude is None:
            continue
        distance = haversine_km(latitude, longitude, float(school.latitude), float(school.longitude))
        if distance <= radius_km:
            nearby.append((distance, school))

    nearby.sort(key=lambda item: item[0])
    return [school for _, school in nearby]


def seed_default_schools() -> list[School]:
    with Session(engine) as session:
        created: list[School] = []
        for item in DEFAULT_SCHOOLS:
            existing = session.scalar(
                select(School).where(
                    School.region == item["region"],
                    School.province == item["province"],
                    School.name == item["name"],
                )
            )
            if existing is not None:
                continue
            school = School(
                region=item["region"],
                province=item["province"],
                name=item["name"],
                latitude=float(item.get("latitude") or 0.0),
                longitude=float(item.get("longitude") or 0.0),
            )
            session.add(school)
            created.append(school)
        session.commit()
        for school in created:
            session.refresh(school)
        return created


def update_user_school(chat_id: int, school_id: int | None) -> None:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.chat_id == chat_id))
        if user is None:
            return
        user.school_id = school_id
        session.commit()


def update_user_tables(chat_id: int, tables: list[int]) -> None:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.chat_id == chat_id))
        if user is None:
            return
        user.tables = tables
        session.commit()


def update_user_setting(chat_id: int, setting: str, value: bool) -> None:
    if setting not in {"auto_send"}:
        raise ValueError(f"Unknown user setting: {setting}")
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.chat_id == chat_id))
        if user is None:
            return
        setattr(user, setting, value)
        session.commit()


def get_user_role(chat_id: int) -> Role:

    with Session(engine) as session:

        user = session.execute(select(User).where(User.chat_id == chat_id)).scalar_one_or_none()

        if user is None:
            return None

        statement = select(Role).where(Role.user_id == user.id)

        result = session.execute(statement)
        role = result.scalar_one_or_none()
        return role



def create_task(file_path:str, file_date:date)->Task:
    with Session(engine) as session:
        task = Task(file_path=file_path, date=file_date, status="pending")
        session.add(task)
        session.commit()
        session.refresh(task)
        return task


def update_task_status(task_id: int, status: str) -> None:
    """Update a task's status: pending/running/completed/failed."""
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is not None:
            task.status = status
            session.commit()


def delete_completed_tasks(now: datetime | None = None) -> int:
    """Delete tasks whose date has passed (completed) and return the count.

    Also removes the associated schedule file from disk.
    """
    import os

    if now is None:
        now = datetime.now()
    removed = 0
    with Session(engine) as session:
        tasks = list(session.scalars(select(Task)))
        for task in tasks:
            if task.date is not None and task.date <= now:
                # Remove the file if it still exists.
                if task.file_path:
                    try:
                        if os.path.exists(task.file_path):
                            os.remove(task.file_path)
                    except OSError:
                        pass
                session.delete(task)
                removed += 1
        session.commit()
    return removed


def get_tasks_due_today(now: datetime | None = None) -> list[Task]:
    """Return tasks whose date falls on the same day as `now` (starting today)."""
    if now is None:
        now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start.replace(day=start.day + 1)
    with Session(engine) as session:
        statement = select(Task).where(Task.date >= start, Task.date < end)
        return list(session.scalars(statement))


def get_active_tasks(now: datetime | None = None) -> list[Task]:
    """Return tasks that are not yet completed (date in the future)."""
    if now is None:
        now = datetime.now()
    with Session(engine) as session:
        statement = select(Task).where(Task.date > now)
        return list(session.scalars(statement))


def get_tasks_due_now(now: datetime | None = None) -> list[Task]:
    """Return tasks whose date has arrived (<= now) but not yet processed.

    These are tasks that should be executed now.
    """
    if now is None:
        now = datetime.now()
    with Session(engine) as session:
        statement = select(Task).where(Task.date <= now)
        return list(session.scalars(statement))


def delete_all_tasks() -> int:
    """Remove all tasks (old ones) and return the count."""
    import os

    removed = 0
    with Session(engine) as session:
        tasks = list(session.scalars(select(Task)))
        for task in tasks:
            if task.file_path:
                try:
                    if os.path.exists(task.file_path):
                        os.remove(task.file_path)
                except OSError:
                    pass
            session.delete(task)
            removed += 1
        session.commit()
    return removed


def get_all_tasks() -> list[Task]:
    """Return all tasks ordered by date."""
    with Session(engine) as session:
        statement = select(Task).order_by(Task.date)
        return list(session.scalars(statement))


def delete_task(task_id: int) -> bool:
    """Delete a single task by id and its associated file. Returns True if deleted."""
    import os

    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            return False
        if task.file_path:
            try:
                if os.path.exists(task.file_path):
                    os.remove(task.file_path)
            except OSError:
                pass
        session.delete(task)
        session.commit()
        return True


def finish_task(task_id: int) -> bool:
    """Manually mark a task as completed (finish it) and delete it.

    The schedule is uploaded to the DB, users are notified, then the task
    and its file are removed. Returns True if the task existed.
    """
    import os

    with Session(engine) as session:
        task = session.get(Task, task_id)
        if task is None:
            return False
        file_path = task.file_path
        # Upload the schedule to the DB.
        if file_path and os.path.exists(file_path):
            upload_table(file_path)
            # Remove the file now that it's used.
            try:
                os.remove(file_path)
            except OSError:
                pass
        session.delete(task)
        session.commit()
        return True



def create_grades(grades: list):
    with Session(engine) as session:
        for grade_value in grades:
            existing_grade = session.execute(
                select(Grade).where(Grade.grade == grade_value)
            ).scalar_one_or_none()

            if not existing_grade:
                session.add(Grade(grade=grade_value))

        session.commit()


def save_groups(tables: list):
    with Session(engine) as session:
        for group in tables:
            grade = session.execute(
                select(Grade).where(Grade.grade == group["grade"])
            ).scalar_one_or_none()
            # Skip classes whose grade is missing (shouldn't happen, but be safe).
            if grade is None:
                continue
            exist_group = session.execute(
                select(Group).where(
                    Group.name == group["name"], Group.grade == grade.id
                )
            ).scalar_one_or_none()
            if not exist_group:
                new_group = Group(
                    name=group["name"], grade=grade.id, table=group["table"]
                )
                session.add(new_group)
            else:
                exist_group.table = group["table"]
                session.add(exist_group)
        session.commit()    

    

def upload_table(file_path: str):
    grades, groups = get_data(file_path)
    create_grades(grades)
    save_groups(groups)


def get_all_users(only_active: bool = False) -> list[User]:
    with Session(engine) as session:
        statement = select(User).order_by(User.id)
        if only_active:
            statement = statement.where(User.auto_send.is_(True))
        return list(session.scalars(statement))


def get_all_admins() -> list[User]:
    with Session(engine) as session:
        statement = (
            select(User)
            .join(Role, Role.user_id == User.id)
            .where(Role.role == "admin")
        )
        return list(session.scalars(statement))


def get_all_guards() -> list[User]:
    with Session(engine) as session:
        statement = (
            select(User)
            .join(Role, Role.user_id == User.id)
            .where(Role.role == "guard")
        )
        return list(session.scalars(statement))


def get_all_school_counselors() -> list[User]:
    with Session(engine) as session:
        statement = (
            select(User)
            .join(Role, Role.user_id == User.id)
            .where(Role.role == "school_counselor")
        )
        return list(session.scalars(statement))


def get_user_by_id(user_id: int) -> User | None:
    with Session(engine) as session:
        return session.get(User, user_id)


def get_admin_by_chat_id(chat_id: int) -> User | None:
    with Session(engine) as session:
        statement = (
            select(User)
            .join(Role, Role.user_id == User.id)
            .where(Role.role == "admin", User.chat_id == chat_id)
        )
        return session.scalar(statement)


def set_user_role(chat_id: int, role_name: str) -> bool:
    with Session(engine) as session:
        user = session.scalar(select(User).where(User.chat_id == chat_id))
        if user is None:
            return False
        role = session.scalar(select(Role).where(Role.user_id == user.id))
        if role is None:
            role = Role(role=role_name, user_id=user.id)
            session.add(role)
        else:
            role.role = role_name
        session.commit()
        return True


def delete_user(user_id: int) -> bool:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            return False
        session.delete(user)
        session.commit()
        return True


# --------------------------
# Group chat bindings
# --------------------------
def get_group_chat(chat_id: int) -> GroupChat | None:
    with Session(engine) as session:
        return session.scalar(select(GroupChat).where(GroupChat.chat_id == chat_id))


def set_group_chat(chat_id: int, group_id: int, title: str | None = None) -> GroupChat:
    with Session(engine) as session:
        gc = session.scalar(select(GroupChat).where(GroupChat.chat_id == chat_id))
        if gc is None:
            gc = GroupChat(chat_id=chat_id, group_id=group_id, title=title)
            session.add(gc)
        else:
            gc.group_id = group_id
            if title:
                gc.title = title
        session.commit()
        session.refresh(gc)
        return gc


def get_all_group_chats() -> list[GroupChat]:
    with Session(engine) as session:
        return list(session.scalars(select(GroupChat)))