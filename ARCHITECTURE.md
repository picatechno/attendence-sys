# Attendance & HR System — Technical Architecture

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐ │
│  │ Web App  │  │ Mobile   │  │ Admin    │  │ ZKTeco MA100    │ │
│  │ (React)  │  │ (PWA)    │  │ Dashboard│  │ (Biometric Dev) │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬────────┘ │
└───────┼──────────────┼──────────────┼─────────────────┼──────────┘
        │              │              │                  │
┌───────▼──────────────▼──────────────▼─────────────────▼──────────┐
│                     API GATEWAY LAYER                             │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │           Nginx / Traefik (SSL Termination, Rate Limit)      │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
└─────────────────────────┼─────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────────┐
│                   APPLICATION LAYER (Backend)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────────┐  │
│  │  REST API   │  │  WebSocket  │  │  ZKTeco PUSH Listener    │  │
│  │  (FastAPI)  │  │  (notify)   │  │  (HTTP /iclock/cdata)    │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬─────────────┘  │
│         │                │                       │               │
│  ┌──────▼────────────────▼───────────────────────▼──────────────┐ │
│  │                    SERVICE LAYER                              │ │
│  │  ┌────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐ │ │
│  │  │Auth    │ │Attendance│ │Employee│ │Leave   │ │Report    │ │ │
│  │  │Service │ │Service   │ │Service │ │Service │ │Service   │ │ │
│  │  └────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────┬─────────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────────┐
│                      DATA LAYER                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │        PostgreSQL (Primary Database)                       │   │
│  │        Redis (Cache, Session, Queue)                       │   │
│  │        MinIO / S3 (Biometric templates, photos)            │   │
│  └────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Tailwind CSS, TanStack Query |
| Backend | Python 3.12+ / FastAPI |
| Database | PostgreSQL 16 |
| Cache/Queue | Redis 7 |
| Object Storage | MinIO (self-hosted S3-compatible) |
| Device Protocol | ZKTeco PUSH Protocol (HTTP-based) |
| Real-time | WebSocket (via FastAPI) |
| Auth | JWT + OAuth2, refresh tokens |
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx |

---

## 2. Database Schema

### 2.1 Entity-Relationship Overview

```
organizations ──┬── departments
                ├── locations
                ├── employees ──┬── attendances
                │               ├── leaves
                │               ├── leave_balances
                │               ├── documents
                │               ├── employee_devices
                │               └── users (auth)
                │
                ├── devices (ZKTeco MA100)
                ├── device_logs (raw PUSH data)
                ├── attendance_policies
                ├── holiday_calendars
                ├── shifts ──┬── shift_assignments
                └── roles ──── user_roles
```

### 2.2 Detailed Table Definitions

```sql
-- ============================================================
-- ORGANIZATION & STRUCTURE
-- ============================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(50) UNIQUE NOT NULL,
    address         TEXT,
    phone           VARCHAR(50),
    email           VARCHAR(255),
    logo_url        TEXT,
    timezone        VARCHAR(50) DEFAULT 'UTC',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE departments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    parent_id       UUID REFERENCES departments(id),
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(50),
    manager_id      UUID,  -- FK to employees, added after employees table
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE locations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    address         TEXT,
    latitude        DECIMAL(10,7),
    longitude       DECIMAL(10,7),
    radius_meters   INTEGER DEFAULT 100,  -- for geofence
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AUTHENTICATION & AUTHORIZATION
-- ============================================================

CREATE TABLE roles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(100) NOT NULL,  -- super_admin, org_admin, hr_manager, dept_head, employee
    description     TEXT,
    permissions     JSONB,  -- { "employee:create": true, "attendance:read": true, ... }
    is_system       BOOLEAN DEFAULT FALSE,  -- cannot delete system roles
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, name)
);

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID UNIQUE REFERENCES employees(id),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    is_locked       BOOLEAN DEFAULT FALSE,
    failed_attempts INTEGER DEFAULT 0,
    last_login_at   TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ DEFAULT NOW(),
    mfa_enabled     BOOLEAN DEFAULT FALSE,
    mfa_secret      VARCHAR(255),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE user_roles (
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_by     UUID REFERENCES users(id),
    assigned_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id)
);

-- ============================================================
-- EMPLOYEES
-- ============================================================

CREATE TABLE employees (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    department_id   UUID REFERENCES departments(id),
    location_id     UUID REFERENCES locations(id),
    employee_code   VARCHAR(50) NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    gender          VARCHAR(10),
    date_of_birth   DATE,
    date_of_joining DATE NOT NULL,
    date_of_exit    DATE,
    employment_type VARCHAR(50) DEFAULT 'full_time',  -- full_time, part_time, contract, intern
    designation     VARCHAR(255),
    grade           VARCHAR(50),
    reporting_to_id UUID REFERENCES employees(id),
    work_email      VARCHAR(255),
    work_phone      VARCHAR(50),
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(50),
    avatar_url      TEXT,
    biometric_ids   JSONB DEFAULT '{}',  -- { "ma100_1": "zk_user_id_1", "ma100_2": "zk_user_id_2" }
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(org_id, employee_code)
);

-- Add FK for dept manager after employees exists
ALTER TABLE departments ADD FOREIGN KEY (manager_id) REFERENCES employees(id);

-- ============================================================
-- DEVICES (ZKTeco MA100)
-- ============================================================

CREATE TABLE devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    location_id     UUID REFERENCES locations(id),
    serial_number   VARCHAR(100) UNIQUE NOT NULL,
    device_name     VARCHAR(255),
    device_model    VARCHAR(100) DEFAULT 'MA100',
    ip_address      INET,
    firmware_version VARCHAR(50),
    push_interval   INTEGER DEFAULT 5,  -- heartbeat interval in seconds
    last_heartbeat  TIMESTAMPTZ,
    last_sync_at    TIMESTAMPTZ,
    timezone        VARCHAR(50) DEFAULT 'UTC',
    status          VARCHAR(20) DEFAULT 'offline',  -- online, offline, error, maintenance
    config          JSONB DEFAULT '{}',  -- device-specific configuration
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE employee_devices (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    device_id       UUID NOT NULL REFERENCES devices(id),
    zk_user_id      VARCHAR(50) NOT NULL,  -- user ID on the ZKTeco device
    fingerprint_template TEXT,  -- base64 encoded, encrypted
    face_template       TEXT,  -- base64 encoded, encrypted
    card_number         VARCHAR(50),
    pin                 VARCHAR(50),
    privilege           VARCHAR(20) DEFAULT 'user',  -- user, admin, super_admin
    enrolled_at         TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(device_id, zk_user_id)
);

-- ============================================================
-- ATTENDANCE
-- ============================================================

CREATE TABLE device_logs (
    id              BIGSERIAL PRIMARY KEY,
    device_id       UUID NOT NULL REFERENCES devices(id),
    zk_user_id      VARCHAR(50) NOT NULL,
    employee_id     UUID REFERENCES employees(id),
    punch_time      TIMESTAMPTZ NOT NULL,
    punch_type      VARCHAR(20),  -- 0=check-in, 1=check-out, 2=break-out, 3=break-in, 4=overtime-in, 5=overtime-out
    verify_mode     INTEGER DEFAULT 0,  -- 0=fingerprint, 1=face, 2=card, 3=pin, 4=etc
    temperature     DECIMAL(4,1),  -- if supported
    raw_data        JSONB,         -- original PUSH payload
    processed       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_device_logs_employee_time (employee_id, punch_time),
    INDEX idx_device_logs_device_time (device_id, punch_time)
);

CREATE TABLE attendances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    date            DATE NOT NULL,
    clock_in        TIMESTAMPTZ,
    clock_out       TIMESTAMPTZ,
    total_work_hours INTERVAL,       -- computed
    total_break_hours INTERVAL,      -- computed
    net_work_hours  INTERVAL,        -- computed
    overtime_hours  INTERVAL,
    status          VARCHAR(30) DEFAULT 'present',
    -- status options: present, absent, late, early_leave, half_day, on_leave, holiday, week_off, missing
    late_minutes    INTEGER DEFAULT 0,
    early_leave_minutes INTEGER DEFAULT 0,
    shift_id        UUID REFERENCES shifts(id),
    clock_in_log_id BIGINT REFERENCES device_logs(id),
    clock_out_log_id BIGINT REFERENCES device_logs(id),
    is_auto_processed BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, date)
);

-- ============================================================
-- SHIFTS & POLICIES
-- ============================================================

CREATE TABLE shifts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    code            VARCHAR(50),
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    grace_late_minutes  INTEGER DEFAULT 15,
    grace_early_minutes INTEGER DEFAULT 15,
    break_start     TIME,
    break_end       TIME,
    min_work_hours  INTERVAL DEFAULT '08:00:00',
    is_night_shift  BOOLEAN DEFAULT FALSE,
    applicable_days INTEGER[] DEFAULT '{1,2,3,4,5,6,7}',  -- 1=Mon..7=Sun
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE shift_assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    shift_id        UUID NOT NULL REFERENCES shifts(id),
    effective_from  DATE NOT NULL,
    effective_to    DATE,
    is_rotation     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(employee_id, effective_from)
);

CREATE TABLE attendance_policies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,
    auto_approve    BOOLEAN DEFAULT FALSE,
    require_geofence BOOLEAN DEFAULT FALSE,
    require_photo   BOOLEAN DEFAULT FALSE,
    overtime_enabled BOOLEAN DEFAULT TRUE,
    overtime_rate   DECIMAL(3,1) DEFAULT 1.5,  -- multiplier
    late_threshold  INTEGER DEFAULT 30,  -- minutes after grace period = late
    absent_threshold INTEGER DEFAULT 240, -- minutes absent after shift start
    max_early_leave INTEGER DEFAULT 30,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- LEAVES
-- ============================================================

CREATE TABLE leave_types (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255) NOT NULL,  -- Annual, Sick, Casual, Maternity, etc.
    code            VARCHAR(50),
    is_paid         BOOLEAN DEFAULT TRUE,
    requires_approval BOOLEAN DEFAULT TRUE,
    max_days_per_request INTEGER DEFAULT 30,
    min_notice_days INTEGER DEFAULT 1,
    carry_forward   BOOLEAN DEFAULT FALSE,
    carry_forward_limit INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    UNIQUE(org_id, code)
);

CREATE TABLE leave_balances (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    leave_type_id   UUID NOT NULL REFERENCES leave_types(id),
    year            INTEGER NOT NULL,
    total_days      DECIMAL(5,1) NOT NULL,
    used_days       DECIMAL(5,1) DEFAULT 0,
    pending_days    DECIMAL(5,1) DEFAULT 0,
    carried_forward DECIMAL(5,1) DEFAULT 0,
    UNIQUE(employee_id, leave_type_id, year)
);

CREATE TABLE leaves (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    leave_type_id   UUID NOT NULL REFERENCES leave_types(id),
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    total_days      DECIMAL(5,1) NOT NULL,
    reason          TEXT,
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, cancelled
    approved_by     UUID REFERENCES employees(id),
    approved_at     TIMESTAMPTZ,
    attachment_url  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- HOLIDAYS
-- ============================================================

CREATE TABLE holiday_calendars (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            VARCHAR(255),
    year            INTEGER NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE holidays (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id     UUID NOT NULL REFERENCES holiday_calendars(id),
    name            VARCHAR(255) NOT NULL,
    date            DATE NOT NULL,
    is_recurring    BOOLEAN DEFAULT FALSE,
    type            VARCHAR(50) DEFAULT 'public',  -- public, company, optional
    UNIQUE(calendar_id, date)
);

-- ============================================================
-- DOCUMENTS
-- ============================================================

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     UUID NOT NULL REFERENCES employees(id),
    doc_type        VARCHAR(100),  -- offer_letter, id_proof, resume, certificate, etc.
    file_name       VARCHAR(255) NOT NULL,
    file_path       TEXT NOT NULL,   -- MinIO/S3 path
    file_size       BIGINT,
    mime_type       VARCHAR(100),
    uploaded_by     UUID REFERENCES users(id),
    is_verified     BOOLEAN DEFAULT FALSE,
    expires_at      DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AUDIT TRAIL
-- ============================================================

CREATE TABLE audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    org_id          UUID REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,  -- create, update, delete, login, export, etc.
    entity_type     VARCHAR(100),           -- employee, attendance, leave, device, etc.
    entity_id       UUID,
    old_values      JSONB,
    new_values      JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. User Roles & Permissions

| Role | Scope | Key Permissions |
|---|---|---|
| **super_admin** | Global | Full system access, cross-org management |
| **org_admin** | Organization | Manage org settings, all modules, device management |
| **hr_manager** | Organization | Employee CRUD, attendance edit, leaves approve, reports |
| **dept_head** | Department | View dept employees, approve dept leaves, view dept reports |
| **employee** | Self | View own attendance, apply leave, view own profile |

### Permission Matrix (JSONB stored in `roles.permissions`)

```json
{
  "employee:create": false,
  "employee:read": true,
  "employee:update": false,
  "employee:delete": false,
  "employee:list": true,
  "attendance:read_own": true,
  "attendance:read_all": false,
  "attendance:manual_edit": false,
  "attendance:export": false,
  "leave:apply": true,
  "leave:approve": false,
  "leave:read_own": true,
  "leave:read_all": false,
  "device:manage": false,
  "device:view_logs": false,
  "report:view": false,
  "report:export": false,
  "organization:manage": false,
  "user:manage": false,
  "audit:view": false
}
```

---

## 4. Main Modules

### Module 1: Authentication & Authorization
- JWT-based token auth (access + refresh tokens)
- OTP / TOTP MFA support
- Role-based access control (RBAC)
- Session management & device tracking
- Password policies (complexity, expiry, history)

### Module 2: Organization Management
- Multi-tenant organization hierarchy
- Department tree (unlimited nesting)
- Location management with geofence support
- Working calendar & holiday management
- Attendance policy configuration

### Module 3: Employee Management
- Full employee lifecycle (onboarding → exit)
- Document management (upload, verify, expiry)
- Reporting hierarchy & org chart
- Biometric enrollment management (map employee to device user IDs)

### Module 4: Device Management (ZKTeco MA100)
- **PUSH Protocol listener** (see Section 7)
- Device registration & pairing via serial number
- Remote command queue (add/delete users, sync time, restart)
- Health monitoring & heartbeat tracking
- Firmware version management

### Module 5: Attendance
- Real-time punch ingestion from device logs
- Shift assignment & rotation
- Auto-computation: work hours, overtime, late, early leave
- Manual attendance correction with audit trail
- Daily attendance summary & monthly aggregation

### Module 6: Leave Management
- Leave type configuration (paid/unpaid, caps, carry-forward)
- Leave application workflow (apply → approve/reject)
- Balance tracking & accrual
- Calendar integration (block leaves on holidays)
- Encashment & forfeiture rules

### Module 7: Reports & Analytics
- Daily/Weekly/Monthly attendance reports
- Late & absenteeism analysis
- Overtime reports
- Department-wise summary
- Export to CSV/Excel/PDF
- Dashboard with KPIs (attendance %, avg hours, late rate)

### Module 8: Audit & Compliance
- Immutable audit log for all critical operations
- Data retention policies
- IP & user-agent tracking
- Export compliance data

---

## 5. API Endpoints

### 5.1 Authentication
```
POST   /api/v1/auth/login              # Login, returns JWT
POST   /api/v1/auth/logout             # Invalidate refresh token
POST   /api/v1/auth/refresh            # Refresh access token
POST   /api/v1/auth/change-password    # Change password
POST   /api/v1/auth/forgot-password    # Send reset email
POST   /api/v1/auth/reset-password     # Reset with token
POST   /api/v1/auth/mfa/enable         # Enable MFA
POST   /api/v1/auth/mfa/verify         # Verify MFA setup
POST   /api/v1/auth/mfa/disable        # Disable MFA
```

### 5.2 Organization
```
GET    /api/v1/org                      # Get current org
PUT    /api/v1/org                      # Update org settings
GET    /api/v1/org/departments          # List departments (tree)
POST   /api/v1/org/departments          # Create department
PUT    /api/v1/org/departments/:id      # Update department
DELETE /api/v1/org/departments/:id      # Delete department
GET    /api/v1/org/locations            # List locations
POST   /api/v1/org/locations            # Create location
PUT    /api/v1/org/locations/:id        # Update location
DELETE /api/v1/org/locations/:id        # Delete location
```

### 5.3 Employees
```
GET    /api/v1/employees                # List (paginated, filterable)
POST   /api/v1/employees                # Create employee + user
GET    /api/v1/employees/:id            # Get employee details
PUT    /api/v1/employees/:id            # Update employee
PATCH  /api/v1/employees/:id/status     # Activate/deactivate
DELETE /api/v1/employees/:id            # Soft delete (set exit date)
GET    /api/v1/employees/:id/documents  # List employee documents
POST   /api/v1/employees/:id/documents  # Upload document
DELETE /api/v1/employees/:id/documents/:docId
GET    /api/v1/employees/:id/leaves     # Employee leave requests
GET    /api/v1/employees/:id/balance    # Leave balance
GET    /api/v1/employees/:id/attendance # Employee attendance records
```

### 5.4 Devices (ZKTeco)
```
GET    /api/v1/devices                  # List devices
POST   /api/v1/devices                  # Register a device
GET    /api/v1/devices/:id              # Device details
PUT    /api/v1/devices/:id              # Update device config
DELETE /api/v1/devices/:id              # Deactivate device
GET    /api/v1/devices/:id/logs         # Raw device logs
POST   /api/v1/devices/:id/sync        # Trigger sync with device
POST   /api/v1/devices/:id/command     # Send remote command
GET    /api/v1/devices/:id/health      # Device health status
```

### 5.5 Attendance
```
GET    /api/v1/attendances              # List (date range, employee, dept)
GET    /api/v1/attendances/:id          # Single attendance record
PUT    /api/v1/attendances/:id          # Manual correction
POST   /api/v1/attendances/reprocess   # Recompute for date range
GET    /api/v1/attendances/summary     # Aggregated summary
GET    /api/v1/device-logs             # Raw device logs (paginated)
```

### 5.6 Shifts
```
GET    /api/v1/shifts                   # List shifts
POST   /api/v1/shifts                   # Create shift
PUT    /api/v1/shifts/:id               # Update shift
DELETE /api/v1/shifts/:id               # Delete shift
GET    /api/v1/shift-assignments        # Current assignments
POST   /api/v1/shift-assignments        # Assign shift to employee
DELETE /api/v1/shift-assignments/:id    # Remove assignment
```

### 5.7 Leaves
```
GET    /api/v1/leaves                   # List leaves (filterable)
POST   /api/v1/leaves                   # Apply for leave
GET    /api/v1/leaves/:id               # Leave detail
PUT    /api/v1/leaves/:id/approve       # Approve leave
PUT    /api/v1/leaves/:id/reject        # Reject leave
DELETE /api/v1/leaves/:id               # Cancel leave
GET    /api/v1/leave-types              # List leave types
POST   /api/v1/leave-types              # Create leave type
PUT    /api/v1/leave-types/:id          # Update leave type
GET    /api/v1/leave-balances           # All balances
GET    /api/v1/leave-balances/:employeeId # Single employee balance
```

### 5.8 Holidays
```
GET    /api/v1/holidays                 # List holidays for year
POST   /api/v1/holidays                 # Add holiday
PUT    /api/v1/holidays/:id             # Update holiday
DELETE /api/v1/holidays/:id             # Remove holiday
```

### 5.9 Reports
```
GET    /api/v1/reports/attendance       # Attendance report (filterable)
GET    /api/v1/reports/absenteeism      # Absenteeism analysis
GET    /api/v1/reports/overtime         # Overtime report
GET    /api/v1/reports/department       # Dept-wise summary
GET    /api/v1/reports/dashboard        # KPI dashboard data
```

### 5.10 Audit
```
GET    /api/v1/audit-logs               # List audit logs (paginated, filterable)
```

### 5.11 ZKTeco PUSH Protocol Endpoints (Unsecured — device-facing)
```
GET    /iclock/cdata                    # Device handshake
POST   /iclock/cdata                    # Receive attendance logs
GET    /iclock/getrequest               # Heartbeat / command poll
GET    /iclock/devicecmd                # Server → Device commands
POST   /iclock/devicecmd                # Device command response
```

---

## 6. Security Rules

### 6.1 Authentication & Session
- **Password requirements**: min 12 chars, upper + lower + digit + special, bcrypt hash (cost 12)
- **JWT access token**: 15-minute expiry, signed with RS256 (asymmetric)
- **JWT refresh token**: 7-day expiry, stored in DB, single-use rotation
- **Failed login lockout**: 5 failures → 15-min lock, 10 failures → require admin unlock
- **MFA**: TOTP (time-based OTP) via authenticator app
- **Session binding**: JWT includes `jti` (token ID), device fingerprint, IP

### 6.2 Authorization (RBAC Enforcement)
- All API endpoints go through middleware that:
  1. Validates JWT
  2. Loads user + roles + permissions
  3. Checks resource ownership (row-level security)
  4. Logs to audit trail for write operations
- **Row-Level Security (RLS)** enforced in service layer:
  - Employees can only read/write their own data
  - Dept heads can read their department
  - HR/Admin can read all within org
  - Super admin can read all across orgs

### 6.3 Data Protection
- **In transit**: TLS 1.3 minimum
- **At rest**: PostgreSQL TDE (Transparent Data Encryption)
- **Secrets**: Stored in environment / Docker secrets, never in code
- **Biometric templates**: AES-256-GCM encrypted before storage in `employee_devices` table
- **PII fields**: `email`, `phone`, `date_of_birth` encrypted at column level with pgcrypto

### 6.4 API Security
- Rate limiting: 100 req/min per IP for auth endpoints, 1000/min for data endpoints
- CORS: Whitelist allowed origins
- Request validation: Pydantic schemas on all endpoints
- SQL injection: ORM parameterized queries only
- No sensitive data in URLs or logs
- Audit log for: all create/update/delete operations, failed auth attempts, data exports

### 6.5 Device Security
- PUSH endpoints (`/iclock/*`) authenticate via device serial number + pre-shared API key
- Device IP whitelist option
- All commands to devices are logged
- Biometric data transmitted over TLS

---

## 7. ZKTeco MA100 Device Integration Strategy

### 7.1 Device Overview

The **ZKTeco MA100** is a biometric attendance terminal supporting:
- Fingerprint verification (optical sensor)
- Face recognition (infrared + visible light)
- RFID card reading
- PIN / password
- Temperature detection (optional)

### 7.2 Communication Protocol: PUSH (ADMS)

The MA100 implements the **ZKTeco PUSH Protocol** (also called ADMS — Attendance Device Management Server). It is a **device-initiated HTTP protocol**:

```
┌────────────────┐          HTTP POST/GET          ┌──────────────────┐
│  ZKTeco MA100  │ ──────────────────────────────── │   Our Server    │
│  (Client)      │ ◄────────────────────────────── │  (FastAPI)      │
└────────────────┘          HTTP 200 OK            └──────────────────┘
```

**Key characteristic**: The MA100 **initiates all connections** — our server is a passive listener.

### 7.3 Protocol Flow

```
STEP 1: INITIAL HANDSHAKE
──────────────────────────
Device → Server:   GET /iclock/cdata?SN=XXXXXXX&options=all
Server → Device:   HTTP 200
                   GET OPTION FROM: XXXXXXX
                   ATTLOGStamp=0
                   OPERLOGStamp=0
                   ATTPHOTOStamp=0
                   Realtime=1
                   ServerVer=3.0.1
                   TransFlag=111111111111

STEP 2: DEVICE CONFIG UPLOAD
──────────────────────────────
Device → Server:   POST /iclock/cdata?table=options
                   (device sends its config as text lines)
Server → Device:   HTTP 200 OK

STEP 3: HEARTBEAT (Continuous)
───────────────────────────────
Device → Server:   GET /iclock/getrequest?SN=XXXXXXX
Server → Device:   (empty response or command)
                   OR commands if queued

STEP 4: ATTENDANCE DATA UPLOAD
───────────────────────────────
Device → Server:   POST /iclock/cdata?table=ATTLOG
                   (attendance records, one per line)
                   Format: <ZKUserID>\t<YYYY-MM-DD HH:MM:SS>\t<verifyMode>\t<workCode>
                   e.g.: 1001  2026-06-17 09:01:33  1  0
Server → Device:   HTTP 200 OK

STEP 5: BIOMETRIC DATA
───────────────────────
Device → Server:   POST /iclock/cdata?table=BIODATA
                   (fingerprint/face templates base64 encoded)
Server → Device:   HTTP 200 OK

STEP 6: ATTENDANCE PHOTOS (if enabled)
────────────────────────────────────────
Device → Server:   POST /iclock/cdata?table=ATTPHOTO
Server → Device:   HTTP 200 OK

STEP 7: SERVER COMMANDS
────────────────────────
(During heartbeat GET /iclock/getrequest)
Server → Device:   <Command>
                   CMD: <COMMAND_NAME>
                   PARAM: <params>

  Common commands:
  ────────────────
  Add user:         CMD: USER PK,KEY=1001\tName=John Doe\tPri=0\tPasswd=1234\tCard=12345678
  Delete user:      CMD: DELETE USER\t1001
  Clear data:       CMD: CLEAR DATA\tATTLOG
  Set time:         CMD: SET TIME\t2026-06-17 14:30:00
  Restart device:   CMD: RESTART
  Get free memory:  CMD: GET FREE MEMORY
```

### 7.4 Server-Side Implementation

```
┌──────────────────────────────────────────────────────────────────┐
│                      ZKTeco PUSH Handler Module                    │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Router: /iclock/*                                  │  │
│  │                                                              │  │
│  │  GET  /iclock/cdata       → handshake_handler()             │  │
│  │  POST /iclock/cdata       → data_receive_handler()          │  │
│  │  GET  /iclock/getrequest  → heartbeat_handler()             │  │
│  │  GET  /iclock/devicecmd   → command_handler()               │  │
│  │  POST /iclock/devicecmd   → command_response_handler()      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Components:                                                │  │
│  │  - DeviceAuthenticator: validates SN + API key              │  │
│  │  - HandshakeManager:   responds with server config          │  │
│  │  - DataParser:         parses ATTLOG, BIODATA, etc.         │  │
│  │  - AttendanceIngestor: writes to device_logs table          │  │
│  │  - CommandQueue:       manages pending device commands      │  │
│  │  - HeartbeatTracker:   updates device last_heartbeat        │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 7.5 Device Registration Flow

```
1. Physical installation of MA100 at site
2. Configure network (IP, gateway, DNS) via device menu
3. Set server URL: http://<our-server>:8080/iclock/cdata
4. Device initiates handshake → server registers it automatically
   (or manual registration via admin dashboard: enter serial number)
5. Map device to location in admin panel
6. Enroll employees on device (fingerprint/face)
7. Server syncs: creates employee_device mapping in DB
```

### 7.6 Employee Biometric Sync Strategy

```
FROM DEVICE → SERVER:
─────────────────────
- During handshake, device uploads all user data (BIODATA table)
- Server stores biometric templates encrypted
- Server maps device user IDs to employee records

FROM SERVER → DEVICE:
─────────────────────
- Admin enrolls employee via admin dashboard
- Server sends `CMD: USER` through command queue
- Next heartbeat, device picks up command and creates user
- Admin can push fingerprint/face templates stored in DB
```

### 7.7 Device Monitoring & Alerts

| Metric | Threshold | Action |
|---|---|---|
| Last heartbeat > 5 min | Warning | Alert admin, mark device offline |
| Last heartbeat > 15 min | Critical | Email + push notification |
| Disk full on device | Warning | Remotely clear old logs |
| Tamper detected | Critical | Alert security |
| Low battery (if UPS) | Warning | Schedule maintenance |

### 7.8 Scalability

- **Single server**: Handles up to ~500 MA100 devices (each pushes ~50 records/min peak)
- **Multiple servers**: Add more PUSH listener instances behind a load balancer (devices are stateless)
- **Redis**: Used as a buffer for incoming attendance logs before batch-insert to PostgreSQL
- **Async processing**: Device logs written to Redis stream → background worker processes and writes to DB

---

## 8. Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Host                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ Nginx    │  │ FastAPI  │  │ FastAPI  │  │ Redis│ │
│  │ (reverse │  │ (API)    │  │ (PUSH    │  │      │ │
│  │  proxy)  │  │          │  │  lstnr)  │  │      │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────┘ │
│  ┌──────────────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Celery Worker  │  │ MinIO   │  │PostgreSQL│    │
│  │ (attendance proc)│  │(storage)│  │          │    │
│  └──────────────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 9. Technology Decisions & Rationale

| Decision | Rationale |
|---|---|
| **FastAPI (Python)** | Native async support for PUSH protocol I/O; Pydantic validation; OpenAPI auto-docs; large ecosystem |
| **PostgreSQL** | JSONB for flexible config; full-text search; mature ORM; excellent concurrent write perf |
| **Redis** | Stream for buffering device logs; cache for sessions; pub/sub for real-time notifications |
| **MinIO** | S3-compatible, self-hosted; stores biometric photos, employee docs, device logs |
| **PUSH (not Pull)** | MA100 native protocol is push-based; no polling overhead; real-time by default |
| **Separate PUSH listener** | Device traffic isolated from user-facing API; can scale independently |
| **Celery** | Async processing of attendance computation (shift matching, overtime calc, report generation) |

---

## 10. Implementation Roadmap

| Phase | Duration | Deliverables |
|---|---|---|
| **Phase 1: Foundation** | Week 1-2 | Project scaffolding, Docker setup, DB schema, Auth module |
| **Phase 2: Core HR** | Week 3-4 | Employee CRUD, Org structure, Document management, RBAC |
| **Phase 3: Device Integration** | Week 5-6 | PUSH listener, Device registration, Attendance ingestion, Heartbeat |
| **Phase 4: Attendance Engine** | Week 7-8 | Shift management, Auto-computation, Manual correction, Daily summary |
| **Phase 5: Leave & Holiday** | Week 9 | Leave types, Balances, Application workflow, Holiday calendar |
| **Phase 6: Reports & Dashboard** | Week 10 | Report engine, Charts, Export, KPI dashboard |
| **Phase 7: Admin & Polish** | Week 11 | Audit log, Email notifications, Admin panel completion |
| **Phase 8: Testing & Deploy** | Week 12 | Integration tests, Load testing, Production deployment |
