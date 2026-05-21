// Status Tracker Chrome Extension Logic

const BASE_URL = "http://localhost:8000";

// State Management
let currentUserEmail = "";
let currentUsername = "";
let currentTab = "MINE"; // MINE, GLOBAL, FRIENDS

// Wrapper for Dual Storage Compatibility (Chrome Extension Storage vs LocalStorage in Browser Tab)
const storage = {
  get: (key) => {
    return new Promise((resolve) => {
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.get([key], (result) => {
          resolve(result[key] || null);
        });
      } else {
        resolve(localStorage.getItem(key) || null);
      }
    });
  },
  set: (key, value) => {
    return new Promise((resolve) => {
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ [key]: value }, () => {
          resolve();
        });
      } else {
        localStorage.setItem(key, value);
        resolve();
      }
    });
  },
  remove: (key) => {
    return new Promise((resolve) => {
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.remove([key], () => {
          resolve();
        });
      } else {
        localStorage.removeItem(key);
        resolve();
      }
    });
  }
};

// DOM Elements
const onboardingView = document.getElementById("onboarding-view");
const dashboardView = document.getElementById("dashboard-view");
const usernameInput = document.getElementById("username-input");
const emailInput = document.getElementById("email-input");
const accessBtn = document.getElementById("access-btn");
const onboardingLog = document.getElementById("onboarding-log");

const tabMine = document.getElementById("tab-mine");
const tabGlobal = document.getElementById("tab-global");
const tabFriends = document.getElementById("tab-friends");

const creationBox = document.getElementById("creation-box");
const taskInput = document.getElementById("task-input");
const addTaskBtn = document.getElementById("add-task-btn");
const taskList = document.getElementById("task-list");
const statusBar = document.getElementById("status-bar");

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  
  // Check if session is already stored
  currentUserEmail = await storage.get("email");
  currentUsername = await storage.get("username");
  
  if (currentUserEmail && currentUsername) {
    showDashboard();
  } else {
    showOnboarding();
  }
});

// Setup Event Listeners
function setupEventListeners() {
  // Onboarding Event
  accessBtn.addEventListener("click", handleOnboarding);
  
  // Tab Event Listeners
  tabMine.addEventListener("click", () => switchTab("MINE"));
  tabGlobal.addEventListener("click", () => switchTab("GLOBAL"));
  tabFriends.addEventListener("click", () => switchTab("FRIENDS"));
  
  // Task Event Listeners
  addTaskBtn.addEventListener("click", handleAddTask);
  taskInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleAddTask();
  });
}

// Show Onboarding Screen
function showOnboarding() {
  onboardingView.style.display = "flex";
  dashboardView.style.display = "none";
}

// Show Core Dashboard Screen
function showDashboard() {
  onboardingView.style.display = "none";
  dashboardView.style.display = "flex";
  statusBar.textContent = `[SYS]: WELCOME_BACK_${currentUsername.toUpperCase()}`;
  switchTab("MINE");
}

// Handle User Onboarding / Registration
async function handleOnboarding() {
  const username = usernameInput.value.trim();
  const email = emailInput.value.trim();
  
  if (!username || !email) {
    logOnboarding("[ERR]: USERNAME_&_EMAIL_REQUIRED");
    return;
  }
  
  if (!validateEmail(email)) {
    logOnboarding("[ERR]: INVALID_EMAIL_FORMAT");
    return;
  }
  
  logOnboarding("[SYS]: INITIALIZING_REGISTRATION...");
  accessBtn.disabled = true;
  
  try {
    const response = await fetch(`${BASE_URL}/api/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, username })
    });
    
    if (response.status === 201) {
      const user = await response.json();
      await storage.set("email", user.email);
      await storage.set("username", user.username);
      currentUserEmail = user.email;
      currentUsername = user.username;
      
      logOnboarding("[SYS]: REGISTRATION_SUCCESSFUL!");
      setTimeout(() => {
        showDashboard();
        accessBtn.disabled = false;
      }, 1000);
    } else if (response.status === 400) {
      const errData = await response.json();
      // If the email already exists in the backend database, we auto-login!
      if (errData.detail && errData.detail.includes("already exists")) {
        await storage.set("email", email);
        await storage.set("username", username);
        currentUserEmail = email;
        currentUsername = username;
        
        logOnboarding("[SYS]: SESSION_VERIFIED_-_LOGGING_IN...");
        setTimeout(() => {
          showDashboard();
          accessBtn.disabled = false;
        }, 1000);
      } else {
        logOnboarding(`[ERR]: ${errData.detail || "REGISTRATION_FAILED"}`);
        accessBtn.disabled = false;
      }
    } else {
      const errData = await response.json();
      logOnboarding(`[ERR]: ${errData.detail || "SERVER_ERROR"}`);
      accessBtn.disabled = false;
    }
  } catch (error) {
    logOnboarding("[ERR]: CONNECTION_FAILED_-_SERVER_OFFLINE");
    console.error(error);
    accessBtn.disabled = false;
  }
}

// Log message to onboarding terminal area
function logOnboarding(msg) {
  onboardingLog.textContent = msg;
}

// Log message to dashboard status bar
function logStatus(msg) {
  statusBar.textContent = msg;
}

// Switch dashboard tabs
function switchTab(tab) {
  currentTab = tab;
  
  // Toggle button styling classes
  tabMine.classList.remove("active");
  tabGlobal.classList.remove("active");
  tabFriends.classList.remove("active");
  
  if (tab === "MINE") tabMine.classList.add("active");
  if (tab === "GLOBAL") tabGlobal.classList.add("active");
  if (tab === "FRIENDS") tabFriends.classList.add("active");
  
  // Hide creation inputs if we are viewing other friends' tasks, 
  // or keep it visible and default to creating PERSONAL tasks
  if (tab === "FRIENDS") {
    // We keep task creation visible as in the mockup Slide 2, but we can style placeholder differently
    taskInput.placeholder = ">_ ENTER_PERSONAL_TASK_FOR_SELF";
  } else if (tab === "GLOBAL") {
    taskInput.placeholder = ">_ ENTER_GLOBAL_TASK_FOR_GROUP";
  } else {
    taskInput.placeholder = ">_ ENTER_TASK_TITLE";
  }
  
  fetchAndRenderTasks();
}

// Fetch tasks and render lists
async function fetchAndRenderTasks() {
  logStatus("[SYS]: FETCHING_LATEST_TASKS...");
  taskList.innerHTML = "";
  
  try {
    if (currentTab === "MINE" || currentTab === "GLOBAL") {
      const response = await fetch(`${BASE_URL}/api/tasks?email=${encodeURIComponent(currentUserEmail)}`);
      if (!response.ok) throw new Error("Failed to load tasks");
      
      let tasks = await response.json();
      
      // Filter out tasks if on GLOBAL tab
      if (currentTab === "GLOBAL") {
        tasks = tasks.filter(t => t.type === "GLOBAL");
      }
      
      renderTaskList(tasks);
      logStatus(`[SYS]: FETCH_SUCCESS_(${tasks.length}_TASKS_LOADED)`);
    } else if (currentTab === "FRIENDS") {
      const response = await fetch(`${BASE_URL}/api/tasks/others?exclude_email=${encodeURIComponent(currentUserEmail)}`);
      if (!response.ok) throw new Error("Failed to load friends' tasks");
      
      const tasks = await response.json();
      renderFriendsTaskList(tasks);
      logStatus(`[SYS]: FETCH_SUCCESS_(${tasks.length}_FRIENDS_TASKS)`);
    }
  } catch (error) {
    logStatus("[ERR]: CONNECTION_FAILED_-_CHECK_SERVER");
    taskList.innerHTML = `<div class="empty-task-log">[SYS]: LOAD_FAILED<br>PLEASE_CHECK_YOUR_CONNECTION</div>`;
    console.error(error);
  }
}

// Render normal tasks (MINE and GLOBAL tabs)
function renderTaskList(tasks) {
  if (tasks.length === 0) {
    taskList.innerHTML = `<div class="empty-task-log">>_ NO_ACTIVE_TASKS_FOUND</div>`;
    return;
  }
  
  tasks.forEach(task => {
    const isCompleted = task.status === "COMPLETED";
    const taskItem = document.createElement("div");
    taskItem.className = `task-item ${isCompleted ? "completed" : ""}`;
    taskItem.dataset.id = task.task_id;
    
    taskItem.innerHTML = `
      <div class="task-details">
        <div class="task-title">${escapeHTML(task.title)}</div>
        ${task.type === "GLOBAL" ? `<div class="task-creator">[GLOBAL_TASK]</div>` : ""}
      </div>
      <label class="checkbox-container">
        <input type="checkbox" ${isCompleted ? "checked" : ""} />
        <span class="checkmark"></span>
      </label>
    `;
    
    // Add checkbox toggle listener
    const checkbox = taskItem.querySelector('input[type="checkbox"]');
    checkbox.addEventListener("change", () => handleToggleStatus(task.task_id, checkbox));
    
    taskList.appendChild(taskItem);
  });
}

// Render friends' tasks (FRIENDS tab)
function renderFriendsTaskList(tasks) {
  if (tasks.length === 0) {
    taskList.innerHTML = `<div class="empty-task-log">>_ FRIENDS_HAVE_NO_ACTIVE_TASKS</div>`;
    return;
  }
  
  tasks.forEach(task => {
    const taskItem = document.createElement("div");
    taskItem.className = "task-item";
    taskItem.dataset.id = task.task_id;
    
    taskItem.innerHTML = `
      <div class="task-details">
        <div class="task-title">${escapeHTML(task.title)}</div>
        <div class="task-creator">@${escapeHTML(task.creator_username)}</div>
      </div>
    `;
    
    taskList.appendChild(taskItem);
  });
}

// Handle Add Task Submission
async function handleAddTask() {
  const title = taskInput.value.trim();
  if (!title) return;
  
  // Decide type: If in GLOBAL tab, type is GLOBAL, else PERSONAL
  const type = currentTab === "GLOBAL" ? "GLOBAL" : "PERSONAL";
  
  logStatus("[SYS]: CREATING_TASK...");
  addTaskBtn.disabled = true;
  
  try {
    const response = await fetch(`${BASE_URL}/api/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        creator_email: currentUserEmail,
        title: title,
        type: type
      })
    });
    
    if (response.ok) {
      taskInput.value = "";
      logStatus("[SYS]: TASK_ADDED_SUCCESSFULLY");
      await fetchAndRenderTasks();
    } else {
      const err = await response.json();
      logStatus(`[ERR]: ${err.detail || "FAILED_TO_CREATE_TASK"}`);
    }
  } catch (error) {
    logStatus("[ERR]: CONNECTION_FAILED_-_TASK_NOT_SAVED");
    console.error(error);
  } finally {
    addTaskBtn.disabled = false;
  }
}

// Handle Task Status Checkbox Toggle
async function handleToggleStatus(taskId, checkbox) {
  const newStatus = checkbox.checked ? "COMPLETED" : "PENDING";
  const taskCard = checkbox.closest(".task-item");
  
  // Optimistic UI updates
  if (newStatus === "COMPLETED") {
    taskCard.classList.add("completed");
  } else {
    taskCard.classList.remove("completed");
  }
  
  logStatus("[SYS]: UPDATING_STATUS...");
  
  try {
    const response = await fetch(`${BASE_URL}/api/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        email: currentUserEmail,
        status: newStatus
      })
    });
    
    if (response.ok) {
      logStatus("[SYS]: STATUS_SYNCHRONIZED");
    } else {
      const err = await response.json();
      logStatus(`[ERR]: ${err.detail || "SYNC_FAILED"}`);
      // Revert optimistic updates on error
      checkbox.checked = !checkbox.checked;
      taskCard.classList.toggle("completed");
    }
  } catch (error) {
    logStatus("[ERR]: SYNC_FAILED_-_CONNECTION_ERROR");
    console.error(error);
    // Revert optimistic updates on error
    checkbox.checked = !checkbox.checked;
    taskCard.classList.toggle("completed");
  }
}

// Form Validation Helpers
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

// Escape HTML utility for securing content injection
function escapeHTML(str) {
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}
