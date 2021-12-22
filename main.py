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
TCP_PORT = 2549
SERVER_ADRESS = (TCP_IP, TCP_PORT)
BUFFER_SIZE = 1024
LISTEN = 20

# MySQL SET
MYSQL_IP = 'localhosy'
MYSQL_PORT = "2417"
DATABASE = 'MainCALCDB'
MYSQL_USER = 'ssapp'
MYSQL_PASS = 'pass'


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
                data = client_socket.recv(BUFFER_SIZE)
                data = data.decode("UTF-8")  # format LICENCE-USER-APP or TYPE-USER-PASSW
                lprint("Connection established with message " + data)
                data = data.split('-')
                if data[0] == 'LICENCE':
                    lprint('LICENCE')
                    threading.Thread(target=self._licenser, args=(client_socket, data[1], data[2])).start()
                elif data[0] == 'AUTH':
                    lprint('AUTH')
                    threading.Thread(target=self._auth, args=(client_socket, data[1], data[2])).start()
                elif data[0] == 'REG':
                    lprint('REG')
                    threading.Thread(target=self._register, args=(client_socket, data[1], data[2])).start()
                else:
                    lprint('ошибка запроса')
                    self._send(client_socket, 'NO')
                    client_socket.close()
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
            try:
                client_socket.close()
            except:
                lprint('MAYBE U SHOULDNT CLOSE HERE?')
            try:
                self.CLIENTS.remove(client_socket)
            except:
                lprint('ALL BAD CALL MOUNTED POLICE NOW')
            sys.exit()

    def broadcast(self):
        lprint("Check clients")
        for sock in self.CLIENTS:
            try:
                self._send(sock, "OK")
            except socket.error:
                sock.close()
                try:
                    self.CLIENTS.remove(sock)
                except:
                    lprint('ALL BAD CALL MOUNTED POLICE NOW')

    def _licenser(self, sock, user, app):
        if self.db.get_licence(user, app):
            self.CLIENTS.append(sock)
            threading.Thread(target=self.client_handler, args=(sock,)).start()
        else:
            self._send(sock, 'NO')
        sys.exit()

    def _register(self, sock, user, password):
        if self.db.hasUser(user):
            self._send(sock, "REGNO")
        else:
            self.db.reg_user(user, password)
            self._send(sock, "REGOK")
        sock.close()
        sys.exit()

    def _auth(self, sock, user, password):
        authed, permissions = self.db.get_auth(user, password)
        if authed:
            self._send(sock, permissions)
        else:
            self._send(sock, "NOAUTH")
        sock.close()
        sys.exit()

    def _send(self, sock, message):
        try:
            message = message.encode('utf-8')
            sock.send(message)
        except AttributeError:
            lprint("Cant send message")


class dbClient:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password

    def get_auth(self, username, password):
        lprint("Auth " + username + " with pass " + password)
        tab = self._select_fetchall('User')
        for i in tab:
            if i[1] == username and i[2] == password:
                if i[3] == None:
                    lprint(username + " ez Auth " + username + "with pass" + password + " permissions: 0")
                    return [True, '']
                else:
                    lprint(username + " ez Auth " + username + "with pass" + password + " permissions: " + i[3])
                    return [True, i[3]]
        return False, False

    def get_licence(self, username, app):
        lprint(username + " Checking the user license for application " + app)
        tab = self._select_fetchall('User')
        for i in tab:
            if i[3] is None:
                continue
            if i[1] == username and (app in i[3]):
                lprint("License ok")
                return True
        return False

    def reg_user(self, username, password):
        try:
            conn = mysql.connector.connect(host=self.host,
                                           port=self.port,
                                           database=self.database,
                                           user=self.user,
                                           password=self.password)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO `MainCALCDB`.`User` (`Username`, `Password`) VALUES ('"
                           + username + "', '" + password + "');")
            conn.commit()
            cursor.close()
            conn.disconnect()
        except mysql.connector.errors.InterfaceError:
            lprint('DB connection error')
            return []
        except:
            lprint('DB unexpected error')
            return []

    def hasUser(self, username):
        for i in self._get_users():
            if i[0] == username:
                return True
        return False

    def _get_users(self):
        try:
            conn = mysql.connector.connect(host=self.host,
                                           port=self.port,
                                           database=self.database,
                                           user=self.user,
                                           password=self.password)
            cursor = conn.cursor()
            cursor.execute("SELECT Username FROM " + self.database + ".User")
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
            sys.exit()

