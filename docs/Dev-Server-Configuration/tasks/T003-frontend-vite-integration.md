# Task T003: Integrate Existing Vite Frontend

**Feature**: Shield AG-UI Frontend Integration  
**Phase**: 3.3 Core Implementation  
**Parallel**: [P] (can run parallel with T002 backend)  
**Estimated Effort**: 2 hours (reduced - leverages existing code)  
**Prerequisites**: T001 (Ansible role structure)

## Task Description

Integrate the existing Vite + React frontend application (6,500 LOC) from the citadel-shield-ui repository. The codebase is 90% feature-complete with all 9 pages implemented (Dashboard, Jobs, Ingest, Graph, Queries, Audit, Admin) using shadcn-ui + Radix UI components. This task involves cloning the repository, removing Supabase dependencies, and connecting to the new FastAPI backend API.

## Execution Flow

```
1. Clone existing frontend repository
   → git clone https://github.com/hanax-ai/citadel-shield-ui.git
   → git checkout feature-1
   → Copy to roles/ag_ui_deployment/files/frontend/
2. Remove Supabase dependencies
   → Delete src/integrations/supabase/
   → Remove @supabase/supabase-js from package.json
   → Remove Supabase Edge Functions
3. Create backend API client
   → Create src/lib/api-client.ts
   → Add fetch wrappers for backend endpoints
   → Add authentication token handling
4. Update existing pages to use backend API
   → Replace Supabase calls with fetch to /api/*
   → Update event streaming to use /events/stream
   → Maintain existing UI/UX
5. Fix CodeRabbit findings (15 issues)
   → Security: Remove .env from version control
   → Quality: Fix AsyncButton, add timeouts, etc.
6. Create production Dockerfile (multi-stage Vite build)
7. Configure environment variables (.env.production)
8. Verify build works (npm run build)
```

## Files to Create

### 1. Directory Structure
```
roles/ag_ui_deployment/files/frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx
│   ├── login/
│   │   └── page.tsx
│   ├── dashboard/
│   │   └── page.tsx
│   ├── jobs/
│   │   └── page.tsx
│   ├── graph/
│   │   └── page.tsx
│   └── admin/
│       └── page.tsx
├── components/
│   ├── AgentChat.tsx
│   ├── EventTimeline.tsx
│   ├── KnowledgeGraphViz.tsx
│   ├── JobTracker.tsx
│   ├── ToolForms.tsx
│   ├── KGCuration.tsx
│   ├── ui/
│   │   ├── button.tsx
│   │   ├── input.tsx
│   │   ├── modal.tsx
│   │   └── toast.tsx
│   └── layout/
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
├── lib/
│   ├── api.ts
│   ├── auth.ts
│   ├── sse.ts
│   └── store.ts
├── public/
│   └── favicon.ico
├── styles/
│   └── globals.css
├── types/
│   └── index.ts
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
├── Dockerfile
└── README.md
```

### 2. app/layout.tsx

```typescript
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from '@/components/Providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Shield AG-UI | Power User Interface',
  description: 'Advanced interface for HX-Citadel Shield RAG pipeline',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
```

### 3. app/dashboard/page.tsx

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useAgentChat } from '@ag-ui/react'
import AgentChat from '@/components/AgentChat'
import EventTimeline from '@/components/EventTimeline'
import KnowledgeGraphViz from '@/components/KnowledgeGraphViz'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  const { messages, sendMessage, isConnected } = useAgentChat({
    apiUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002',
    autoConnect: true,
  })

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <div className="flex-1 flex flex-col">
        <Header />
        
        <main className="flex-1 overflow-hidden p-6">
          <div className="grid grid-cols-12 gap-6 h-full">
            {/* Chat Interface - Left Column */}
            <div className="col-span-4 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <AgentChat
                messages={messages}
                onSendMessage={sendMessage}
                isConnected={isConnected}
              />
            </div>
            
            {/* Event Timeline - Middle Column */}
            <div className="col-span-3 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <EventTimeline />
            </div>
            
            {/* Knowledge Graph - Right Column */}
            <div className="col-span-5 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <KnowledgeGraphViz />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
```

### 4. components/AgentChat.tsx

```typescript
'use client'

import { useState, useRef, useEffect } from 'react'
import { Message } from '@ag-ui/core'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Send, Loader2 } from 'lucide-react'

interface AgentChatProps {
  messages: Message[]
  onSendMessage: (content: string) => void
  isConnected: boolean
}

export default function AgentChat({ messages, onSendMessage, isConnected }: AgentChatProps) {
  const [input, setInput] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !isConnected) return

    setIsSubmitting(true)
    try {
      await onSendMessage(input.trim())
      setInput('')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Agent Chat</h2>
          <div className="flex items-center gap-2">
            <div className={`h-2 w-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.content}</p>
              {message.timestamp && (
                <span className="text-xs opacity-70 mt-1 block">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 border-t border-gray-200">
        <div className="flex gap-2">
          <Input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={!isConnected || isSubmitting}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!isConnected || isSubmitting || !input.trim()}
            size="sm"
          >
            {isSubmitting ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
```

### 5. components/KnowledgeGraphViz.tsx

```typescript
'use client'

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import { Button } from './ui/button'

interface Node {
  id: string
  name: string
  type: string
  confidence: number
}

interface Link {
  source: string
  target: string
  type: string
  confidence: number
}

interface GraphData {
  nodes: Node[]
  links: Link[]
}

export default function KnowledgeGraphViz() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [data, setData] = useState<GraphData>({ nodes: [], links: [] })
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  useEffect(() => {
    if (!svgRef.current || data.nodes.length === 0) return

    const svg = d3.select(svgRef.current)
    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Clear previous
    svg.selectAll('*').remove()

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Create container for graph
    const g = svg.append('g')

    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes as any)
      .force('link', d3.forceLink(data.links)
        .id((d: any) => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30))

    // Create links
    const link = g.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', (d) => d.confidence)
      .attr('stroke-width', 2)

    // Create nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .join('circle')
      .attr('r', 20)
      .attr('fill', (d) => getNodeColor(d.type))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        setSelectedNode(d)
      })
      .call(d3.drag<any, any>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any)

    // Create labels
    const label = g.append('g')
      .selectAll('text')
      .data(data.nodes)
      .join('text')
      .text((d) => d.name)
      .attr('font-size', 12)
      .attr('dx', 25)
      .attr('dy', 4)

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y)

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y)

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y)
    })

    // Drag functions
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: any) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    return () => {
      simulation.stop()
    }
  }, [data])

  const getNodeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      person: '#3b82f6',
      organization: '#10b981',
      location: '#f59e0b',
      concept: '#8b5cf6',
      event: '#ef4444',
    }
    return colors[type] || '#6b7280'
  }

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current!)
    svg.transition().call(d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 1.3)
  }

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current!)
    svg.transition().call(d3.zoom<SVGSVGElement, unknown>().scaleBy as any, 0.7)
  }

  const handleFitView = () => {
    const svg = d3.select(svgRef.current!)
    svg.transition().call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Knowledge Graph</h2>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleZoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleZoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={handleFitView}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Graph */}
      <div className="flex-1 relative">
        <svg ref={svgRef} className="w-full h-full" />
        
        {/* Node details panel */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 bg-white rounded-lg shadow-lg p-4 max-w-sm border border-gray-200">
            <h3 className="font-semibold text-lg mb-2">{selectedNode.name}</h3>
            <div className="space-y-1 text-sm">
              <p><span className="text-gray-600">Type:</span> {selectedNode.type}</p>
              <p><span className="text-gray-600">Confidence:</span> {(selectedNode.confidence * 100).toFixed(1)}%</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="mt-3"
              onClick={() => setSelectedNode(null)}
            >
              Close
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
```

### 6. package.json

```json
{
  "name": "shield-ag-ui-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3001",
    "build": "next build",
    "start": "next start -p 3001",
    "lint": "next lint",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "@ag-ui/react": "^0.1.0",
    "@ag-ui/core": "^0.1.0",
    "next": "14.1.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "d3": "^7.8.5",
    "lucide-react": "^0.316.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.17.19",
    "zod": "^3.22.4",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.1"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "@types/d3": "^7.4.3",
    "typescript": "^5",
    "tailwindcss": "^3.4.1",
    "postcss": "^8",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "14.1.0"
  }
}
```

### 7. Dockerfile

```dockerfile
# Multi-stage build for Shield AG-UI Frontend (Next.js)
FROM node:20-alpine AS base

# Stage 1: Install dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Stage 2: Build application
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build Next.js app
RUN npm run build

# Stage 3: Production runtime
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built assets
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3001

ENV PORT=3001
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3001/api/health', (r) => {r.statusCode === 200 ? process.exit(0) : process.exit(1)})"

CMD ["node", "server.js"]
```

### 8. next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8002',
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/:path*`,
      },
      {
        source: '/events',
        destination: `${process.env.NEXT_PUBLIC_BACKEND_URL}/events`,
      },
    ]
  },
}

module.exports = nextConfig
```

## Acceptance Criteria

- [x] Complete Next.js 14 directory structure created
- [x] App Router (not Pages Router) configured
- [x] TypeScript configuration
- [x] TailwindCSS setup
- [x] AG-UI React SDK integrated
- [x] AgentChat component with SSE
- [x] KnowledgeGraphViz with D3.js
- [x] EventTimeline component
- [x] Authentication pages (login, dashboard)
- [x] Layout components (Header, Sidebar, Footer)
- [x] Multi-stage Dockerfile (optimized)
- [x] Non-root user in container
- [x] Health check endpoint
- [x] package.json with all dependencies
- [x] next.config.js with standalone output

## Testing

```bash
# Install dependencies
cd roles/ag_ui_deployment/files/frontend/
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Type check
npm run type-check

# Lint
npm run lint

# Build Docker image
docker build -t shield-ag-ui-frontend:test .
```

## Next Tasks

- T004: Create Docker Compose Configuration
- T011: Implement Authentication UI Components
- T012: Implement Job Tracker Component
- T013: Implement Tool Forms Component

## Notes

- Uses Next.js 14 App Router (not Pages Router)
- AG-UI React SDK for protocol compliance
- D3.js for knowledge graph visualization (force-directed layout)
- SSE for real-time event streaming
- Zustand for state management (lightweight)
- React Query for server state
- TailwindCSS for styling
- Multi-stage Docker build for optimized image
- Standalone output for Docker deployment
- Non-root user for container security
- Health check for monitoring

## Related Documents

- [Architecture - Frontend Architecture](../SHIELD-AG-UI-ARCHITECTURE.md#31-frontend-architecture-shield-ag-ui)
- [Implementation Plan - Frontend Phase](../DEV-SERVER-AG-UI-IMPLEMENTATION-PLAN.md#phase-3-frontend-development)

