# Shield AG-UI Frontend - Infrastructure Only

This directory contains the **frontend infrastructure** (Dockerfile) provided by the backend infrastructure team.

## Important Notes

- **Frontend code is maintained separately** by the Frontend AI team in the `citadel-shield-ui` repository
- This Dockerfile is a **generic template** that will work with the Vite + React application
- The actual frontend source code (6,500 LOC) will be deployed here during Ansible playbook execution

## Dockerfile

The `Dockerfile` in this directory:
- Uses Node 20 Alpine for minimal footprint
- Multi-stage build for optimized image size
- Supports npm, yarn, or pnpm package managers
- Runs as non-root user (agui:1001)
- Serves static build on port 3001
- Uses `serve` to serve the Vite production build

## Deployment Process

1. Frontend AI team maintains code in `citadel-shield-ui` repository
2. Ansible playbook clones the frontend repository during deployment
3. This Dockerfile builds the production image
4. Docker Compose orchestrates the frontend container

## Frontend Source

The actual frontend source code lives at:
- **Repository**: `hanax-ai/citadel-shield-ui`
- **Branch**: `feature-1`
- **Technology**: Vite 5.4 + React 18 + TypeScript
- **Lines of Code**: ~6,500 LOC

## License

Proprietary - HX-Citadel Shield Team
