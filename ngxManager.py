#!/usr/bin/python3

# ========= CONTRIBUTERS ========= #
# Himanshu Rastogi <hi.himanshu14@gmail.com> --> AUTHOR
# ...?


# GLOBAL VAIRABLE FOR COLOR
RED = "\033[91m"
WHITE = "\033[00m"
GREEN = "\033[92m"
YELLOW = "\033[93m"

from subprocess import call, getstatusoutput
import sqlite3
import os.path


class NgxManager:
    def __init__(self):
        self.dbname = 'db.db'
        if(os.path.isfile(self.dbname)):
            print("Database Exist")
        else:
            self.createDB()
        self.php = self.getPhpService()
        if(self.php is 'not found'):
            print('PHP service not found, Please install!')
        self.phpConfig()

    def choose(self):
        ch = None
        while(True):
            print("""{}** NGINX SERVER MANAGEMENT ** {}
1. Display Servers
2. Add Server
3. Delete Server
4. Nginx Reload
5. About
0. Exit
{}Enter Your Choice {}""".format(GREEN, WHITE, RED, YELLOW))
            ch = int(input("> "))
            if ch == 0:
                exit()
            self.choiceOption()[ch]()
            input()
            call(['clear'])

    def choiceOption(self):
        return {
            1: self.displayServersDetail,
            2: self.addServer,
            3: self.deleteServer,
            4: self.nginxReload,
            5: self.about
        }

    def displayServers(self):
        call(['clear'])
        tuple = self.sqliteToTuple(None, "all")
        if len(tuple) is 0:
            print("EMPTY..!")
            return tuple
        for i, t in enumerate(tuple):
            print("{}{}. {}{}{}".format(WHITE, i+1, GREEN, t[0], WHITE))
        ch = int(input("{}Enter Your Choice: {}".format(RED, WHITE)))
        if ch > len(tuple):
            print('{}Invalid Choice!'.format(RED))
            input("Try agin!{}".format(WHITE))
        else:
            call(['clear'])
            print("You Choose: {}".format(tuple[ch-1][0]))
            tuple = self.sqliteToTuple(tuple[ch-1][0], 'one')
            return tuple

    def displayServersDetail(self):
        tuple = self.displayServers()
        if(len(tuple) is not 0):
            print("""{}*** Host {} Detail ***{}
Servername: {}
Port: {}
PHP Enabled: {}
Adminer Enabled: {}
{}Press Any key to continue...{}""".format(GREEN, tuple[0], YELLOW, tuple[0], tuple[1], tuple[2], tuple[3], RED, YELLOW))

    def addServer(self):
        print("Add Server")
        tuple = self.inputConfigData()
        self.fileMgr(tuple[0], 'add')
        self.tupleToSqlite(tuple)
        print("*** Config FIle Created ***")
        filedata = self.configFile(tuple)
        with open('/etc/nginx/sites-enabled/{}.conf'.format(tuple[0]), 'w+') as f:
            f.write(filedata)
            print(
                "Writed to /etc/nginx/sites-enabled/{}.conf".format(tuple[0]))

    def inputConfigData(self):
        self.serverName = str(input("Server Name: "))
        self.port = int(input("Port: "))
        self.phpEnable = str(input("Enable Php (Y/y): "))
        if(self.phpEnable is 'Y' or self.phpEnable is 'y'):
            self.phpEnable = True
        else:
            self.phpEnable = False
        self.adminerEnable = str(input("Enable Adminer Support: "))
        if(self.adminerEnable is 'Y' or self.adminerEnable is 'y'):
            self.adminerEnable = True
        else:
            self.adminerEnable = False
        return (self.serverName, self.port, self.phpEnable, self.adminerEnable)

    def fileMgr(self, server, cmd):
        if cmd is 'add':
            print(call(['mkdir /var/www/{}'.format(server)], shell=True))
        else:
            print(call(['rm -rf {}'.format(server)], shell=True))

    # NDER DEVELOPMENT
    # def modifyServer(self):
    #     tuple = self.displayServers()
    #     if(len(tuple) is not 0):
    #         tuple = self.updateColumn(tuple[0])
    #         filedata = self.configFile(tuple)
    #         with open('/etc/nginx/sites-enabled/{}.conf'.format(tuple[0]), 'w+') as f:
    #             f.write(filedata)
    #         print("Writed to /etc/nginx/sites-enabled/{}.conf".format(tuple[0]))

    def configFile(self, tuple):
        tuple = list(tuple)
        if not tuple[2]:
            tuple[2] = '#'
        else:
            tuple[2] = " "
        configFileData = """server {{
	listen {1};
        # This is the URI of your website.
        server_name {0} *.{0};
        index index.php index.html, index.htm;
        root /var/www/{0};
        location = /favicon.ico {{
                log_not_found off;
                access_log off;
        }}

        location = /robots.txt {{
                # If you have one, you want to allow them access to it.
                allow all;
                log_not_found off;
                access_log off;
        }}
        {2}include /etc/nginx/conf.d/php.conf;
}}""".format(tuple[0], tuple[1], tuple[2])
        print(configFileData)
        return configFileData

    def sqliteToTuple(self, server, mode):
        # print("Mode: ", mode)
        if mode is "all":
            con = sqlite3.connect(self.dbname)
            cur = con.cursor()
            tuple = cur.execute("SELECT * FROM ngxManager").fetchall()
            con.close()
            return tuple
        else:
            con = sqlite3.connect(self.dbname)
            cur = con.cursor()
            cur.execute(
                "SELECT * FROM ngxManager WHERE servername=?", (server,))
            tuple = cur.fetchone()
            con.close()
            return tuple

    def tupleToSqlite(self, tuple):
        print("Tuple: ", tuple)
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute("INSERT INTO ngxManager VALUES(?,?,?,?)", tuple)
        con.commit()
        con.close()

    def nginxReload(self):
        print(call(['sudo', 'nginx', '-s', 'reload']))

    def deleteServer(self):
        tuple = self.displayServers()
        if(len(tuple) is not 0):
            ch = str(input("Do you really want to delete (Y/y): "))
            if(ch == 'y' or ch == 'Y'):
                print('Delete Column: ', tuple[0])
                self.dropColumn(tuple[0])
                self.fileMgr(tuple[0], 'rm')

    def createDB(self):  # DONE
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE ngxManager(servername TEXT prime key, port INT, phpEnable BOOL, adminer BOOL)")
        con.commit()
        con.close()

    def dropColumn(self, column):
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute("DELETE FROM ngxManager where servername = ?", (column,))
        con.commit()
        print("{} Deleted".format(column))
        con.close()
    # UNDER DEVELOPMENT
    # def updateColumn(self, column):
    #     tuple = self.inputConfigData()
    #     con = sqlite3.connect(self.dbname)
    #     cur = con.cursor()
    #     print("column: ", column)
    #     cur.execute("UPDATE ngxManager SET servername = ?, port = ?, phpEnable = ?, adminer = ? where servername = ?", (tuple[0], tuple[1], tuple[2], tuple[3], column, ))
    #     con.commit()
    #     con.close()
    #     con = sqlite3.connect(self.dbname)
    #     cur = con.cursor()
    #     print(column)
    #     cur.execute("SELECT * FROM ngxManager WHERE servername = ?", (column,))
    #     temp = cur.fetchall()
    #     cur.close()
    #     print("Update...!")
    #     print("TEMP: ", temp)
    #     return temp

    def phpConfig(self):
        with open("/etc/nginx/conf.d/php.conf", "w+") as f:
            f.write("""location ~ \.php$ {{
	include snippets/fastcgi-php.conf;
	fastcgi_pass unix:/run/php/{}.sock;
	}}
location ~ /\.ht {{
        deny all;
         }}""".format(self.php))

    def getPhpService(self):
        php = getstatusoutput(
            'service --status-all | grep php[5-9].[0-9]-[f]*')[1].replace("[ + ]", "").strip()
        if(php is ''):
            return "php"
        else:
            return php

    def about(self):
        call(['clear'])
        print(""" 
#                 {}ngxManager - {}Nginx Management Tools
#       Name: {}Himanshu Rastogi
#       {}Email: {}hi.himanshu14@gmail.com
#       {}github: {}https://github.com/xhimanshuz
#
#   {}I developed this project to run multiple sites in 
#   my Raspberry Pi with little efforts but you can use 
#   it for your own way. 
#   {}***Too many bugs because it was developed in 1 day.***{}""".format(GREEN, WHITE, RED, WHITE, YELLOW, WHITE, GREEN, YELLOW, RED, WHITE))


user = os.getuid()  # ROOT CHECK
if user is 0:
    ngx = NgxManager()
    ngx.choose()
else:
    print("{}[!] {}ngxManager {}must run as {}root".format(
        RED, GREEN, YELLOW, RED))
    print("{}try {}sudo ./ngxManager.py".format(YELLOW, WHITE))
