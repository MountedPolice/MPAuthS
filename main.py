# MPolice auth+license server
import socket
import threading
import sys
import time
import mysql.connector

pony = True

SLEEP_TIME = 60

# TCP SET
TCP_IP = 'localhost'
TCP_PORT = 8686
SERVER_ADRESS = (TCP_IP, TCP_PORT)
BUFFER_SIZE = 1024
LISTEN = 20

# MySQL SET
MYSQL_IP = 'localhost'
MYSQL_PORT = "3306"
DATABASE = 'MainCALCDB'
MYSQL_USER = 'root'
MYSQL_PASS = '12345678'


class server:
    def __init__(self):
        self.CLIENTS = []
        self.db = dbClient(MYSQL_IP, MYSQL_PORT, DATABASE, MYSQL_USER, MYSQL_PASS)

    def start_server(self):
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind(SERVER_ADRESS)
            server_socket.listen(LISTEN)
            while pony:
                client_socket, addr = server_socket.accept()
                data = client_socket.recv(BUFFER_SIZE)  # format LICENCE-USER-APP or TYPE-USER-APP
                data = data.decode("UTF-8")
                lprint("Connection established with message " + data)
                data = data.split('-')
                if data[0] == 'LICENCE':
                    threading.Thread(target=self._licenser, args=(client_socket, data[1], data[2])).start()
                elif data[0] == 'AUTH':
                    lprint('AUTH')
                elif data[0] == 'REG':
                    lprint('REG')
            server_socket.close()
        except socket.error:
            lprint('Could not start server thread')
            sys.exit()

    def client_handler(self, client_socket):
        try:
            self._send(client_socket, 'OK')
            while pony:
                data = client_socket.recv(BUFFER_SIZE)
                if not data:
                    pass
                else:
                    lprint('Data : ' + str(data.decode("UTF-8")) + "\n")
        except socket.error:
            lprint('Client disconnected')
            self.CLIENTS.remove(client_socket)
            client_socket.close()
            sys.exit()

    def broadcast(self):
        lprint("Check clients")
        for sock in self.CLIENTS:
            try:
                self._send(sock, "OK")
            except socket.error:
                sock.close()
                self.CLIENTS.remove(sock)

    def _licenser(self, socket, user, app):
        if self.db.get_licence(user, app):
            self.CLIENTS.append(socket)
            threading.Thread(target=self.client_handler, args=(socket, )).start()
        else:
            self._send(socket, 'NO')
        sys.exit()

    def _send(self, sock, message):
        try:
            message = message.encode('utf-8')
            sock.send(message)
        except AttributeError:
            lprint("Cant send message")

a = 1

class dbClient:

    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def get_licence(self, username, app):
        lprint(username + " Checking the user license for application " + app)
        tab = self._select_fetchall('User')
        for i in tab:
            if i[1] == username and (app in i[3]):
                lprint("License ok")
                return True
        return False

    def _select_fetchall(self, table):
        try:
            conn = mysql.connector.connect(host=self.host,
                                           port=self.port,
                                           database=self.database,
                                           user=self.user,
                                           password=self.password)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM " + self.database + "." + table)
            tab = cursor.fetchall()
            cursor.close()
            conn.disconnect()
            return tab
        except mysql.connector.errors.InterfaceError:
            lprint('DB connection error')
            return []
        except:
            lprint('DB unexpected error')
            return []



def lprint(message):
    print(time.asctime() + ' ' + str(message))


if __name__ == '__main__':
    s = server()
    threading.Thread(target=s.start_server).start()
    while pony:
        s.broadcast()
        lprint('Connections: ' + str(len(s.CLIENTS)))
        try:
            time.sleep(SLEEP_TIME)
        except:
            pass