
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from db.schemas import User, Role, Task, Group, Grade, GroupChat
from db.engine import engine
from typing import Any

from excel.get_data_from_file import get_data


def create_user(chat_id: int, data: dict[str, Any]):
    with Session(engine) as session:
        user = User(
            name=data["name"],
            chat_id=chat_id,
            phone_number=data["phone_number"],
            auto_send=data["auto_send"],
            sms_service=data.get("sms_service", False),
            tables=[],
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def create_role(user_id: int, role_name: str = "user"):
    with Session(engine) as session:
        role = Role(role=role_name, user_id=user_id)
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


def ensure_admin(chat_id: int) -> bool:
    """Promote an existing user to admin. Returns True if the user exists."""
    return set_user_role(chat_id, "admin")


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