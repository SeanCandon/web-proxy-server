import socket
import sys
import _thread
import tkinter as tk
from tkinter import *

PORT = 8080
buff_size = 4096

CACHE = {}
PRIORITY = {}
MAX_CACHE_SIZE = 4
CURRENT_CACHE_SIZE = 0
BLOCKED = {}
TIME = {}


def main():
    try:
        _thread.start_new_thread(console, ())
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', PORT))
        sock.listen(10)
        print("She's binded!")
    except Exception:
        sys.exit(0)

    while 1:
        try:
            conn, addr = sock.accept()
            data = conn.recv(buff_size)
            _thread.start_new_thread(proxy_server, (conn, data, addr))
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    sock.close()


def proxy_server(conn, data, addr):
    https, webserver, port, url = conn_string(data)
    print("url = " + url)
    print("webserver = " + webserver)
    print("port = " + str(port))
    b = BLOCKED.get(url)
    if b != 1:
        if https is False:
            proxy_server_http(webserver, port, conn, data, addr, url)
        else:
            proxy_server_https(webserver, port, conn, addr, url)
    else:
        print("sorry that url is blocked")
        conn.close()


def proxy_server_http(webserver, port, conn, data, addr, url):
    try:

        x = CACHE.get(url)
        if x is not None:
            print("in cache")
            t = TIME.get(url)
            lines = data.decode().split('\n')
            message = ""
            message += lines[0] + '\n'
            message += "If-Modified-Since: "
            message += t

            i = 1
            while i < len(lines):
                if i != (len(lines)-1):
                    message += lines[i] + '\n'
                else:
                    message += lines[i]
                i += 1

            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((webserver, port))
            send_and_cache(s2, message.encode(), url, conn)

        else:
            print("not in cache")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((webserver, port))

            send_and_cache(sock, data, url, conn)

        conn.close()
    except socket.error:
        sock.close()
        conn.close()
        sys.exit(2)


def proxy_server_https(webserver, port, conn, addr):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, port))

        sock.setblocking(0)
        conn.setblocking(0)

        conn.sendall("HTTP/1.0 200 Connection established\r\nProxy-Agent: Pyx\r\n\r\n".encode())

        while 1:
            try:
                reply1 = conn.recv(buff_size)
                if ((not reply1) or (len(reply1) <= 0)):
                    break
                sock.sendall(reply1)
            except socket.error:
                pass

            try:
                reply2 = sock.recv(buff_size)
                if ((not reply2) or (len(reply2) <= 0)):
                    break
                conn.sendall(reply2)
            except socket.error:
                pass

        conn.close()
        sock.close()

    except socket.error:
        conn.close()
        sys.exit(2)


def parse_request(request):
    https = False

    print(request)

    lines = request.decode().split('\n')
    get = lines[0].find("GET")
    if get == -1:
        https = True

    url = lines[0].split(' ')[1]

    host = ""
    for l in lines:
        h = l.find("Host")
        if h != -1:
            host = l
            break

    webserver = host.split(": ")[1]
    port_pos = webserver.find(":")
    port = 80
    # if port_pos != -1:
        # port = int(webserver[(port_pos+1):])
    webserver2 = ""
    i = 0
    if port_pos != -1:
        while i < port_pos:
            webserver2 += webserver[i]
            i += 1
    else:
        webserver2 = webserver

    if https is True:
        port = 443

    return https, webserver2, port, url


def conn_string(data):
    https = False
    try:
        first = data.decode().split('\n')[0]
        get = first.find("GET")
        if get == -1:
            https = True
        url = first.split(' ')[1]
        http_pos = url.find("://")
        if(http_pos == -1):
            temp = url
        else:
            temp = url[(http_pos+3):]

        port_pos = temp.find(":")
        webserver_pos = temp.find("/")
        if webserver_pos == -1:
            webserver_pos = len(temp)
        webserver = ""
        port = -1
        if (port_pos == -1):
            port = 80
            webserver = temp[:webserver_pos]
        else:
            port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
            webserver = temp[:port_pos]

        if https:
            port = 443

        return https, webserver, port, url
    except Exception:
        print("fugg")
        pass


def console():
    console = tk.Tk()
    block_input = Entry(console)
    block_input.grid(row=0, column=0)
    unblock_input = Entry(console)
    unblock_input.grid(row=1, column=0)

    def callback1():
        e = block_input.get() + "/"
        b = BLOCKED.get(e)
        if b is None:
            BLOCKED[e] = 1
            print("blocked")
        else:
            print("already blocked")

    def callback2():
        e = unblock_input.get() + "/"
        b = BLOCKED.get(e)
        if b is not None:
            BLOCKED.pop(e)
            print("unblocked")
        else:
            print("not blocked")

    block = Button(console, text = "BLOCK", command=callback1)
    block.grid(row=0, column=1)
    block = Button(console, text = "UNBLOCK", command=callback2)
    block.grid(row=1, column=1)
    mainloop()


def get_time(response):
    start = 0
    end = 0
    i = 0
    time = ""
    while i < len(response):
        if((response[i] == ord('D')) and (response[i+1] == ord('a'))
           and (response[i+2] == ord('t')) and (response[i+3] == ord('e'))):
            start = i + 6
            end = start + 30
            break
        i += 1

    i = 0
    while i < (len(response)):
        if(i >= start and i <= end):
            time += chr(response[i])
        i += 1

    return time


def send_and_cache(sock, data, url, conn):
    sock.send(data)

    sock.settimeout(2)

    reply = bytearray("", 'utf-8')
    try:
        while 1:
            temp = sock.recv(buff_size)
            if(len(temp) > 0):
                # conn.send(temp)
                reply.extend(temp)
            else:
                break
    except socket.error:
        pass

    if is_modified(reply):
        conn.sendall(reply)
        CACHE[url] = reply
        time = get_time(reply)
        TIME[url] = time
        global CURRENT_CACHE_SIZE
        if CURRENT_CACHE_SIZE < MAX_CACHE_SIZE:
            CURRENT_CACHE_SIZE += 1
        else:
            u = PRIORITY.get(1)
            PRIORITY.pop(1)
            CACHE.pop(u)
            TIME.pop(u)
            print(u + "removed from cache")
            i = 2
            while i <= MAX_CACHE_SIZE:
                u1 = PRIORITY.get(i)
                PRIORITY.pop(i)
                PRIORITY[i-1] = u1
                i += 1
            PRIORITY[CURRENT_CACHE_SIZE] = url
        print("added to cache")
    else:
        print("retrieved from cache")
        conn.sendall(CACHE.get(url))

    sock.close()


def is_modified(reply):
    i = 0
    while i < len(reply):
        if (reply[i] == ord('2') and reply[i+1] == ord('0') and reply[i+2] == ord('0')
           and reply[i+4] == ord('O') and reply[i+5] == ord('K')):
            print("has been modified since")
            return True
        i += 1
    return False


main()
