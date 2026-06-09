# micropython_http.server

A lightweight MicroPython HTTP server module for Raspberry Pi Pico W.

This project implements a small HTTP server in `http/server.py` that can serve static files and directory listings from a local filesystem on Pico W.

## Features

- Simple static file serving using `SimpleHTTPServer`
- Directory listing generation when a directory has no `index.html`
- MIME type handling for `html`, `css`, `js`, `json`, `txt`, and `py`
- Supports `GET` requests only
- Uses the `pHeader` packet parsing library for HTTP request/response handling
- Includes `pic.txt` as a large (~16KB) file for efficiency testing

## Requirements

- MicroPython on Raspberry Pi Pico W
- `network`, `socket`, `os`, and `utime` modules provided by MicroPython
- `pHeader` dependency from:
  - https://github.com/thread101/micropython_header_parsing.git

## Installation

1. Copy this repository onto your Pico W filesystem at `/lib`.
2. Install or copy the `pHeader` MicroPython module from the dependency repository.
3. Make sure `http/server.py` and `http/__init__.py` are available on the Pico W.

### Expected filesystem layout

```text
/lib
  ├── http
  │   ├── __init__.py
  │   └── server.py
  ├── pic.txt
  └── README.md
```

## Usage

### From the command line

```python
from http.server import SimpleHTTPServer

server = SimpleHTTPServer(path='/', port=8080)
server.serve(timeout=0)
```

By default, `SimpleHTTPServer` uses the current working directory as its root when created with `path='.'`.

### From a main script

```python
import network
from http.server import SimpleHTTPServer

# connect the Pico W to Wi-Fi first
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect('SSID', 'PASSWORD')

while not wlan.isconnected():
    pass

server = SimpleHTTPServer(path='/', port=8080)
server.serve(timeout=0)
```

## API

### `SimpleHTTPServer(path='.', port=8080)`

- `path`: Root serving folder on the Pico W filesystem
- `port`: Port to listen on (default `8080`)

### `serve(timeout=0)`

- `timeout`: Maximum runtime in seconds. Use `0` for no timeout.

### `shutdown()`

Stops the server loop and closes the socket.

## Behavior

- Requests are parsed using `pHeader.parse()`.
- Only `GET` requests are handled.
- If the requested path resolves to a file, the file is returned with the appropriate `Content-Type`.
- If the requested path resolves to a directory and contains `index.html`, that file is served.
- If the requested path resolves to a directory without `index.html`, a generated HTML directory listing is returned.
- If the request path is not found, the server returns a `404` HTML error page.

## Test file: `pic.txt`

This repository includes `pic.txt` as a large test file (about 16KB) to verify the server's ability to serve larger static content efficiently.

## Notes

- The server uses `sock.sendall()` and reads files in chunks of `4094` bytes.
- Response headers are built through the `pHeader.Packet` class.
- This implementation is intended for simple local file serving on Pico W and is not a full production HTTP server.

## Dependency

This server relies on the `pHeader` module from the following GitHub repository:

- https://github.com/thread101/micropython_header_parsing.git

Make sure that `pHeader.py` or the equivalent module is available on the Pico W filesystem.
