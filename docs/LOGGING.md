# Voice Assistant Logging System

## Overview

The Voice Assistant uses a centralized logging system that stores all log files in the `logs/` directory. This document outlines the logging configuration and the various log files created by the application.

## Log Files Structure

All log files are stored in the `logs/` directory:

```
logs/
├── app.jsonl                           # Main application logs (structured JSON)
├── performance.jsonl                   # Performance metrics and timing data
├── dialog_YYYY-MM-DD_HH-MM-SS.log      # Conversation logs (human-readable)
├── transcriptions.log                  # STT transcriptions (rotating daily)
├── transcriptions.log.YYYY-MM-DD       # Rotated transcription logs
└── main_app.log                        # Application stdout/stderr
```

## Log File Descriptions

### 1. `app.jsonl` - Main Application Logs
- **Format**: JSON Lines (one JSON object per line)
- **Content**: All application logs from all services
- **Level**: DEBUG and above
- **Rotation**: No automatic rotation
- **Purpose**: Structured logging for debugging and monitoring

**Example entry**:
```json
{"timestamp": "2025-07-30T11:46:23.456789", "level": "INFO", "name": "main", "message": "Voice assistant ready - listening for wake word..."}
```

### 2. `performance.jsonl` - Performance Metrics
- **Format**: JSON Lines
- **Content**: Timing data, token counts, resource usage
- **Purpose**: Performance monitoring and optimization

**Example entry**:
```json
{"timestamp": "2025-07-30T11:46:23.789", "event": "llm_response", "duration_ms": 1250.45, "context": {"input_length": 15, "output_length": 87}}
```

### 3. `dialog_*.log` - Conversation Logs
- **Format**: Human-readable text
- **Content**: Complete conversation transcripts
- **Naming**: `dialog_YYYY-MM-DD_HH-MM-SS.log` (one per session)
- **Purpose**: Conversation history and analysis

**Example entries**:
```
[30-07-11-46-23] USER: What's the weather like today?
[30-07-11-46-23] INTENT: web_search
[30-07-11-46-25] ASSISTANT: I'll check the weather for you...
```

### 4. `transcriptions.log` - STT Transcriptions
- **Format**: Timestamped text entries
- **Content**: All speech-to-text transcriptions
- **Rotation**: Daily (keeps 7 days of backups)
- **Purpose**: Speech recognition accuracy monitoring

**Example entries**:
```
2025-07-30 11:46:23,456: What's the weather like today?
2025-07-30 11:47:15,789: Set a reminder for 3 PM
```

### 5. `main_app.log` - Application Output
- **Format**: Plain text
- **Content**: Console output (stdout/stderr)
- **Purpose**: Debugging application startup and runtime issues

## Logging Configuration

### Logger Hierarchy
```
app_logger (singleton)
├── main                    # Main application
├── microservices_loader    # Service initialization
├── stt_service            # Speech-to-text
├── llm_service            # Language model
├── tts_service            # Text-to-speech
├── kwd_service            # Wake word detection
├── dashboard              # Real-time dashboard
└── transcriptions         # Dedicated STT logger
```

### Log Levels
- **Console**: INFO and above (colored output)
- **File**: DEBUG and above (structured JSON)
- **Performance**: All timing events

### Special Features
- **Color-coded console output** for easy reading
- **ANSI color filtering** for clean file logs
- **Thread-safe logging** for concurrent services
- **Structured JSON logging** for programmatic analysis
- **Performance timing** with microsecond precision
- **Automatic log rotation** for transcriptions

## Log Management

### Using the Log Management Script

The project includes a `manage_logs.py` script for log file management:

```bash
# Check current log files status
python3 manage_logs.py --check

# Move misplaced log files to logs/ directory
python3 manage_logs.py --organize

# Clean up old log files (>7 days)
python3 manage_logs.py --clean

# Show detailed logging system status
python3 manage_logs.py --status
```

### Manual Log Management

```bash
# View recent application logs
tail -f logs/app.jsonl | jq .

# Monitor performance metrics
tail -f logs/performance.jsonl | jq .

# Check conversation history
cat logs/dialog_*.log

# Monitor transcriptions
tail -f logs/transcriptions.log

# Check application output
tail -f logs/main_app.log
```

## Configuration Files

### Logger Configuration
- **Location**: `services/logger.py`
- **Singleton pattern**: Ensures consistent logging across all services
- **Automatic directory creation**: Creates `logs/` if it doesn't exist

### Excluded Files
These files are **NOT** stored in `logs/` (they belong elsewhere):
- `config/memory.log` - User memory file (configuration data)

## Best Practices

### For Developers
1. **Use structured logging** with context information
2. **Include performance timing** for critical operations
3. **Use appropriate log levels** (DEBUG/INFO/WARNING/ERROR/CRITICAL)
4. **Add exception context** when logging errors

### For System Administrators
1. **Monitor log file sizes** regularly
2. **Set up log rotation** for production deployments
3. **Archive old logs** to prevent disk space issues
4. **Monitor performance metrics** for system optimization

### Example Logging Usage

```python
from services.logger import app_logger

# Get a logger for your service
log = app_logger.get_logger("my_service")

# Log with different levels
log.debug("Detailed debugging information")
log.info("General information about operation")
log.warning("Something unexpected happened")
log.error("An error occurred", extra={"props": {"context": "additional_info"}})

# Log performance metrics
start_time = time.time()
# ... perform operation ...
duration = time.time() - start_time
app_logger.log_performance("operation_name", duration, {"param": "value"})
```

## Troubleshooting

### Common Issues

1. **Log files in wrong location**
   - Run `python3 manage_logs.py --organize` to fix

2. **Permission errors**
   - Ensure the `logs/` directory is writable
   - Check file permissions: `chmod 755 logs/`

3. **Missing transcriptions.log**
   - Normal if no speech has been processed yet
   - File is created on first STT operation

4. **Large log files**
   - Use `manage_logs.py --clean` to remove old files
   - Consider implementing automatic rotation

### Log Analysis

```bash
# Find errors in application logs
grep -i error logs/app.jsonl

# Analyze performance metrics
cat logs/performance.jsonl | jq '.event' | sort | uniq -c

# Check conversation patterns
grep "USER:" logs/dialog_*.log | head -20

# Monitor resource usage
tail -f logs/performance.jsonl | grep -i "cpu\|memory"
```

## Production Considerations

For production deployments, consider:

1. **Log aggregation** (ELK stack, Fluentd, etc.)
2. **Automated log rotation** and archival
3. **Log monitoring** and alerting
4. **Performance dashboard** integration
5. **Log retention policies**
6. **Security considerations** for sensitive data in logs

---

*This logging system provides comprehensive monitoring and debugging capabilities for the Voice Assistant application while maintaining organized and accessible log data.*
