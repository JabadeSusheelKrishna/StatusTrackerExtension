-- Enable UUID extension if needed
create extension if not exists "uuid-ossp";

-- Users Table
create table if not exists users (
    email text primary key,
    username text not null
);

-- Tasks Table
create table if not exists tasks (
    task_id uuid primary key default gen_random_uuid(),
    creator_email text not null references users(email) on delete cascade,
    title text not null,
    type text not null check (type in ('PERSONAL', 'GLOBAL')),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Task Status Table (Tracks status per user by email)
create table if not exists task_status (
    task_id uuid not null references tasks(task_id) on delete cascade,
    email text not null references users(email) on delete cascade,
    status text not null check (status in ('PENDING', 'COMPLETED')),
    primary key (task_id, email)
);
