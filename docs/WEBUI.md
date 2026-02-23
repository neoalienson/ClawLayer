# ClawLayer Web UI

The ClawLayer Web UI provides **complete visibility into OpenClaw-LLM communication** for security monitoring, development, and troubleshooting.

![ClawLayer Web UI](assets/webui.png)

## Features

### Dashboard
Real-time statistics showing:
- Request counts by router type
- Router hit rates (quick/semantic/LLM fallback)
- Average latency per router
- System uptime

### Config Editor
- Edit YAML configuration directly in the browser
- Syntax highlighting and validation
- Reload configuration without restarting the server
- Backup and restore previous configurations

### Log Viewer
- **Real-time request monitoring**: See all requests as they happen
- **Detailed inspection**: Click any log entry to view full details
- **Complete visibility**: Inspect untruncated prompts, context, and responses
- **Router tracking**: Understand which router handled each request and why
- **Performance monitoring**: Monitor latency per request

## Use Cases

### 🛡️ Security
- Monitor for prompt injection attempts
- Detect data leakage in responses
- Identify policy violations
- Track suspicious patterns in requests

### 🐛 Development
- Debug agent behavior in real-time
- Understand decision-making process
- Test routing configurations
- Validate prompt engineering

### 🔧 Troubleshooting
- Identify performance bottlenecks
- Analyze request failures
- Optimize routing efficiency
- Debug cascade fallback behavior

### 📚 Learning
- Understand how OpenClaw agents communicate with LLMs
- Study prompt patterns and responses
- Learn routing optimization techniques
- Analyze cost vs accuracy tradeoffs

## Getting Started

### Installation

```bash
# Install web UI dependencies (first time only)
cd webui && npm install && cd ..
```

### Running

**Start both backend and web UI:**
```bash
./start-dev.sh
```

**Or start separately:**
```bash
# Terminal 1: Backend
python run.py -v

# Terminal 2: Web UI
cd webui && npm run dev
```

### Access

- **Backend API**: http://localhost:11435
- **Web UI**: http://localhost:3000

### Stopping

```bash
./stop-dev.sh
```

## Configuration

The Web UI automatically connects to the ClawLayer backend on `localhost:11435`. To change this:

```bash
# In webui/.env
VITE_API_URL=http://your-backend:11435
```

## Features in Detail

### Request Inspection

Each log entry shows:
- **Timestamp**: When the request was received
- **Router**: Which router handled the request (quick/semantic/LLM)
- **Latency**: Time taken to process the request
- **Status**: Success/failure indicator

Click any entry to see:
- **Full prompt**: Complete untruncated prompt sent to LLM
- **Context**: All context data (conversation history, system messages)
- **Response**: Complete untruncated response
- **Routing details**: Stage-by-stage cascade information
- **Confidence scores**: Similarity/confidence at each stage

### Configuration Management

The config editor provides:
- **Syntax highlighting**: YAML syntax highlighting
- **Validation**: Real-time validation of configuration
- **Backup rotation**: Automatic backups of previous configurations
- **Hot reload**: Apply changes without restarting

### Statistics Dashboard

Monitor system performance:
- **Request distribution**: Pie chart showing router usage
- **Latency trends**: Line chart showing latency over time
- **Hit rates**: Percentage of requests handled by each router
- **Cost tracking**: Estimated API costs based on router usage

## Security Considerations

The Web UI is designed for **local development and monitoring**. For production:

1. **Restrict access**: Use firewall rules to limit access
2. **Enable authentication**: Add authentication layer (nginx, etc.)
3. **Use HTTPS**: Encrypt traffic with TLS
4. **Monitor logs**: Regularly review access logs

## Troubleshooting

### Web UI won't start

```bash
# Check if port 3000 is available
lsof -i :3000

# Reinstall dependencies
cd webui && rm -rf node_modules && npm install
```

### Can't connect to backend

```bash
# Check if backend is running
curl http://localhost:11435/v1/models

# Check backend logs
python run.py -v
```

### Configuration changes not applying

```bash
# Reload configuration via API
curl -X POST http://localhost:11435/api/reload

# Or restart backend
./stop-dev.sh && ./start-dev.sh
```

## Related Documentation

- [README.md](../README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [QUICK_ROUTER.md](QUICK_ROUTER.md) - Quick router documentation
