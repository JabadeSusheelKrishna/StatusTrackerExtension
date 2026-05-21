from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from app.database import supabase
from app.schemas import (
    TaskCreate, TaskResponse, TaskOtherResponse,
    TaskStatusUpdate, TaskStatusResponse
)
from uuid import UUID

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

# Helper function to check if user exists
def verify_user_exists(email: str):
    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found."
        )
    return res.data[0]

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    # 1. Verify creator exists
    verify_user_exists(task.creator_email)

    try:
        # 2. Insert task into tasks table
        task_data = {
            "creator_email": task.creator_email,
            "title": task.title,
            "type": task.type
        }
        res_task = supabase.table("tasks").insert(task_data).execute()
        if not res_task.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task in database."
            )
        created_task = res_task.data[0]
        task_id = created_task["task_id"]

        # 3. Create initial PENDING status for the creator in task_status table
        status_data = {
            "task_id": task_id,
            "email": task.creator_email,
            "status": "PENDING"
        }
        supabase.table("task_status").insert(status_data).execute()

        # 4. Construct response
        return TaskResponse(
            task_id=UUID(task_id),
            creator_email=created_task["creator_email"],
            title=created_task["title"],
            type=created_task["type"],
            status="PENDING",
            created_at=created_task["created_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("", response_model=List[TaskResponse])
def get_tasks(email: str = Query(..., description="Email of the logged-in user")):
    # 1. Verify user exists
    verify_user_exists(email)

    try:
        # 2. Fetch all PERSONAL tasks created by this user
        personal_res = supabase.table("tasks") \
            .select("*") \
            .eq("type", "PERSONAL") \
            .eq("creator_email", email) \
            .execute()
        
        # 3. Fetch all GLOBAL tasks
        global_res = supabase.table("tasks") \
            .select("*") \
            .eq("type", "GLOBAL") \
            .execute()
        
        # Combine tasks
        all_tasks = (personal_res.data or []) + (global_res.data or [])

        # 4. Fetch all task statuses for this user
        status_res = supabase.table("task_status") \
            .select("*") \
            .eq("email", email) \
            .execute()
        
        status_map = {item["task_id"]: item["status"] for item in (status_res.data or [])}

        # 5. Map statuses to the tasks (default to 'PENDING')
        response_tasks = []
        for t in all_tasks:
            t_status = status_map.get(t["task_id"], "PENDING")
            response_tasks.append(
                TaskResponse(
                    task_id=UUID(t["task_id"]),
                    creator_email=t["creator_email"],
                    title=t["title"],
                    type=t["type"],
                    status=t_status,
                    created_at=t["created_at"]
                )
            )

        # Sort combined tasks by created_at in descending order
        response_tasks.sort(key=lambda x: x.created_at, reverse=True)
        return response_tasks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/others", response_model=List[TaskOtherResponse])
def get_other_tasks(exclude_email: str = Query(..., description="Email to exclude from results")):
    # 1. Verify exclude user exists
    verify_user_exists(exclude_email)

    try:
        # 2. Fetch all users to create a mapping of email -> username
        users_res = supabase.table("users").select("email, username").execute()
        user_map = {u["email"]: u["username"] for u in (users_res.data or [])}

        # 3. Fetch all PERSONAL tasks belonging to other users
        tasks_res = supabase.table("tasks") \
            .select("*") \
            .eq("type", "PERSONAL") \
            .neq("creator_email", exclude_email) \
            .execute()

        # 4. Build response tasks (excluding completion status, mapping creator_username)
        response_tasks = []
        for t in (tasks_res.data or []):
            creator_username = user_map.get(t["creator_email"], "Unknown Friend")
            response_tasks.append(
                TaskOtherResponse(
                    task_id=UUID(t["task_id"]),
                    creator_email=t["creator_email"],
                    creator_username=creator_username,
                    title=t["title"],
                    type=t["type"],
                    created_at=t["created_at"]
                )
            )

        # Sort tasks by created_at in descending order
        response_tasks.sort(key=lambda x: x.created_at, reverse=True)
        return response_tasks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.patch("/{task_id}/status", response_model=TaskStatusResponse)
def update_task_status(task_id: UUID, payload: TaskStatusUpdate):
    # 1. Verify user exists
    verify_user_exists(payload.email)

    try:
        # 2. Fetch task to verify existence and check access rules
        task_res = supabase.table("tasks").select("*").eq("task_id", str(task_id)).execute()
        if not task_res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID '{task_id}' not found."
            )
        task = task_res.data[0]

        # 3. Security check: Users can only update their own personal tasks
        # (Global tasks can be completed by any user)
        if task["type"] == "PERSONAL" and task["creator_email"] != payload.email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to update status for another user's personal task."
            )

        # 4. Upsert the task status for the user
        status_data = {
            "task_id": str(task_id),
            "email": payload.email,
            "status": payload.status
        }
        res_status = supabase.table("task_status").upsert(status_data).execute()
        if not res_status.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task status in database."
            )
        
        updated_status = res_status.data[0]
        return TaskStatusResponse(
            task_id=UUID(updated_status["task_id"]),
            email=updated_status["email"],
            status=updated_status["status"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
