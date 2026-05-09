# cae_tools

CAE System List project — starter files and utilities.

## Structure

```
cae_tools/
├── src/
│   ├── types/
│   │   └── cae.ts                # TypeScript interfaces (CAESystem, CAEDomain, etc.)
│   └── data/
│       ├── caeSystems.json       # Initial CAE system data (15 tools)
│       └── caeTargets.json       # Cron fetch targets (vendor news URLs)
└── README.md
```

## Setup

1. Scaffold React + Vite + TypeScript project
2. Configure GitHub Actions deploy (see `.github/workflows/deploy.yml`)
3. Set the following GitHub Actions secrets in your repository settings:
   - `SAKURA_SSH_KEY` — private key for SSH access
   - `SAKURA_HOST` — deployment server hostname
   - `SAKURA_USER` — deployment server username
   - `DEPLOY_PATH` — absolute path to the web root directory
   - `SCRIPTS_PATH` — absolute path to the scripts directory
   - `REPO_DATA_PATH` — absolute path to the data directory on the server
4. Set `DEPLOYED_JSON` environment variable for the cron script (path to output JSON)
