import socket
import threading
import telebot

from config import TELEGRAM_TOKEN

HEADER = 64
PORT = 5050
SERVER = "192.168.31.16"
ADDR = (SERVER, PORT)
FORMAT = "ASCII"
DISCONNECT_MESSAGE = "!DISCONNECT"

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(ADDR)

send_photo_flag = False
connected = True


# Send message to server
def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b" " * (HEADER - len(send_length))
    socket.send(send_length)
    socket.send(message)
    print(socket.recv(HEADER).decode(FORMAT))


# Receive message from server
def recv():
    global send_photo_flag
    global connected

    while connected:

        msg_length = socket.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = socket.recv(msg_length).decode(FORMAT)
            print(f"[SERVER] {msg}")
            if msg == DISCONNECT_MESSAGE:
                connected = False
            if msg == "send photo":
                send_photo_flag = True

    socket.close()


def send_photo():
    global send_photo_flag

    bot = telebot.TeleBot(TELEGRAM_TOKEN)
    while connected:

        if send_photo_flag: 
            with open('img/screenshot.jpg', 'rb') as photo:
                bot.send_photo('1815092465', photo)
                send_photo_flag = False


   

def main():
    print("Start client...")

    bot_thread = threading.Thread(target=send_photo)
    bot_thread.daemon = True
    bot_thread.start()

    recv_thread = threading.Thread(target=recv)
    recv_thread.daemon = True
    recv_thread.start()

    bot_thread.join()
    recv_thread.join()


if __name__ == "__main__":
    main()