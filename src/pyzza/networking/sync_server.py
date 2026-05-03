import asyncio
import socket
import threading
import urllib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen

from zeroconf import Zeroconf, ServiceInfo, ServiceListener
from zeroconf.asyncio import AsyncZeroconf, AsyncServiceBrowser

PORT = 8765
SERVICE_TYPE = "_pyzza._tcp.local."
SERVICE_NAME = "Pyzza._pyzza._tcp.local."


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


class FileHandler(BaseHTTPRequestHandler):
    file_path = None
    callback = None

    def do_GET(self):
        if self.path == "/data":
            with open(FileHandler.file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(content)
            if self.callback:
                self.callback(f"{self.client_address[0]}:{self.client_address[1]}")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


class SyncServer:
    def __init__(self, callback):
        FileHandler.callback = callback
        self.server = HTTPServer(("0.0.0.0", PORT), FileHandler)
        self.zc = None
        self.started = False
        self.ip = None

    def start(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

        # advertise via zeroconf
        self.ip = get_local_ip()
        self.zc = Zeroconf()
        info = ServiceInfo(
            SERVICE_TYPE, SERVICE_NAME,
            addresses=[socket.inet_aton(self.ip)],
            port=PORT,
        )
        self.zc.register_service(info)

        self.started = True

    @staticmethod
    def set_file(new_path): FileHandler.file_path = new_path

    def stop(self):
        if self.zc:
            self.zc.unregister_all_services()
            self.zc.close()
        self.server.shutdown()
        self.started = False

    def server_address(self): return f"{self.ip}:{PORT}"


async def fetch(timeout=3, print_callback=lambda x: None) -> bytes:
    found = []
    event = asyncio.Event()

    # print_callback("Starting")

    class Listener:
        def add_service(self, zc, type_, name):
            # print_callback(f"add_service({name=})")

            async def get_info():
                info = await azc.async_get_service_info(type_, name)
                print_callback(f"Found provider")
                if info:
                    found.append(info)
                    event.set()

            asyncio.ensure_future(get_info())

        def remove_service(self, *args):
            pass

        def update_service(self, *args):
            pass

    azc = AsyncZeroconf()
    # print_callback(f"Built {azc.__class__.__name__}")
    try:
        browser = AsyncServiceBrowser(azc.zeroconf, SERVICE_TYPE, Listener())
        # print_callback(f"Built {browser.__class__.__name__}")
        await asyncio.wait_for(event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print_callback(f"Exception: {e}")
    finally:
        await azc.async_close()

    if not found:
        print_callback("No providers found. Is synchronization active on desktop app?")
        return None

    info = found[0]
    ip = socket.inet_ntoa(info.addresses[0])
    url = f"http://{ip}:{info.port}/data"
    print_callback(f"Requesting file from {ip}:{info.port}")
    with urlopen(url) as r:
        data = r.read()
        print_callback(f"Received {len(data)} bytes")
        return data
