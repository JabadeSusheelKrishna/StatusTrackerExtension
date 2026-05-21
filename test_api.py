import httpx
import sys
import time

BASE_URL = "http://localhost:8000"

def log_test_header(title: str):
    print("\n" + "=" * 60)
    print(f" TESTING: {title}")
    print("=" * 60)

def main():
    print("Starting Placement Progress Tracker API Integration Tests...")
    
    # 0. Healthcheck
    try:
        res = httpx.get(f"{BASE_URL}/health")
        print(f"Healthcheck: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"Error connecting to server at {BASE_URL}: {e}")
        print("Please ensure the FastAPI server is running.")
        sys.exit(1)

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        
        # 1. Register Users
        log_test_header("1. Registering test users (Susheel and Ananya)")
        
        # Create Susheel
        res = client.post("/api/users", json={
            "email": "susheel@example.com",
            "username": "Susheel"
        })
        print(f"Created Susheel: {res.status_code} - {res.json()}")
        
        # Create Ananya
        res = client.post("/api/users", json={
            "email": "ananya@example.com",
            "username": "Ananya"
        })
        print(f"Created Ananya: {res.status_code} - {res.json()}")

        # 2. Create Tasks
        log_test_header("2. Creating Tasks (Personal & Global)")
        
        # Susheel adds a personal task: "Review OS notes"
        res = client.post("/api/tasks", json={
            "creator_email": "susheel@example.com",
            "title": "Review OS notes",
            "type": "PERSONAL"
        })
        print(f"Susheel Personal Task: {res.status_code} - {res.json()}")
        susheel_task = res.json()
        susheel_task_id = susheel_task["task_id"]

        # Ananya adds a global task: "Solve the weekly LeetCode contest"
        res = client.post("/api/tasks", json={
            "creator_email": "ananya@example.com",
            "title": "Solve the weekly LeetCode contest",
            "type": "GLOBAL"
        })
        print(f"Ananya Global Task: {res.status_code} - {res.json()}")
        global_task = res.json()
        global_task_id = global_task["task_id"]

        # 3. Fetch Personal Dashboard (GET /api/tasks?email=...)
        log_test_header("3. Fetching Dashboard for Susheel")
        res = client.get(f"/api/tasks?email=susheel@example.com")
        print(f"Susheel Dashboard Tasks (Should show 'Review OS notes' and 'Solve weekly LeetCode contest'):")
        for t in res.json():
            print(f" - [{t['type']}] '{t['title']}' | Status: {t['status']} (Created by: {t['creator_email']})")

        log_test_header("3. Fetching Dashboard for Ananya")
        res = client.get(f"/api/tasks?email=ananya@example.com")
        print(f"Ananya Dashboard Tasks (Should only show 'Solve weekly LeetCode contest' and NOT Susheel's personal task):")
        for t in res.json():
            print(f" - [{t['type']}] '{t['title']}' | Status: {t['status']} (Created by: {t['creator_email']})")

        # 4. Update Task Status (PATCH /api/tasks/{task_id}/status)
        log_test_header("4. Updating status of Global Task for Susheel only")
        res = client.patch(f"/api/tasks/{global_task_id}/status", json={
            "email": "susheel@example.com",
            "status": "COMPLETED"
        })
        print(f"Update Status Response: {res.status_code} - {res.json()}")

        # 5. Fetch Dashboard again to verify tracked per-user status
        log_test_header("5. Verifying dashboard status separation (Per-user tracking)")
        
        # Susheel's dashboard
        res = client.get(f"/api/tasks?email=susheel@example.com")
        print("Susheel Dashboard (Global task should show COMPLETED):")
        for t in res.json():
            print(f" - [{t['type']}] '{t['title']}' | Status: {t['status']}")

        # Ananya's dashboard
        res = client.get(f"/api/tasks?email=ananya@example.com")
        print("Ananya Dashboard (Global task should still show PENDING):")
        for t in res.json():
            print(f" - [{t['type']}] '{t['title']}' | Status: {t['status']}")

        # 6. Fetching other friends' tasks (GET /api/tasks/others)
        log_test_header("6. Checking others' tasks on plate")
        
        # Susheel looks at other users' tasks
        res = client.get("/api/tasks/others?exclude_email=susheel@example.com")
        print("Susheel looks at friends' active tasks (Should be empty initially since Ananya has no personal tasks):")
        print(res.json())

        # Ananya creates a personal task: "Practice 3 SQL queries"
        client.post("/api/tasks", json={
            "creator_email": "ananya@example.com",
            "title": "Practice 3 SQL queries",
            "type": "PERSONAL"
        })
        
        # Susheel looks again
        res = client.get("/api/tasks/others?exclude_email=susheel@example.com")
        print("Susheel looks at friends' active tasks again (Should show Ananya's personal task):")
        for t in res.json():
            print(f" - {t['creator_username']} is working on: '{t['title']}' (Created at: {t['created_at']})")

        # 7. Security check
        log_test_header("7. Security checks (Cannot update status of someone else's personal task)")
        res = client.patch(f"/api/tasks/{susheel_task_id}/status", json={
            "email": "ananya@example.com",
            "status": "COMPLETED"
        })
        print(f"Ananya tries to complete Susheel's personal task: {res.status_code} - {res.json()}")

    print("\n" + "=" * 60)
    print(" ALL TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
