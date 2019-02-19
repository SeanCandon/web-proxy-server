import socket
import sys
import _thread

PORT = 8080
buff_size = 4096

CACHE = {}
# BLOCKED = {}


def main():
    try:
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
            # print(data)
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
    if https is False:
        proxy_server_http(webserver, port, conn, data, addr, url)
    else:
        proxy_server_https(webserver, port, conn, addr)


def proxy_server_http(webserver, port, conn, data, addr, url):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, port))
        sock.send(data)

        # reply = ''
        reply = bytearray("", 'utf-8')
        while 1:
            temp = sock.recv(buff_size)
            if(len(temp) > 0):
                conn.send(temp)
                reply.extend(temp)
                # temp = temp.decode('cp1252').encode('utf-8')
                # reply += temp.decode('utf-8')
                # reply += str(temp, 'utf-8')
            else:
                break

        # conn.sendall(reply.encode())

        # reply = sock.recv(buff_size)
        # conn.sendall(reply)

        sock.close()
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
    # url = url1.split('/')[1]

    host = ""
    for l in lines:
        h = l.find("Host")
        if h != -1:
            host = l
            break

    webserver = host.split(": ")[1]
    port_pos = webserver.find(":")
    port = 80
    if port_pos != -1:
        port = int(webserver[(port_pos+1):])
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


main()
