# YB Task Management System

A comprehensive task management software designed for accounting companies, featuring audit logs, permissions, client management, and user authentication.

## Features

### Core Functionality
- **Task Management**: Create, assign, update, and track tasks with subtasks
- **Client Management**: Manage clients, contacts, accounts, and client groups
- **Document Management**: Upload, organize, and manage client documents with automatic purge policies
- **Recurring Tasks**: Set up recurring tasks with flexible scheduling options
- **User Authentication**: Secure login/logout with session management
- **Role-Based Permissions**: Granular permission system with role management
- **Audit Logging**: Comprehensive audit trail of all system activities

### Security Features
- JWT-based authentication
- Session tracking with inactivity timeout
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Comprehensive audit logging

### Permissions
- `manage_users`: Can manage users
- `manage_roles`: Can manage roles
- `manage_permissions`: Can manage permissions
- `manage_tasks`: Can manage all tasks
- `manage_clients`: Can manage clients
- `view_audit_logs`: Can view audit logs
- `manage_documents`: Can manage documents
- `view_reports`: Can view reports

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **SQLite**: Database (can be configured for PostgreSQL)
- **Alembic**: Database migrations
- **JWT**: Authentication tokens
- **bcrypt**: Password hashing

### Frontend
- **Next.js 14**: React framework
- **Tailwind CSS**: Styling
- **React**: UI library

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Create virtual environment** (if not already created):
   ```bash
   python -m venv venv
   ```

2. **Activate virtual environment**:
   ```bash
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   
   # Windows Git Bash / Linux / macOS
   source venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirement.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**:
   ```bash
   # Using venv Python directly (Recommended)
   venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or activate venv first
   uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
   ```

   Backend will be available at: http://localhost:8000

### Frontend Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Set up environment variables**:
   Create a `.env.local` file:
   ```bash
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   Frontend will be available at: http://localhost:3000

## Default Admin Credentials

On first startup, the system creates an admin user:
- **Email**: `kruz@yecnybooks.com`
- **Password**: `YecnyBKruz2025`

**⚠️ IMPORTANT**: Change these credentials in production!

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
YB-Task-Management/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI application
│       ├── models.py            # SQLAlchemy models
│       ├── auth.py              # Authentication routes
│       ├── crud.py              # CRUD operations
│       ├── crud_utils/          # Specialized CRUD utilities
│       │   ├── audit.py         # Audit logging
│       │   ├── documents.py    # Document management
│       │   └── tasks.py        # Task operations
│       ├── routers/             # API route handlers
│       │   ├── audit.py        # Audit log endpoints
│       │   ├── clients_router.py
│       │   ├── tasks_router.py
│       │   ├── users_router.py
│       │   └── ...
│       ├── schemas/             # Pydantic schemas
│       ├── services/            # Business logic
│       └── utils/               # Utility functions
│           ├── security.py     # Auth utilities
│           └── permissions.py   # Permission checking
├── app/                         # Next.js frontend
│   ├── (protected)/             # Protected routes
│   │   ├── dashboard/
│   │   ├── clients/
│   │   ├── audit/
│   │   └── ...
│   └── (auth)/                 # Auth routes
│       └── login/
├── alembic/                     # Database migrations
└── documents/                  # Document storage
```

## Key Features Explained

### Audit Logging
All significant actions are logged:
- User login/logout
- Task creation, updates, completion, deletion
- Client creation, updates, deletion
- User management operations
- Permission/role changes
- Document uploads

Audit logs can be filtered by:
- Entity type (task, client, user, etc.)
- Action name
- User who performed the action
- Date range

### Permissions System
- **Roles**: Groups of permissions (e.g., "Admin", "Manager", "Staff")
- **Permissions**: Granular actions (e.g., "manage_users", "view_audit_logs")
- **Role-Permission Mapping**: Assign permissions to roles
- **User-Role Assignment**: Assign roles to users

### Client Management
- Create and manage clients
- Add contacts to clients
- Manage client accounts
- Organize clients into groups
- Track client status (active, inactive, left)

### Task Management
- Create tasks with due dates
- Assign tasks to users
- Create subtasks
- Mark tasks as billable
- Set up recurring tasks
- Filter and search tasks
- Kanban board view

### Document Management
- Upload documents for clients
- Organize by client, account, month, year
- Automatic purge policies (6 months after client leaves)
- Two-approval system for document purges

## Development

### Running Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Adding New Permissions
1. Add permission to `DEFAULT_PERMISSIONS` in `backend/app/startup.py`
2. Run the application (permissions are auto-created)
3. Assign permissions to roles via the admin interface

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Change default admin credentials
- [ ] Set `COOKIE_SECURE=true` for HTTPS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up proper backup strategy
- [ ] Configure CORS properly
- [ ] Set up SSL/TLS certificates
- [ ] Review and restrict permissions

### Environment Variables
See `.env.example` for all available configuration options.

## Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change port with `--port 8001`
- **Migration errors**: Ensure `alembic.ini` is in project root
- **Import errors**: Activate virtual environment

### Frontend Issues
- **API connection errors**: Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- **CORS errors**: Verify CORS settings in `backend/app/main.py`

## License

Copyright © 2025 YB Bookkeeping

## Support

For issues and questions, please contact the development team.
