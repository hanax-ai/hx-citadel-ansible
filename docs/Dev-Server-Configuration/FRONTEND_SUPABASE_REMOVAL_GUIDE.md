# Frontend: Supabase Removal & Backend Integration Guide

**For**: Frontend AI Assistant  
**Date**: October 12, 2025  
**Task**: Remove Supabase, Connect to FastAPI Backend  
**Scope**: Part of T003 (Frontend Integration)

---

## 📋 Overview

**What You're Doing**: Completely removing Supabase from the frontend and connecting to the new FastAPI backend.

**Why**: We're moving from Supabase (SaaS) to a self-hosted FastAPI backend that consumes events from Redis Streams and provides them to the frontend via REST + SSE.

---

## 🎯 Answers to Your Questions

### Q1: Which Files Should I Update?

**Answer**: Search the ENTIRE codebase for ALL Supabase usage and replace/remove it.

**Search Strategy**:
```bash
# Find all Supabase imports
grep -r "from '@/integrations/supabase" src/
grep -r "import.*supabase" src/

# Find all supabase client usage
grep -r "supabase\." src/
grep -r "\.from(" src/  # Supabase query pattern

# Find Supabase Edge Functions
grep -r "supabase/functions" src/
```

**Expected Files to Update** (based on CodeRabbit review):
1. `src/integrations/supabase/client.ts` - **DELETE THIS FILE**
2. `src/lib/telemetry.ts` - Remove Supabase telemetry
3. `supabase/functions/agents-crawl/index.ts` - **DELETE (replace with backend call)**
4. `supabase/functions/agents-query/index.ts` - **DELETE (replace with backend call)**
5. Any pages that call Supabase:
   - `src/pages/Ingest.tsx` - Replace crawl function
   - `src/pages/Queries.tsx` - Replace query function
   - `src/pages/Admin.tsx` - If it uses Supabase
6. `src/hooks/use-agui-stream.ts` - Update to call backend SSE endpoint
7. `.env` - Remove Supabase vars, add backend vars

**Action**: Replace ALL Supabase usage. Do NOT keep any Supabase code.

---

### Q2: API Endpoints - What Should the Paths Be?

**Answer**: The FastAPI backend will expose these endpoints:

#### REST Endpoints (for actions):

```typescript
// Base URL (will be environment variable)
const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

// POST: Start a web crawl
POST ${API_BASE}/api/v1/crawl
Body: { "url": "https://example.com", "session_id": "uuid" }
Response: { "job_id": "uuid", "status": "accepted" }

// POST: Submit a query
POST ${API_BASE}/api/v1/query
Body: { "query": "What is X?", "session_id": "uuid" }
Response: { "job_id": "uuid", "status": "accepted" }

// GET: Get job status
GET ${API_BASE}/api/v1/jobs/{job_id}
Response: { "job_id": "uuid", "status": "completed", "result": {...} }

// GET: Get session history
GET ${API_BASE}/api/v1/sessions/{session_id}/history
Response: { "session_id": "uuid", "messages": [...] }

// GET: Health check
GET ${API_BASE}/api/health
Response: { "status": "healthy" }
```

#### SSE Endpoint (for real-time events):

```typescript
// SSE: Stream events for a session
GET ${API_BASE}/api/v1/events/stream?session_id={uuid}
Response: Server-Sent Events stream

Event format:
event: job_status
data: {"job_id": "uuid", "status": "processing", "progress": 50}

event: ui_update  
data: {"type": "render", "component": "progress_bar", "props": {...}}

event: job_complete
data: {"job_id": "uuid", "status": "completed", "result": {...}}
```

---

### Q3: Authentication Token - Where Does It Come From?

**Answer**: For the MVP, use **session-based auth** (not JWT tokens).

#### Simple Approach (Recommended for MVP):

**No authentication layer for MVP**. The backend will be on internal network only.

```typescript
// frontend/src/lib/api-client.ts

// Generate or retrieve session ID (stored in localStorage)
function getOrCreateSessionId(): string {
  let sessionId = localStorage.getItem('shield_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('shield_session_id', sessionId);
  }
  return sessionId;
}

// API client (no auth header needed)
export async function apiRequest(endpoint: string, options?: RequestInit) {
  const sessionId = getOrCreateSessionId();
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Session-ID': sessionId,
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }
  
  return response.json();
}
```

#### If You Need RBAC Later (Future Enhancement):

```typescript
// Create an auth context
// frontend/src/contexts/AuthContext.tsx

import { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: string;
  role: 'admin' | 'contributor' | 'viewer';
  name: string;
}

interface AuthContextType {
  user: User | null;
  sessionId: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [sessionId] = useState(() => {
    let id = localStorage.getItem('shield_session_id');
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem('shield_session_id', id);
    }
    return id;
  });

  const login = async (username: string, password: string) => {
    // For MVP: Mock user based on username
    const mockUser: User = {
      id: crypto.randomUUID(),
      role: username === 'admin' ? 'admin' : 'contributor',
      name: username,
    };
    setUser(mockUser);
    localStorage.setItem('shield_user', JSON.stringify(mockUser));
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('shield_user');
  };

  useEffect(() => {
    // Restore user from localStorage
    const stored = localStorage.getItem('shield_user');
    if (stored) {
      setUser(JSON.parse(stored));
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, sessionId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

**For MVP**: Use the simple session ID approach. No auth needed.

---

### Q4: Backend Implementation - Do Endpoints Already Exist?

**Answer**: **NO, the backend does NOT exist yet**.

**What's Happening**:
- **Devin** (another AI agent) is writing the FastAPI backend code (T002)
- **You** are modifying the frontend to call that backend (T003)
- Both tasks happen in parallel
- The backend will be deployed by the HX team after both are done

**What You Should Do**:

1. **Write the frontend code** to call the backend endpoints (listed above)
2. **Mock the backend responses** for local development/testing
3. **Don't worry about the backend not existing** - it will be there when deployed

#### Example: Mock Backend for Local Dev

```typescript
// frontend/src/lib/api-client.ts

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

async function mockCrawl(url: string, sessionId: string) {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return {
    job_id: crypto.randomUUID(),
    status: 'accepted',
    message: `Crawl started for ${url}`,
  };
}

async function mockQuery(query: string, sessionId: string) {
  await new Promise(resolve => setTimeout(resolve, 500));
  
  return {
    job_id: crypto.randomUUID(),
    status: 'accepted',
    message: `Query submitted: ${query}`,
  };
}

// API client with mock support
export async function startCrawl(url: string): Promise<{ job_id: string }> {
  const sessionId = getOrCreateSessionId();
  
  if (USE_MOCK) {
    return mockCrawl(url, sessionId);
  }
  
  return apiRequest('/api/v1/crawl', {
    method: 'POST',
    body: JSON.stringify({ url, session_id: sessionId }),
  });
}

export async function submitQuery(query: string): Promise<{ job_id: string }> {
  const sessionId = getOrCreateSessionId();
  
  if (USE_MOCK) {
    return mockQuery(query, sessionId);
  }
  
  return apiRequest('/api/v1/query', {
    method: 'POST',
    body: JSON.stringify({ query, session_id: sessionId }),
  });
}
```

---

### Q5: Scope - Moving Away from Supabase Entirely?

**Answer**: **YES, completely removing Supabase**.

**Why**:
- Supabase was a prototype/demo tool
- We're moving to self-hosted infrastructure
- Backend will be FastAPI on internal network
- All data stays on-premises (security requirement)

**What to Remove**:
1. ✅ All Supabase imports
2. ✅ `src/integrations/supabase/` directory
3. ✅ `supabase/` directory
4. ✅ Supabase env vars from `.env`
5. ✅ Supabase dependencies from `package.json`

**What to Add**:
1. ✅ Backend API client (`src/lib/api-client.ts`)
2. ✅ SSE event stream handler (`src/lib/sse-client.ts`)
3. ✅ Backend env vars in `.env`
4. ✅ Mock backend for local dev

---

## 🔧 Step-by-Step Implementation

### Step 1: Create Backend API Client

**File**: `src/lib/api-client.ts`

```typescript
// API Configuration
const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

// Session Management
export function getOrCreateSessionId(): string {
  let sessionId = localStorage.getItem('shield_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('shield_session_id', sessionId);
  }
  return sessionId;
}

// Base API Request
export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const sessionId = getOrCreateSessionId();
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-Session-ID': sessionId,
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.message || `API Error: ${response.status}`);
  }
  
  return response.json();
}

// API Methods
export const api = {
  // Crawl
  startCrawl: async (url: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500));
      return { job_id: crypto.randomUUID(), status: 'accepted' };
    }
    return apiRequest('/api/v1/crawl', {
      method: 'POST',
      body: JSON.stringify({ url, session_id: getOrCreateSessionId() }),
    });
  },

  // Query
  submitQuery: async (query: string) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 500));
      return { job_id: crypto.randomUUID(), status: 'accepted' };
    }
    return apiRequest('/api/v1/query', {
      method: 'POST',
      body: JSON.stringify({ query, session_id: getOrCreateSessionId() }),
    });
  },

  // Job Status
  getJobStatus: async (jobId: string) => {
    if (USE_MOCK) {
      return { job_id: jobId, status: 'completed', result: {} };
    }
    return apiRequest(`/api/v1/jobs/${jobId}`);
  },

  // Health
  checkHealth: async () => {
    if (USE_MOCK) {
      return { status: 'healthy' };
    }
    return apiRequest('/api/health');
  },
};
```

---

### Step 2: Create SSE Event Stream Client

**File**: `src/lib/sse-client.ts`

```typescript
export interface SSEEvent {
  event: string;
  data: any;
}

export type SSECallback = (event: SSEEvent) => void;

export class SSEClient {
  private eventSource: EventSource | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(
    private url: string,
    private onEvent: SSECallback,
    private onError?: (error: Event) => void
  ) {}

  connect() {
    if (this.eventSource) {
      this.eventSource.close();
    }

    this.eventSource = new EventSource(this.url);

    this.eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.onEvent({
          event: event.type,
          data,
        });
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };

    // Listen to custom event types
    ['job_status', 'ui_update', 'job_complete', 'error'].forEach(eventType => {
      this.eventSource!.addEventListener(eventType, (event: any) => {
        try {
          const data = JSON.parse(event.data);
          this.onEvent({
            event: eventType,
            data,
          });
        } catch (error) {
          console.error(`Failed to parse ${eventType} event:`, error);
        }
      });
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      this.onError?.(error);
      
      // Attempt reconnect
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => {
          console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
          this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
      }
    };

    this.eventSource.onopen = () => {
      console.log('SSE Connected');
      this.reconnectAttempts = 0;
    };
  }

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
  }
}

// Hook for React components
export function useSSEStream(
  sessionId: string,
  onEvent: SSECallback,
  enabled = true
) {
  const clientRef = useRef<SSEClient | null>(null);

  useEffect(() => {
    if (!enabled || !sessionId) return;

    const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';
    const url = `${API_BASE}/api/v1/events/stream?session_id=${sessionId}`;

    clientRef.current = new SSEClient(url, onEvent);
    clientRef.current.connect();

    return () => {
      clientRef.current?.disconnect();
    };
  }, [sessionId, enabled]);

  return clientRef.current;
}
```

---

### Step 3: Update Hook (Replace Supabase)

**File**: `src/hooks/use-agui-stream.ts`

**OLD (Supabase)**:
```typescript
// Using Supabase Edge Functions
const response = await fetch('https://xxx.supabase.co/functions/v1/agents-query', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${supabaseKey}`,
  },
  body: JSON.stringify({ query }),
});
```

**NEW (Backend API)**:
```typescript
import { api } from '@/lib/api-client';
import { useSSEStream } from '@/lib/sse-client';

export function useAGUIStream() {
  const [events, setEvents] = useState<any[]>([]);
  const sessionId = getOrCreateSessionId();

  // Connect to SSE stream
  useSSEStream(sessionId, (event) => {
    setEvents(prev => [...prev, event]);
  }, true);

  const submitQuery = async (query: string) => {
    const result = await api.submitQuery(query);
    return result;
  };

  const startCrawl = async (url: string) => {
    const result = await api.startCrawl(url);
    return result;
  };

  return {
    events,
    submitQuery,
    startCrawl,
  };
}
```

---

### Step 4: Update Pages

**File**: `src/pages/Ingest.tsx`

**OLD**:
```typescript
import { supabase } from '@/integrations/supabase/client';

const handleCrawl = async () => {
  const { data } = await supabase.functions.invoke('agents-crawl', {
    body: { url },
  });
};
```

**NEW**:
```typescript
import { api } from '@/lib/api-client';

const handleCrawl = async () => {
  try {
    const result = await api.startCrawl(url);
    console.log('Crawl started:', result.job_id);
  } catch (error) {
    console.error('Crawl failed:', error);
  }
};
```

**File**: `src/pages/Queries.tsx` - Same pattern

---

### Step 5: Update Environment Variables

**File**: `.env`

**OLD (Supabase)**:
```bash
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=xxx
```

**NEW (Backend API)**:
```bash
# Backend API
VITE_BACKEND_URL=http://localhost:8001
VITE_USE_MOCK=false

# Session config
VITE_SESSION_STORAGE_KEY=shield_session_id
```

**File**: `.env.example` (create this)
```bash
# Backend API Configuration
VITE_BACKEND_URL=http://localhost:8001
VITE_USE_MOCK=false

# Session Configuration
VITE_SESSION_STORAGE_KEY=shield_session_id
```

---

### Step 6: Update package.json (Remove Supabase)

**Remove**:
```json
"@supabase/supabase-js": "^2.x.x"
```

**Add** (if needed):
```json
"eventsource": "^2.0.2"  // For SSE polyfill if needed
```

---

### Step 7: Delete Supabase Files

```bash
# Delete entire Supabase integration
rm -rf src/integrations/supabase/
rm -rf supabase/

# Delete Supabase env file
rm .env  # Then recreate with backend vars

# Remove from .gitignore if present
# (Keep .env in .gitignore)
```

---

## ✅ Checklist for Completion

```
- [ ] Created src/lib/api-client.ts with all API methods
- [ ] Created src/lib/sse-client.ts with SSE stream handler
- [ ] Updated src/hooks/use-agui-stream.ts (removed Supabase)
- [ ] Updated src/pages/Ingest.tsx (use api.startCrawl)
- [ ] Updated src/pages/Queries.tsx (use api.submitQuery)
- [ ] Updated src/pages/Admin.tsx (if uses Supabase)
- [ ] Deleted src/integrations/supabase/ directory
- [ ] Deleted supabase/ directory
- [ ] Updated .env with backend vars
- [ ] Created .env.example
- [ ] Removed @supabase/supabase-js from package.json
- [ ] Updated all imports (no more Supabase)
- [ ] Added mock backend for local dev
- [ ] Tested with USE_MOCK=true
- [ ] Fixed all 15 CodeRabbit issues
- [ ] All TypeScript/linting errors fixed
```

---

## 🧪 Testing Strategy

### Local Development (Before Backend Exists):
```bash
# Use mocks
VITE_USE_MOCK=true npm run dev
```

### With Backend (After Deployment):
```bash
# Point to real backend
VITE_BACKEND_URL=http://hx-dev-server:8001 npm run dev
```

---

## 📞 Questions?

If you have more questions, ask about:
- Specific API endpoint behavior
- Event data structures
- Error handling patterns
- Mock data structures

**Remember**: The backend doesn't exist yet, so write the frontend to EXPECT it, and use mocks for local dev.

---

**Ready to proceed? Start with Step 1!**

