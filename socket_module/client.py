import socket
import threading
import telebot

TELEGRAM_TOKEN = '6962397424:AAFiGfycmm0yoCJzQJ_Bg_fgkb3XGUJED5M'

HEADER = 64
PORT = 5050
SERVER = "172.100.2.218"
ADDR = (SERVER, PORT)
FORMAT = "ASCII"
DISCONNECT_MESSAGE = "!DISCONNECT"

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect(ADDR)

send_photo_flag = False

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
def recv(run_event):
    global send_photo_flag
    connected = True
    while run_event.is_set() and connected:

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

def telegram_bot(run_event):
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    def send_photo():
        global send_photo_flag
        while run_event.is_set():  
            if send_photo_flag: 
                with open('img/screenshot.jpg', 'rb') as photo:
                    bot.send_photo('1815092465', photo)
                    send_photo_flag = False
        bot.stop_polling()

    try:
        print("Bot is running...")
        th = threading.Thread(target=send_photo)
        th.start()
        bot.polling(none_stop=True)
        th.join()
    except Exception as e:
        print(e)


def main():
    try:
        run_event = threading.Event()
        run_event.set()
        th = threading.Thread(target=telegram_bot, args=(run_event, ))
        th.daemon = True
        th.start()

        th1 = threading.Thread(target=recv, args=(run_event, ))
        th1.daemon = True
        th1.start()

    except KeyboardInterrupt:
        run_event.clear()
        th.join()
        th1.join()
        print("Server is stopped")

if __name__ == "__main__":
    main()