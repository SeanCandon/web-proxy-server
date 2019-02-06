import socket
import sys
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
    try:
        print data
        line1 = data.split('\n')[0]
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
            port  = int((rest[(port_pos+1):])[:server_pos-port_pos-1])
            webserver = rest[:port_pos]

        proxy_server(webserver, port, conn, data, addr)
    except Exception, e:
        pass


def proxy_server(webserver, port, conn, data, addr):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, PORT))
        sock.send(data)

        while True:
            reply = sock.recv(buff_size)
            if(len(reply) <= 0):
                break
            else:
                conn.send(reply)
                dar = float(len(reply))
                dar = float(dar / 1024)
                dar = "%.3s" % (str(dar))
                dar = "%s KB" % (dar)
                print "request complete: %s => %s <=" % (str(addr[0]), str(dar))

        sock.close()
        conn.close()
    except socket.error, (value, message):
        sock.close()
        conn.close()
        sys.exit(2)


main()
