import socket
import json
import copy
from labs import lab1_signals, fourier_series

PORT = 5000
LABS = {
    "lab1": lab1_signals,
    "fourier": fourier_series,
}

def handle(connection):
    buffer = b""
    while True:
        data = connection.recv(65536)
        if not data:
            raise ConnectionError("client closed")
        buffer += data
        while b"\n" in buffer:
            line, buffer = buffer.split(b"\n", 1)
            request = json.loads(line)
            module = LABS[request["lab"]]
            settings = copy.deepcopy(module.DEFAULTS)
            settings.update(request.get("settings", {}))
            answer = module.compute(settings)
            answer["lab"] = request["lab"]
            connection.sendall((json.dumps(answer) + "\n").encode())

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("0.0.0.0", PORT))
server.listen(1)
print("Server ready on port", PORT)

while True:
    print("Waiting for a client...")
    connection, address = server.accept()
    print("Client connected:", address)
    try:
        handle(connection)
    except (ConnectionError, OSError, ValueError, KeyError) as error:
        print("Disconnected:", error)
    connection.close()