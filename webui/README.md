# ClawLayer Web UI

Modern web interface for ClawLayer built with Lit and Vite.

## Setup

```bash
npm install
```

## Development

```bash
# Start Python backend (Terminal 1)
cd ../
python run.py -v

# Start web UI (Terminal 2)
cd webui
npm run dev
```

Open http://localhost:3000

## Build

```bash
npm run build
```

Output in `dist/` directory.

## Features

- **Dashboard**: Real-time stats and router performance
- **Config Editor**: Edit and save configuration
- **Logs**: View request logs in real-time
