#!/usr/bin/python3

# ========= CONTRIBUTERS ========= #
# Himanshu Rastogi <hi.himanshu14@gmail.com> --> AUTHOR
# ...?

from subprocess import call, getstatusoutput, PIPE, Popen # For terminal process handling
import sqlite3                                            # For sqlite handling
import os.path                                            # For file handling
from urllib.request import urlopen                        # To fecth new version

# GLOBAL VAIRABLE FOR COLOR
RED = "\033[91m"
WHITE = "\033[00m"
GREEN = "\033[92m"
YELLOW = "\033[93m"


class NgxManager:
    def __init__(self):
        self.ver = 0.2  # Current version
        self.updateChecking() #Check for new update
        self.currentPath = os.path.dirname(os.path.realpath(__file__)) #Settingup current path of file
        self.dbname = self.currentPath + '/db.db'   #Settingup database file with path
        print(YELLOW + "Database Location: " + self.dbname + WHITE)
        if(os.path.isfile(self.dbname)):    #Checking is Database exist or not
            print("Database Exist")
        else:
            self.createDB() # Creating Databse if not exist
        self.php = self.getPhpService() # Check available php Version 
        if(self.php is 'not found'):
            print('PHP service not found, Please install!')
        self.nginxConfig()  # configure /etc/nginx/nginx.conf
        self.phpConfig()    # configure php support for nginx

    #Choose Option
    def choose(self):
        ch = None
        while(True):
            call(['clear'])
            print(""" 
#       {}ngxManager {}v{}-pre-alpha - {}Nginx Management Tools
#       {}Github: {}https://github.com/xhimanshuz/ngxManager
#
#
#   {}I developed this project to run multiple sites in 
#   my Raspberry Pi with little efforts but you can use 
#   it for your own way. 
#   {}***Too many bugs but still working great.***{}\n""".format(GREEN, RED, self.ver, WHITE , WHITE, GREEN, YELLOW, RED, WHITE))

            print("""{}** NGINX SERVER MANAGEMENT ** {}
1. Display Servers
2. Add Server
3. Delete Server
4. Nginx Reload
5. About
6. Check Update
0. Exit
{}Enter Your Choice {}""".format(GREEN, WHITE, RED, YELLOW))
            try:
                ch = int(input("> "))
            except (ValueError, TypeError):
                print(RED + "Invalid input please try again..." + WHITE)
                input()
                continue
            if ch == 0:
                exit()
            elif ch > 6:
                print(RED + "Invalid input {} please try again...".format(ch) + WHITE)
                input()
                continue
            self.choiceOption()[ch]()
            input()
            call(['clear'])

    # Calling function according to input
    def choiceOption(self):
        return {
            1: self.displayServersDetail,
            2: self.addServer,
            3: self.deleteServer,
            4: self.nginxReload,
            5: self.about,
            6: self.updateChecking
        }

    # Configure nginx file
    def nginxConfig(self):
        with open("/etc/nginx/nginx.conf", 'r') as f:
            str = f.read()
        str = str.replace("include /etc/nginx/conf.d/*.conf;", "#include /etc/nginx/conf.d/*.conf;")
        with open("/etc/nginx/nginx.conf", "w") as f:
            f.write(str)

    # Display added server list
    def displayServers(self):
        call(['clear'])
        tuple = self.sqliteToTuple(None, "all")
        if len(tuple) is 0:
            print("EMPTY..!" + WHITE + "\nPress any key to continue...")
            return tuple
        for i, t in enumerate(tuple):
            print("{}{}. {}{}{}".format(WHITE, i+1, GREEN, t[0], WHITE))
        try:
            ch = int(input("{}Enter Your Choice: {}".format(RED, WHITE)))
        except ValueError:
            print(RED + "Invalid input, please try again." + WHITE)
            return []
        if ch > len(tuple):
            print('{}Invalid Choice!'.format(RED))
            input("Try agin!{}".format(WHITE))
        else:
            call(['clear'])
            print("You Choose: {}".format(tuple[ch-1][0]))
            tuple = self.sqliteToTuple(tuple[ch-1][0], 'one')
            return tuple

    # Display selected server detail
    def displayServersDetail(self):
        tuple = self.displayServers()
        if(len(tuple) is not 0):
            print("""{}*** Host {} Detail ***{}
Servername: {}
Port: {}
PHP Enabled: {}
Adminer Enabled: {}
{}Press Any key to continue...{}""".format(GREEN, tuple[0], YELLOW, tuple[0], tuple[1], tuple[2], tuple[3], RED, YELLOW))

    # Add server to SQL and nginx
    def addServer(self):
        print("Add Server")
        tuple = self.inputConfigData() # Add server detail
        if(tuple is ''):
            return
        self.fileMgr(tuple[0], 'add') # Configure file according server name
        self.tupleToSqlite(tuple)
        print(RED + "*** Config FIle Created ***" + WHITE)
        filedata = self.configFile(tuple)
        with open('/etc/nginx/sites-enabled/{}.conf'.format(tuple[0]), 'w+') as f:
            f.write(filedata)
        print("{}Config file generated at: {}/etc/nginx/sites-enabled/{}.conf".format(GREEN, YELLOW, tuple[0]))
        self.nginxReload()
    
    # Input Server detail
    def inputConfigData(self):
        try:
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
        except ValueError:
            print(RED + "Input Corret and each value" + WHITE)
            return ''

    # File handling
    def fileMgr(self, server, cmd):
        if cmd is 'add':
            print(call(['mkdir /var/www/{}'.format(server)], shell=True))
        else:
            print(call(['rm', '/etc/nginx/sites-enabled/{}.conf'.format(server)]))
            print(call(['rm -rf /var/www/{}'.format(server)], shell=True))

    # NDER DEVELOPMENT
    # def modifyServer(self):
    #     tuple = self.displayServers()
    #     if(len(tuple) is not 0):
    #         tuple = self.updateColumn(tuple[0])
    #         filedata = self.configFile(tuple)
    #         with open('/etc/nginx/sites-enabled/{}.conf'.format(tuple[0]), 'w+') as f:
    #             f.write(filedata)
    #         print("Writed to /etc/nginx/sites-enabled/{}.conf".format(tuple[0]))

    # Configure Nginx File
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

    # Conver sqlite data to tuple
    def sqliteToTuple(self, server, mode):
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

    # Convert Tuple to Sqlite data
    def tupleToSqlite(self, tuple):
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute("INSERT INTO ngxManager VALUES(?,?,?,?)", tuple)
        con.commit()
        con.close()

    # Reload Nginx Server
    def nginxReload(self):
        status = getstatusoutput("nginx -s reload")
        if status[0] == 127:
            print(RED + "Error: Nginx not found, try.\n" + YELLOW + "apt install nginx\n" + WHITE + status[1] + "\nPress Any Key to continue...")
            exit()
        elif status[1]:
            print(RED + "Error: " + WHITE + status[1])
            exit()
        else:
            if not status[0]:
                print(GREEN + "Succcessfully Reloaded, " + WHITE + "Press Any Key to continue...")

    # Delete Server
    def deleteServer(self):
        tuple = self.displayServers()
        if(len(tuple) is not 0):
            ch = str(input("Do you really want to delete (Y/y): "))
            if(ch == 'y' or ch == 'Y'):
                print('Delete Column: ', tuple[0])
                self.dropColumn(tuple[0])
                self.fileMgr(tuple[0], 'rm')

    # Create Sqlite database
    def createDB(self):  # DONE
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute(
            "CREATE TABLE ngxManager(servername TEXT prime key, port INT, phpEnable BOOL, adminer BOOL)")
        con.commit()
        con.close()

    # Perform Delete operation in SQLite Database
    def dropColumn(self, column):
        con = sqlite3.connect(self.dbname)
        cur = con.cursor()
        cur.execute("DELETE FROM ngxManager where servername = ?", (column,))
        con.commit()
        print(RED + "{} Deleted".format(column) + WHITE)
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

    # Configure nginx file for PHP Support
    def phpConfig(self):
        try:
            with open("/etc/nginx/conf.d/php.conf", "w+") as f:
                f.write("""location ~ \.php$ {{
	include snippets/fastcgi-php.conf;
	fastcgi_pass unix:/run/php/{}.sock;
	}}
location ~ /\.ht {{
        deny all;
         }}""".format(self.php))
        except FileNotFoundError:
            print("{}PHP not install!\nExiting... {}".format(RED, WHITE))
            exit(0)

    # Get PHP current Version if exist otherwise return 'php'
    def getPhpService(self):
        php = getstatusoutput(
            'service --status-all | grep php[5-9].[0-9]-[f]*')[1].replace("[ + ]", "").strip()
        if(php is ''):
            return "php"
        else:
            return php

    # Display about NgxManager Detail
    def about(self):
        call(['clear'])
        print(""" 
#                 {}ngxManager {}v{}-pre-alpha - {}Nginx Management Tools
#       Developer: {}Himanshu Rastogi
#       {}Email: {}hi.himanshu14@gmail.com
#       {}Github: {}https://github.com/xhimanshuz/ngxManager
#
#   {}I developed this project to run multiple sites in 
#   my Raspberry Pi with little efforts but you can use 
#   it for your own way. 
#   {}***Too many bugs but still works great.***{}""".format(GREEN, RED, self.ver, WHITE, RED, WHITE, YELLOW, WHITE, GREEN, YELLOW, RED, WHITE + "\nPress any key to continue..."))

    # Check current version on github
    def updateChecking(self):
        print(GREEN + "Cheking for update..." + WHITE)
        try:
            gitVersion = urlopen("https://raw.githubusercontent.com/xhimanshuz/ngxManager/master/.version", timeout=3).read()
            if float(gitVersion) > self.ver:
                ch = str(input(GREEN + "New Version" + YELLOW + " {}-pre-alpha " + GREEN + "available, Do you want update?" + WHITE))
                if(ch == 'y'):
                    self.updateVersion()
                else:
                    return
            else:
                print(GREEN + "This Version" + RED + " v{}-pre-alpha ".format(self.ver) + GREEN + "is latest\n" + WHITE + "Press any key to continue...")
        except:
            print(RED + "[!] Error in checking Update... Check your internet connection!" + WHITE)

    # Update latest version on github if exist
    def updateVersion(self):
        if (getstatusoutput("wget https://raw.githubusercontent.com/xhimanshuz/ngxManager/master/ngxManager.py -O ngxManager.py")[0]):
            print(RED + "[!]" + "Error in update, please check your connection" + WHITE)
        else:
            print(GREEN + "Update Successfully,{} restarting...".format(YELLOW) + WHITE)
            call(["sudo", "python3", "./ngxManager.py"])

# Check for Super User permision
user = os.getuid()  # ROOT CHECK
if user is 0:
    try:
        ngx = NgxManager()
        ngx.choose()
    except KeyboardInterrupt:
        print(YELLOW + " Interruption, Exiting...")
else:
    print("{}[!] {}ngxManager {}must run as {}root".format(
        RED, GREEN, YELLOW, RED))
    print("{}try {}sudo ./ngxManager.py".format(YELLOW, WHITE))
