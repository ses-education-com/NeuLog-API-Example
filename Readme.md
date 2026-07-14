# NeuLog API Examples

This repository contains example programs demonstrating how to communicate with NeuLog sensors using the **NeuLog API**.

The examples illustrate how to access the API from different programming languages and can serve as a starting point for developing your own applications.


## Requirements

Before running the examples, make sure that:

- NeuLog API is installed on your computer.
- At least one NeuLog sensor is connected through a NeuLog USB Module or Bluetooth Module.
- The NeuLog API application is running.

By default, the API listens on:

```
http://localhost:22001
```

If port **22001** is unavailable, the API automatically opens the next available port.

## Available Examples

### JavaScript

The JavaScript example demonstrates communication with the NeuLog API directly from a web browser using standard HTTP GET requests.

Open:

```
JavaScript/index.html
```

in your browser after the NeuLog API is running.

---

### Python

The Python example demonstrates how to send HTTP requests to the NeuLog API and receive JSON responses.

Run:

```bash
python Demo_python.py
```

## API Documentation

The complete API reference is included in this repository:

**manual.pdf**

The manual contains:

- API architecture
- Communication protocol
- Complete command reference
- Experiment commands
- Photo Gate commands
- Sensor list
- Response format


Please refer to the manual for detailed information about all supported commands and parameters.

## Communication Model

The NeuLog API uses standard HTTP GET requests.

Example:

```
http://localhost:22001/NeuLogAPI?GetSensorValue:[Light],[1]
```

Typical responses are returned in JSON format, for example:

```json
{
    "GetSensorValue":[532]
}
```


## Support

For additional information, software updates and product documentation, visit:

https://neulog.com

## License

See the LICENSE file for details.

Copyright © NeuLog.