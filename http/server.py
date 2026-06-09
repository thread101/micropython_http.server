import os
import socket
import utime
import network
import pHeader

html = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{}</title>
</head>
<body>
  {}
</body>
</html>
'''

class SimpleHTTPServer:
    def __init__(self, path: str=".", port: int=8080):
        assert self.is_dir(path), "Path doesn't exist"
        self.path = path
        self.port = port
        self.mime = {
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript",
            "json": "application/json",
            "txt": "text/plain",
            "py": "x-python",
        }        
        self.active = False
        
    def is_dir(self, path: str):
        try:
            pwd = os.getcwd()
            os.chdir(path)
            os.chdir(pwd)
            return True
        except Exception:
            return False
        
    def is_file(self, path: str):
        try:
            with open(path, "r") as f: f.read(1)
            return True
        except Exception:
            return False
    
    def serve_dir(self, path: str):
        full_path = f"{self.path}{path}"
        assert self.is_dir(full_path), "File not found"
        all_files = os.listdir(full_path)
        folders, files = [], []
        for file in all_files:
            p = f"{full_path}{file}"
            if self.is_dir(p): folders.append(f"{file}/")
            else: files.append(file)
        folders.extend(files)
        page = "<ul>\n"
        for file in folders:
            p = f"{path}{file}"
            page += f'<li><a href="{p}">{file}</a></li>\n'
        page += "</ul>\n"
        return page
        
    def serve_file(self, path: str, sock: socket.socket):
        full_path = f"{self.path}{path}"
        assert self.is_file(full_path), "File not found"

        pkt = pHeader.Packet()
        pkt.header.version = "HTTP/1.1"
        pkt.code = 200
        ext = path.rsplit(".")[-1]
        mime = self.mime[ext] if ext in list(self.mime.keys()) else "text/plain"
        with open(full_path, "rb") as f:
            f.seek(0, 2) # move cursor to stream end
            length = f.tell()
        pkt.header.options = [{"Content-Type": mime}, {"Content-Length": length}, {"Server": "picoW"}]
        
        bytes_sent = 0
        with open(full_path, "r") as f:
            iteration = 0
            while True:
                chunk = f.read(4094)  # read up to the network buffer size
                if not chunk: break  # no more data to read
                if iteration == 0:
                    pkt.content = chunk
                    sock.sendall(str(pkt))
                    bytes_sent += len(str(pkt))
                else:
                    sock.sendall(chunk)
                    bytes_sent += len(chunk)
                iteration += 1

        return bytes_sent
        
    def shutdown(self):
        self.log("Exiting ...")
        self.active = False
    
    def log(self, info: str):
        tym = utime.localtime(utime.time())
        print(f"[{tym[0]}-{tym[1]}-{tym[2]} {tym[3]}:{tym[4]}:{tym[5]}] {info}")
        
    def serve(self, timeout: int=0):
        net = network.WLAN(network.STA_IF)
        assert net.isconnected(), "No connected interface"
        startT = utime.time()
        timeout = utime.time() if timeout == 0 else timeout
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        saddr = socket.getaddrinfo("0.0.0.0", self.port)[0][-1]
        s.bind(saddr)
        s.listen(1)
        ip = net.ifconfig()[0]
        self.log(f"Server running on http://{ip}:{self.port} for {self.path} timeout: {timeout}")
        self.active = True
        while self.active and utime.time() - startT < timeout:
            resp = ""
            try:
                cl, addr = s.accept()
                req = pHeader.parse(cl.recv(1024))
                self.log(f"{req.header.method.upper()} {req.header.route} from {addr[0]}:{addr[1]}")
                if req.header.method.lower() != "get":
                    self.log("\033[31;1mUsupported method \033[0m")
                    title = "Error response"
                    content_type = ""
                    for option in req.header.options:
                        if list(option.keys())[0].lower() == "Content-Type":
                            content_type = list(option.values())[0]
                            break
                    else:
                        content_type = "application/json"
                    
                    phtml = f"<h1>{title}</h1>\n"
                    phtml += "<p>Error code: 501</p>\n"
                    phtml += f"<p>Message: Unsupported method ('{content_type}').</p>\n"
                    phtml += "<p>Error code explanation: 501 - Server does not support this operation.</p>"
                    page = html.format(title, phtml)

                    pkt = pHeader.Packet()
                    pkt.header.version = "HTTP/1.1"
                    pkt.code = 501
                    pkt.header.options = [{"Content-Type": "text/html"}, {"Server": "picoW"}]
                    pkt.content = page
                    resp = str(pkt)
                    cl.send(resp)
                else:
                    p = self.get_path(f"{req.header.route}")
                    try:
                        self.serve_file(p, cl)
                    except AssertionError:
                        try:
                            full_path = f"{self.path}{p}"
                            assert self.is_dir(full_path)
                            if "index.html" in os.listdir(full_path):
                                self.serve_file(f"{p}index.html", cl)
                            else:
                                title = f"Directory listing for {p}"
                                phtml = "<header>\n"
                                phtml += f"<h1>{title}</h1>\n"
                                phtml += "</header>\n"
                                phtml += "<hr>\n"
                                phtml += f"{self.serve_dir(p)}"
                                page = html.format(title, phtml)

                                pkt = pHeader.Packet()
                                pkt.header.version = "HTTP/1.1"
                                pkt.code = 200
                                pkt.header.options = [{"Content-Type": "text/html"}, {"Server": "picoW"}]
                                pkt.content = page
                                resp = str(pkt)
                                cl.send(resp)
                        except AssertionError as e:
                            self.log(f"\033[31;1mFile not found\033[0m")
                            title = "Error response"
                            phtml = f"<h1>{title}</h1>\n"
                            phtml += "<p>Error code: 404</p>\n"
                            phtml += "<p>Message: File not found.</p>\n"
                            phtml += "<p>Error code explanation: 404 - Nothing matches the given URI.</p>"
                            page = html.format(title, phtml)

                            pkt = pHeader.Packet()
                            pkt.header.version = "HTTP/1.1"
                            pkt.code = 404
                            pkt.header.options = [{"Content-Type": "text/html"}, {"Server": "picoW"}]
                            pkt.content = page
                            resp = str(pkt)
                            cl.send(resp)
                
            except KeyboardInterrupt:
                self.shutdown()
            except Exception as e:
                self.log(f"({addr[0]}:{addr[1]}) \033[31;1m[error]: {e}\033[0m")
            finally:
                try: cl.close()
                except Exception: pass

        s.close()
        self.log("Server stopped")
        
    def get_path(self, url: str):
        url = url.replace("\\", "", url.count("\\"))
        url = url.replace("../", "", url.count("../"))
        url = url.replace("%20", " ", url.count("%20"))
        return url



if __name__ == "__main__":
    s = SimpleHTTPServer("/")
    s.serve()
