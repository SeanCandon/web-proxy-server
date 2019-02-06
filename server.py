import socket
import sys
import ssl
from thread import *

PORT = 8080
buff_size = 1024
'''
try:
    print int(raw_input(""))
except KeyboardInterrupt:
    print "Exiting..."
    sys.exit(1)
'''


def main():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', PORT))
        sock.listen(10)
        print "She's binded!"
    except Exception, e:
        print "fuck didn't work"
        sys.exit(0)

    while 1:
        try:
            conn, addr = sock.accept()
            data = conn.recv(buff_size)
            start_new_thread(conn_string, (conn, data, addr))
        except KeyboardInterrupt:
            sock.close()
            print "Exiting"
            sys.exit(1)
    print "goodbye"
    sock.close()


def conn_string(conn, data, addr):
    https = False
    try:
        print data
        line1 = data.split('\n')[0]
        get = line1.find("GET")
        if get == -1:
            https = True
        url = line1.split(' ')[1]
        http = url.find("://")
        if (http == -1):
            rest = url
        else:
            rest = url[(http+3):]

        port_pos = rest.find(":")
        server_pos = rest.find("/")
        if server_pos == -1:
            server_pos = len(rest)
        webserver = ""
        port = -1
        if (port_pos == -1 or server_pos < port_pos):
            port = 80
            webserver = rest[:server_pos]
        else:
            port = int((rest[(port_pos+1):])[:server_pos-port_pos-1])
            webserver = rest[:port_pos]

        lines = data.split('\n')
        print len(lines)

        host = ""
        for l in lines:
            h = l.find("Host")
            if h != -1:
                host = l.split(' ')[1]
                break

        if https is False:
            proxy_server_http(webserver, port, conn, data, addr)
        else:
            proxy_server_https(webserver, port, conn, addr, host, url)

    except Exception, e:
        print "fuck didn't work 2"
        pass


def proxy_server_http(webserver, port, conn, data, addr):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, port))
        sock.send(data)

        while 1:
            reply = sock.recv(buff_size)
            if(len(reply) > 0):
                conn.send(reply)
                dar = float(len(reply))
                dar = float(dar / 1024)
                dar = "%.3s" % (str(dar))
                dar = "%s KB" % (dar)
                # print "request complete: %s => %s <=" % (str(addr[0]), str(dar))
            else:
                # print "welp no reply"
                break

        sock.close()
        conn.close()
    except socket.error, (value, message):
        print "fuck didn't work 3"
        sock.close()
        conn.close()
        sys.exit(2)


def proxy_server_https(webserver, port, conn, addr, host, url):
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.verify_mode = ssl.CERT_NONE
        context.check_hostname = False
        conn2 = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=webserver)
        conn2.connect((webserver, 443))
        conn2.sendall("GET "+url+" HTTP/1.1\r\n"+"Host: "+host+"\r\n"+"Connection: close\r\n"+"\r\n")

        reply = ""
        while 1:
            temp = conn2.recv(1024)
            if not temp:
                break
            reply += temp

        conn.send(reply)
        conn.close()
        conn2.close()
    except socket.error, (value, message):
        print "fuck didn't work 4"
        conn.close()
        sys.exit(2)


main()
