# CPU Analysis - Terminal System Monitor

a modern, terminal-based system monitor built with python and textual. monitor cpu, memory, processes, and network stats in real-time with a clean tui interface.

## Features

- **user authentication** - login system with role-based permissions (admin/user)
- **user registration** - admins can register new users from login screen
- **password management** - change your password anytime with `x` key
- **cpu monitoring** - real-time cpu usage with sparklines, per-core analysis, and frequency stats
- **memory tracking** - visual memory usage with bar graphs for ram and swap
- **process management** - searchable, sortable process list with real-time updates
- **process control** - kill processes (admin only)
- **network stats** - monitor network i/o and interface stats in real-time
- **async updates** - all panels update concurrently every few seconds

## Requirements

- python >= 3.12
- uv (recommended) or pip

## Installation

### using uv (recommended)

```bash
# clone the repo
git clone https://github.com/rev-975/cpu_anal
cd cpu_analysis

# uv will automatically create venv and install dependencies
uv sync
```

### using pip

```bash
# clone the repo
git clone https://github.com/rev-975/cpu_anal
cd cpu_analysis

# create virtual environment
python -m venv .venv
source .venv/bin/activate  # on windows: .venv\Scripts\activate

# install dependencies
pip install -e .
```

## Running

### with uv

```bash
uv run cpu-anal
```

### with pip/venv

```bash
# make sure venv is activated
source .venv/bin/activate  # on windows: .venv\Scripts\activate

# run the app
cpu-anal
```

## Default Login

on first run, a default admin account is created:

- **username:** admin
- **password:** admin

**important:** change this password after first login using the `x` key!

## Usage

### keyboard shortcuts

#### general
- `q` - quit application
- `x` - change password
- `u` - manage users (requires permission)
- `esc` - close dialogs/clear search

#### process panel
- `↑/↓` - navigate process list
- `c` - sort by cpu usage
- `m` - sort by memory usage
- `p` - sort by pid
- `/` - search processes by name
- `k` - kill selected process (admin only)

#### login screen
- `tab` - switch between fields
- `enter` - login
- click "register new user" - create new users (requires admin credentials)

## user management

### registering new users

only admins can register new users:

1. on the login screen, enter admin credentials
2. click "register new user" button
3. fill in new user details (username, password, admin checkbox)
4. click "register"
5. new user can now login

### changing password

any user can change their password:

1. login to the application
2. press `x` key
3. enter current password
4. enter and confirm new password
5. click "change password"

## permissions

the application now supports granular permissions! each user can be assigned specific permissions:

### available permissions:
- **view cpu** - access to cpu monitoring panel
- **view memory** - access to memory panel
- **view processes** - access to process list
- **view network** - access to network stats panel
- **kill processes** - ability to terminate processes (shown as `[k]kill` in UI)
- **manage users** - ability to create users and edit permissions (shown as `[u]users` in UI)
- **admin** - admin status (gives all permissions by default)

### managing permissions:
1. users with `manage users` permission can press `u` to open user management
2. use arrow keys or mouse to navigate (scroll down to see all permissions)
3. select a user from the list
4. toggle permissions using checkboxes
5. click "save changes" to apply
6. press `esc` or `q` or click "close" to exit user management

### default permissions:
- **admin user** - all permissions enabled (cannot be disabled)
- **new regular users** - can view cpu, processes, and network (memory viewing disabled by default)

### important notes:
- users with `admin` status always have all permissions enabled (this cannot be changed)
- users with `manage users` permission cannot remove their own user management access
- if you check the `admin` checkbox, all other permissions are automatically enabled

## troubleshooting

### permission denied when killing processes

some processes require root/admin privileges to kill. run with:

```bash
sudo uv run cpu-anal  # linux/mac
# or
# run terminal as administrator on windows
```

### module not found errors

make sure you've installed the package:

```bash
uv sync  # or pip install -e .
```

### database locked errors

only one instance can run at a time. close other instances or delete `cpu_anal.db` to reset.

## security

- all passwords are hashed using bcrypt
- database file (`cpu_anal.db`) is excluded from git to protect credentials
- each installation maintains its own local user database
