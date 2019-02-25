import socket
import sys
import _thread
import tkinter as tk
from tkinter import *
import time

# default port number and buffer size
PORT = 8080
buff_size = 4096

# hash maps for the priority cache and blocked urls,
# along with control global variables
CACHE = {}
PRIORITY = {}
MAX_CACHE_SIZE = 3
CURRENT_CACHE_SIZE = 0
BLOCKED = {}
TIME = {}


def main():
    '''main function. Runs thread for management console, binds new socket
    to port and waits for a connection from client. When a connection
    is made it receives client's request and the starts a new thread to deal
    with it. Function constantly loops, waiting for new connections'''
    try:
        _thread.start_new_thread(console, ())
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', PORT))
        sock.listen(10)
    except Exception:
        sys.exit(0)

    # infinite loop, waiting for new connections
    while 1:
        try:
            conn, addr = sock.accept()
            data = conn.recv(buff_size)  # request received
            start = time.time()  # variable to calculate time elapsed
            bandwidth = len(data)  # variable to calculate total bandwidth
            # here, a new thread is started that will call function
            # proxy_server
            _thread.start_new_thread(proxy_server, (conn, data, addr, start, bandwidth))
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    sock.close()


def proxy_server(conn, data, addr, start, bandwidth):
    '''master function. Firstly it calls parse_request to parse the request, then
    determines if the url has been blocked. If not, then depending on whether or
    not the request is HTTP or HTTPS, it will call proxy_server_http or
    proxy_server_https'''
    https, webserver, port, url = parse_request(data)
    if port != 0:
        b = BLOCKED.get(url)
        REQUESTS.insert(END, url)
        bw = 0
        if b != 1:
            if https is False:
                bw = proxy_server_http(webserver, port, conn, data, addr, url, bandwidth)
            else:
                proxy_server_https(webserver, port, conn, addr)
        else:
            print("sorry that url is blocked")
            conn.close()
        end = time.time()
        if https is False:
            print("time elapsed = " + str(end-start) + " seconds")
            print("total bandwidth = " + str(bw) + " bytes")
    else:
        conn.close()


def proxy_server_http(webserver, port, conn, data, addr, url, bandwidth):
    '''function to handle http requests. Will check if the url has been
    cached. If yes, then it creates an if-modified message and passes that
    into send_and_cache, which handles http communication and caching. If no,
    then the initial request is passed into send_and_cache'''
    try:
        b = 0
        x = CACHE.get(url)
        if x is not None:
            print("in cache")
            # here the previous time is retrieved from the cache and an
            # if-modified is added to the initial request.
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

            bandwidth += len(message.encode())
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.connect((webserver, port))
            b = send_and_cache(s2, message.encode(), url, conn, bandwidth)

        else:
            print(url + " not in cache")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((webserver, port))
            b = send_and_cache(sock, data, url, conn, bandwidth)

        conn.close()
        return b  # new bandwidth value is returned
    except socket.error:
        sock.close()
        conn.close()
        sys.exit(2)


def proxy_server_https(webserver, port, conn, addr):
    '''function to handle https. It first sends a HTTP/1.0 200 Connection
    established to the client, and then enters a loop that will only exit
    when the connection closes. In the loop it will pass encrypted data
    between the client and web server.'''
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((webserver, port))

        sock.setblocking(0)
        conn.setblocking(0)

        conn.sendall("HTTP/1.0 200 Connection established\r\nProxy-Agent: Pyx\r\n\r\n".encode())

        # loop to pass encrypted data between client and web server.
        while 1:
            # retrieve data from client and pass it onto web server
            try:
                reply1 = conn.recv(buff_size)
                if ((not reply1) or (len(reply1) <= 0)):
                    break
                sock.sendall(reply1)
            except socket.error:
                pass

            # retrieve data from web server and pass it onto client
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
    '''
    function that parses a client's request. It determines whether or not it's a
    http or https request, then parses the request for the url, hostname, and
    port number.'''
    try:
        https = False

        lines = request.decode().split("\r\n")
        # if "GET" is found, we know it's http, not https
        get = lines[0].find("GET")
        if get == -1:
            https = True

        # get url from request
        url = "https://"
        url1 = lines[0].split(' ')[1]
        url += url1.split(':')[0]
        url += "/"

        # get hostname from request
        host = ""
        for l in lines:
            h = l.find("Host")
            if h != -1:
                host = l
                break
        webserver = host.split(": ")[1]
        port_pos = webserver.find(":")
        webserver2 = ""
        i = 0
        if port_pos != -1:
            while i < port_pos:
                webserver2 += webserver[i]
                i += 1
        else:
            webserver2 = webserver

        # if a https connection use port 443, otherwise use port 80
        if https is True:
            port = 443
        else:
            port = 80

        if https:
            return https, webserver2, port, url
        else:
            return https, webserver2, port, url1
    except Exception:
        pass
        return True, 0, 0, ""


def console():
    '''
    function to handle the management console. Two buttons and two Text entries
    are created. If the BLOCK button is clicked, the string from the block
    entry is retrieved and put into the BLOCKED cache. If UNBLOCK is clicked,
    then the inputted string is popped from the BLOCKED cache, if it's already
    present'''
    console = tk.Tk()
    console.geometry("500x500")
    # create text entries
    block_input = Entry(console)
    block_input.grid(row=0, column=0)
    unblock_input = Entry(console)
    unblock_input.grid(row=1, column=0)

    # function called if BLOCKED is clicked
    def callback1():
        e = block_input.get() + "/"
        b = BLOCKED.get(e)
        if b is None:
            BLOCKED[e] = 1
            print(e + " blocked")
        else:
            print("already blocked")

    # function called if UNBLOCK is clicked
    def callback2():
        e = unblock_input.get() + "/"
        b = BLOCKED.get(e)
        if b is not None:
            BLOCKED.pop(e)
            print("unblocked")
        else:
            print("not blocked")

    # buttons created
    block = Button(console, text = "BLOCK", command=callback1)
    block.grid(row=0, column=1)
    block = Button(console, text = "UNBLOCK", command=callback2)
    block.grid(row=1, column=1)

    global REQUESTS
    REQUESTS = Listbox(console)
    REQUESTS.grid(row=2, columnspan=2)
    REQUESTS.config(width=50, height=50)
    # calling mainloop() runs console
    mainloop()


def get_time(response):
    '''
    function to retrieve the day, date, and time from a response from a web
    server. This is necessary for later using this information in an if-Modified
    request. This function looks for the string "Date" in the response and then
    returns the next 30 characters.'''
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


def send_and_cache(sock, data, url, conn, bandwidth):
    '''
    function to handle http connections including caching. It first sends the
    get request (perhaps containing an if-modified) and receives the first chunk
    of data back. It then checks this chunk for a "200 OK" (by calling the boolean
    function is-modified). If found, then it waits to receive the entirety of the
    response and sends that back to the client, while also updating the cache. If
    the data hasn't been modified however, the function doesn't wait for the rest
    of the response, and instead retrieves the data from the cache and sends that.
    '''
    sock.send(data)

    sock.settimeout(2)

    reply = bytearray("", 'utf-8')
    count = 0
    modified = False
    try:
        while 1:
            temp = sock.recv(buff_size)
            bandwidth += len(temp)
            # check first chunk to see if data has been modified
            if count == 0:
                if is_modified(temp):
                    modified = True
                else:
                    # break out of loop if data is un-modified
                    break
            if(len(temp) > 0):
                reply.extend(temp)
            else:
                break
            count += 1
    except socket.error:
        pass

    # if the data has been modified, send the new reply from the webserver and
    # cache it.
    if modified:
        conn.sendall(reply)
        bandwidth += len(reply)
        emptybefore = False
        i = CACHE.get(url)
        if i is None:
            emptybefore = True
        CACHE[url] = reply  # save new reply in cache
        time = get_time(reply)
        TIME[url] = time  # save new reply's time in cache
        global CURRENT_CACHE_SIZE
        # if cache has not yer reached maximim capacity
        if CURRENT_CACHE_SIZE < MAX_CACHE_SIZE:
            # if this url was previously not in the cache, increment cache size
            # and set url's priority to be the cache size
            if emptybefore:
                CURRENT_CACHE_SIZE += 1
                print("cache size = " + str(CURRENT_CACHE_SIZE))
                PRIORITY[CURRENT_CACHE_SIZE] = url
        # if cache is full
        else:
            # remove lowest priority url from cache
            u = PRIORITY.get(1)
            PRIORITY.pop(1)
            CACHE.pop(u)
            TIME.pop(u)
            print(u + " removed from cache")
            i = 2
            # loop to decrement other urls' priorities
            while i <= MAX_CACHE_SIZE:
                u1 = PRIORITY.get(i)
                PRIORITY.pop(i)
                PRIORITY[i-1] = u1
                i += 1
            # set new url's priority to highest priority
            PRIORITY[CURRENT_CACHE_SIZE] = url
        print("added to cache")
    # if data has not been modified, retrieve from cache and send to client
    else:
        if CACHE.get(url) is not None:
            print("retrieved from cache")
            conn.sendall(CACHE.get(url))
            bandwidth += len(CACHE.get(url))
        else:
            print("unable to retrieve from cache")
            conn.send(reply)
            bandwidth += len(reply)

    sock.close()
    return bandwidth


def is_modified(reply):
    '''function to determine whether or not data has been modified since it was
    cached. If the string "304 Not Modified" is found, we know the data has
    not been modified. Otherwise, we know that it has been.'''
    r = reply.decode()
    f = r.find("304 Not Modified")
    if f == -1:
        print("has been modified since")
        return True
    return False


main()
