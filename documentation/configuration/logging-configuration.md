# TunaCode Logging Configuration

## Overview

Starting with version 0.0.50, TunaCode has **logging disabled by default** for better performance and privacy. This means no log files are created unless you explicitly enable logging.

## Quick Start

### Default Behavior (Logging OFF)
By default, TunaCode runs without creating any log files:
```json
{
  "default_model": "anthropic:claude-3.5-sonnet"
}
```

### Enable Logging
To enable logging with default settings, add the `logging_enabled` flag to your `~/.config/tunacode.json`:
```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "logging_enabled": true
}
```

This will create log files:
- `tunacode.log` - Detailed logs with rotation
- `tunacode.json.log` - Structured JSON logs

## Custom Logging Configuration

When logging is enabled, you can customize the behavior by adding a `logging` section:

```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "logging_enabled": true,
  "logging": {
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
      "simple": {
        "format": "[%(levelname)s] %(message)s"
      },
      "detailed": {
        "format": "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s"
      }
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "level": "INFO",
        "formatter": "simple",
        "stream": "ext://sys.stdout"
      },
      "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "DEBUG",
        "formatter": "detailed",
        "filename": "tunacode.log",
        "maxBytes": 10485760,
        "backupCount": 3
      }
    },
    "root": {
      "level": "DEBUG",
      "handlers": ["console", "file"]
    },
    "loggers": {
      "tunacode.tools": {
        "level": "INFO"
      },
      "tunacode.ui": {
        "level": "WARNING"
      }
    }
  }
}
```

## Configuration Options

### `logging_enabled`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Master switch to enable/disable all logging

### `logging`
- **Type**: Object
- **Description**: Python logging configuration dictionary following the [dictConfig format](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema)

#### Key sections:
- **`formatters`**: Define how log messages are formatted
- **`handlers`**: Configure where logs are written (files, console, etc.)
- **`loggers`**: Set logging levels for specific modules

## Examples

### Minimal File Logging
```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "logging_enabled": true,
  "logging": {
    "version": 1,
    "handlers": {
      "file": {
        "class": "logging.FileHandler",
        "filename": "my-tunacode.log"
      }
    },
    "root": {
      "handlers": ["file"]
    }
  }
}
```

### Console Only (No Files)
```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "logging_enabled": true,
  "logging": {
    "version": 1,
    "handlers": {
      "console": {
        "class": "logging.StreamHandler"
      }
    },
    "root": {
      "handlers": ["console"]
    }
  }
}
```

### Debug Specific Modules
```json
{
  "default_model": "anthropic:claude-3.5-sonnet",
  "logging_enabled": true,
  "logging": {
    "version": 1,
    "handlers": {
      "debug_file": {
        "class": "logging.FileHandler",
        "filename": "debug.log"
      }
    },
    "loggers": {
      "tunacode.tools": {
        "level": "DEBUG",
        "handlers": ["debug_file"]
      }
    }
  }
}
```

## Benefits

1. **Performance**: No file I/O overhead when logging is disabled
2. **Privacy**: No logs are created by default, protecting sensitive information
3. **Flexibility**: Full control over logging when you need it
4. **Debugging**: Enable detailed logs only when troubleshooting

## Migration

If you're upgrading from a version before 0.0.50:
- No action required - logging will be automatically disabled
- To keep previous logging behavior, add `"logging_enabled": true` to your config
- Your existing log files will remain untouched

## Troubleshooting

**Q: I enabled logging but don't see any log files**
- Ensure your config file is valid JSON
- Check file permissions in the directory where logs should be created
- Try a simple configuration first to verify it's working

**Q: How do I see what TunaCode is doing internally?**
- Enable logging and set the root level to "DEBUG"
- Use the console handler to see logs in real-time

**Q: Can I change logging settings without restarting?**
- Currently, you need to restart TunaCode for logging changes to take effect
