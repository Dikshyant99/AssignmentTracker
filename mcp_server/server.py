from datetime import date
from typing import Literal

from mcp.server.fastmcp import FastMCP

from api_client import AssignmentAPI

#The name shown in claude desktop
mcp=FastMCP("AssignmentTracker")

#One API client Used by all tools
api=AssignmentAPI()

#The only allowed status values
Status=Literal["pending","in_progress","done"]


@mcp.tool()
def get_today()-> str:
    """Get today's date (YYYY-MM-DD). Use this to work out what is due soon or overdue."""
    return date.today().isoformat()
@mcp.tool()
def list_assignments(status: Status | None = None) -> list[dict]:
    """List the user's assignments, sorted by due date (soonest first).

    Args:
        status: Optional filter - "pending", "in_progress" or "done". Leave empty to get all.
    """
    params = {"status": status} if status else None
    return api.request("GET", "/assignments", params=params)
@mcp.tool()
def get_assignment(assignment_id: int) -> dict:
    """Get the full details of one assignment by its id."""
    return api.request("GET", f"/assignments/{assignment_id}")

@mcp.tool()
def create_assignment(
    title: str,
    subject: str,
    due_date: date,
    status: Status = "pending",
    notes: str | None = None,
) -> dict:
    """Create a new assignment for the user.

    Args:
        title: Short name of the assignment, e.g. "Database Lab Report".
        subject: The course or subject, e.g. "DBMS".
        due_date: The deadline as YYYY-MM-DD. If the user says something like
            "next Friday", call get_today first and work out the date.
        status: "pending" (default), "in_progress" or "done".
        notes: Optional extra details.
    """
    body = {
        "title": title,
        "subject": subject,
        "due_date": due_date.isoformat(),
        "status": status,
        "notes": notes,
    }
    return api.request("POST", "/assignments", json=body)
@mcp.tool()
def update_assignment(
    assignment_id: int,
    title: str | None = None,
    subject: str | None = None,
    due_date: date | None = None,
    status: Status | None = None,
    notes: str | None = None,
    clear_notes: bool = False,
) -> dict:
    """Update an existing assignment. Only pass the fields that should change.

    For example, to mark assignment 3 as done, pass assignment_id=3 and status="done".
    If you don't know the id, call list_assignments first to find it.
    To remove the notes entirely, pass clear_notes=True (and leave notes empty).
    """
    if clear_notes and notes is not None:
        raise ValueError("Pass either notes or clear_notes=True, not both.")

    changes = {
        "title": title,
        "subject": subject,
        "due_date": due_date.isoformat() if due_date else None,
        "status": status,
        "notes": notes,
    }

# Keep only the fields that were actually given
    changes = {key: value for key, value in changes.items() if value is not None}
    if clear_notes:
        changes["notes"] = None  # explicit null tells the API to clear it

    if not changes:
        raise ValueError("Nothing to update - pass at least one field to change.")

    return api.request("PATCH", f"/assignments/{assignment_id}", json=changes)


@mcp.tool()
def delete_assignment(assignment_id: int) -> str:
    """Permanently delete an assignment. This cannot be undone.

    Always confirm with the user before calling this, and mention the assignment's title.
    """
    api.request("DELETE", f"/assignments/{assignment_id}")
    return f"Assignment {assignment_id} was deleted."


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
