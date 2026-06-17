const BASE = '/api/v1';

let token: string | null = localStorage.getItem('token');

export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem('token', t);
  else localStorage.removeItem('token');
}

export function getToken() {
  return token || localStorage.getItem('token');
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) headers['Authorization'] = `Bearer ${t}`;

  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    setToken(null);
    window.location.hash = '#/login';
    throw new Error('Unauthorized');
  }

  if (path.endsWith('/login')) return res.json();

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }

  if (res.headers.get('content-type')?.includes('application/json')) {
    return res.json();
  }
  return undefined as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; refresh_token: string }>('POST', '/auth/login', { email, password }),

  dashboard: () =>
    request<{ total_employees: number; today_attendance: { total: number; by_status: Record<string, number> } }>('GET', '/dashboard/stats'),

  listEmployees: () =>
    request<{ items: any[]; total: number }>('GET', '/employees?limit=100'),

  createEmployee: (data: any) =>
    request<any>('POST', '/employees', data),

  listShifts: () =>
    request<any[]>('GET', '/shifts'),

  createShift: (data: any) =>
    request<any>('POST', '/shifts', data),

  createAttendance: (data: any) =>
    request<any>('POST', '/attendances', data),

  listAttendances: (params: string = '') =>
    request<{ items: any[]; total: number }>('GET', `/attendances${params}`),

  computeAttendance: (employeeId: string, date: string) =>
    request<any>('POST', `/attendances/compute?employee_id=${employeeId}&att_date=${date}`),

  listDepartments: () =>
    request<any[]>('GET', '/departments'),

  createDepartment: (data: any) =>
    request<any>('POST', '/departments', data),
};
