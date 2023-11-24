import socket
import threading

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = "ASCII"
DISCONNECT_MESSAGE = "!DISCONNECT"
MSG = ""

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen(2)


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    while connected:

        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)

            if msg == DISCONNECT_MESSAGE:
                connected = False

            print(f"[{addr}] {msg}")
            conn.send("Msg received".encode(FORMAT))

    conn.close()

def handle_client_send(conn, addr):
    global MSG
    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    while connected:
        if MSG:
            message = MSG.encode(FORMAT)
            msg_length = len(message)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b" " * (HEADER - len(send_length))
            conn.send(send_length)
            conn.send(message)
            MSG = False

        if MSG == DISCONNECT_MESSAGE:
            connected = False
    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client_send, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
    


def main():
    print("Start server...")
    threading.Thread(target=start).start()
    global MSG
    while True:
        try:
            MSG = input("Server: ")
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()