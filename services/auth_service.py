"""Authentication, session gates, and user management (FR-1, PRD §3)."""

from __future__ import annotations

import sqlite3

import bcrypt

from db import database


def _row_to_user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "is_active": bool(row["is_active"]),
        "must_change_pw": bool(row["must_change_pw"]),
    }


def authenticate(username: str, password: str) -> dict | None:
    """Return the user dict on success, None on bad credentials/inactive user."""
    conn = database.get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),)
        ).fetchone()
        if row is None or not row["is_active"]:
            return None
        if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            return None
        return _row_to_user(row)
    finally:
        conn.close()


def change_password(user_id: int, new_password: str) -> None:
    """Set a new password chosen by the user; clears the forced-change flag."""
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, must_change_pw = 0 WHERE id = ?",
                (database.hash_password(new_password), user_id),
            )
    finally:
        conn.close()


def create_user(username: str, full_name: str, password: str, role: str = "employee") -> int:
    """Owner adds a new account (FR-1.3). Raises ValueError on duplicate username."""
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, full_name, role, must_change_pw)"
                " VALUES (?, ?, ?, ?, 1)",
                (username.strip(), database.hash_password(password), full_name.strip(), role),
            )
        return cur.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Username '{username}' already exists.") from exc
    finally:
        conn.close()


def set_active(user_id: int, active: bool) -> None:
    """Deactivate/reactivate an account (FR-1.4). History stays intact."""
    conn = database.get_connection()
    try:
        with conn:
            conn.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if active else 0, user_id))
    finally:
        conn.close()


def reset_password(user_id: int, new_password: str) -> None:
    """Owner resets a password; the user must change it at next login (FR-1.5)."""
    conn = database.get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, must_change_pw = 1 WHERE id = ?",
                (database.hash_password(new_password), user_id),
            )
    finally:
        conn.close()


def list_users() -> list[dict]:
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, full_name, role, is_active, must_change_pw, created_at"
            " FROM users ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _user_transaction_count(conn: sqlite3.Connection, user_id: int) -> int:
    """How many purchase/sale/adjustment rows reference this user (audit trail)."""
    return conn.execute(
        "SELECT (SELECT COUNT(*) FROM purchases WHERE created_by = ? OR cancelled_by = ?)"
        "      + (SELECT COUNT(*) FROM sales WHERE created_by = ? OR cancelled_by = ?)"
        "      + (SELECT COUNT(*) FROM stock_adjustments WHERE created_by = ?)",
        (user_id, user_id, user_id, user_id, user_id),
    ).fetchone()[0]


def delete_block_reason(user_id: int, acting_user_id: int) -> str | None:
    """Return a human-readable reason if the user cannot be deleted, else None."""
    if user_id == acting_user_id:
        return "You cannot delete your own account while logged in."
    conn = database.get_connection()
    try:
        row = conn.execute("SELECT id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return "User not found."
        if row["role"] == "owner":
            owners = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'owner'"
            ).fetchone()[0]
            if owners <= 1:
                return "Cannot delete the only Owner account in the system."
        if _user_transaction_count(conn, user_id) > 0:
            return (
                "This user has purchase, sale, or stock-adjustment records. "
                "Deactivate the account instead — their history must stay intact (FR-1.4)."
            )
        return None
    finally:
        conn.close()


def delete_user(user_id: int, acting_user_id: int) -> None:
    """Permanently remove a user with no transaction history (owner only)."""
    reason = delete_block_reason(user_id, acting_user_id)
    if reason:
        raise ValueError(reason)
    conn = database.get_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            if cur.rowcount == 0:
                raise ValueError("User not found.")
    finally:
        conn.close()


# --- Streamlit session gates (imported lazily so services stay testable) ---

def current_user() -> dict | None:
    import streamlit as st

    return st.session_state.get("user")


def require_login() -> dict:
    """Stop page execution unless a user is logged in. Returns the user."""
    import streamlit as st

    user = st.session_state.get("user")
    if user is None:
        st.warning("Please log in first.")
        st.stop()
    return user


def require_owner() -> dict:
    """Stop page execution unless the logged-in user is the owner."""
    import streamlit as st

    user = require_login()
    if user["role"] != "owner":
        st.error("This page is available to the Owner only.")
        st.stop()
    return user


def logout() -> None:
    import streamlit as st

    st.session_state.pop("user", None)
