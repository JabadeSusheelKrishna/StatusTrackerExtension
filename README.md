## 🚀 Placement Progress Tracker - Backend Requirements Specification

This document details the backend requirements for your placement preparation tracker. It helps your group skip WhatsApp management and log progress directly through an API.

---

## 📌 Project Overview

The backend acts as a central storage for tasks and events. It allows friends to create personal goals or assign collective tasks to the group. It also provides transparency by letting users view each other's active tasks.

---

## 🛠️ Core Concepts & Task Classifications

Every item in the system is either a **Task** or an **Event**. They are classified by two main criteria:

### 1. By Scope (Who is it for?)

* **Personal Task:** Created by a user only for themselves.
* *Example:* Susheel adds a task: "Review OS notes." Only Susheel sees this task.


* **Global Task:** Created by any user for everyone in the group.
* *Example:* Kiran adds a task: "Solve the weekly LeetCode contest." This task instantly appears for all users.



### 2. By Status (What is the current state?)

* **To-be-done (Pending):** Tasks that are active and not yet finished.
* **Done (Completed):** Tasks that the user has finished.

> 💡 **Visibility Rule:** You can see what tasks your friends have on their plate. However, you do not track whether they completed them or not. You only track your own completion status.

---

## 💾 Database Schema Design

To support these features, you need two primary tables: **Users** and **Tasks**.

### 🧑‍💻 1. Users Table

Stores information about the group members.

| Field Name | Data Type | Description |
| --- | --- | --- |
| `user_id` | String / UUID | Unique identifier for each user. |
| `username` | String | Name of the friend (e.g., "Ananya"). |
| `email` | String | Email address for login identification. |

### 📝 2. Tasks Table

Stores both personal and global tasks.

| Field Name | Data Type | Description |
| --- | --- | --- |
| `task_id` | String / UUID | Unique identifier for the task. |
| `creator_id` | String / UUID | The user who created the task. |
| `title` | String | Brief title (e.g., "Practice 3 SQL queries"). |
| `type` | String | Value is either `PERSONAL` or `GLOBAL`. |
| `status` | String | Value is either `PENDING` or `COMPLETED` (Tracked per user). |
| `created_at` | Timestamp | Time when the task was made. |

---

## 🌐 API Endpoints Breakdown

Your frontend (App, Web, or Chrome Extension) will interact with the backend using these REST endpoints:

### 📥 1. Task Creation

* **`POST /api/tasks`**
* **Purpose:** Allows a user to add a new task.
* **Payload Example:**
```json
{
  "creator_id": "user_123",
  "title": "Study System Design Trie Architecture",
  "type": "GLOBAL" 
}

```





### 📤 2. Fetching Tasks

* **`GET /api/tasks?user_id=user_123`**
* **Purpose:** Retrieves the personalized dashboard for the logged-in user.
* **Response:** Returns all personal tasks for `user_123` and all global tasks.


* **`GET /api/tasks/others?exclude_user_id=user_123`**
* **Purpose:** Retrieves the task lists of all other friends to see what they are working on.
* **Response:** Returns a list of tasks belonging to other users (ignoring completion status).



### 🔄 3. Updating Status

* **`PATCH /api/tasks/{task_id}/status`**
* **Purpose:** Marks a task as Done or moves it back to To-be-done.
* **Payload Example:**



```json
        {
          "user_id": "user_123",
          "status": "COMPLETED"
        }
        ```

---

## 🎯 Next Steps for Implementation

1. Choose your backend framework (like Node.js Express, Python FastAPI, or Go).
2. Set up a simple database (like PostgreSQL, MySQL, or MongoDB).
3. Build and test these endpoints using an API client like Postman before coding your frontend.

```