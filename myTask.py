#! /usr/bin/python3
#-*-coding:utf-8-*-

import os
import sys
import time
import datetime
import pymysql
import config

helpstr = \
"""
myTask Help:
    myTask是一个简单的任务定时管理器，主要用于管理一些Pythone的每日任务。
    myTask用户命令:
        ./myTask.py install -- 初始化安装myTask(注:需要root权限执行)
        ./myTask.py update -- 更新变动的任务列表到crontab(注:需要root权限执行)
        ./myTask.py add [(name filename args runtime)/(args)] -- 添加任务
            例如添加name=helloworld filename=/usr/bin/python3 args=/root/helloworld.py runtime=00:00有以下三种方法
            1: ./myTask.py add helloworld /usr/bin/python3 /root/helloworld.py 00:00
            2: ./myTask.py add /root/helloworld.py  --    然后进入交互模式补全信息
            3: ./myTask.py add  --    直接进入交互模式补全信息
        ./myTask.py change -- 修改任务，直接进入交互模式补全信息
        ./myTask.py delete -- 删除任务，直接进入交互模式补全信息
        ./myTask.py help -- 显示本页帮助
    myTask crontab执行命令:
        ./myTask.py run "taskName" "filename" "args" -- 调用执行脚本，将回显保存到数据库。
 """.strip()

conn = None
cursor=None

def logout(s):
    print(s)
    with open(config.logout, "a") as out:
        out.write("[{0}] {1}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"),s))
#判断是否连接数据库
def isConnectMysql():
    return not(conn==None and cursor==None)

#连接数据库
def connectMysql():
    global conn, cursor
    if conn != None:
        closeMysql()
    if cursor != None:
        closeMysql()
    try:
        conn = pymysql.connect(host=config.dbhost,user=config.dbusername,password=config.dbpassword,database=config.dbname,charset="utf8")
        cursor = conn.cursor(cursor=pymysql.cursors.DictCursor)
        return True
    except:
        return False

#关闭连接
def closeMysql():
    global conn, cursor
    if cursor != None:
        cursor.close()
    if conn != None:
        conn.close()
    cursor = None
    conn = None

#初始化config文件
def initconfig():
    t = input("logout({0}):".format(config.logout))
    config.logout = t if t.strip() != ""else config.logout

    t = input("dbhost({0}):".format(config.dbhost))
    config.dbhost = t if t.strip() != ""else config.dbhost

    t = input("dbusername({0}):".format(config.dbusername))
    config.dbusername = t if t.strip() != ""else config.dbusername

    t = input("dbpassword({0}):".format(config.dbpassword))
    config.dbpassword = t if t.strip() != ""else config.dbpassword

    t = input("dbname({0}):".format(config.dbname))
    config.dbname = t if t.strip() != ""else config.dbname

    logout("更新config.py")
    newconfig = "#config[{4}]\ndbname=\"{0}\"\ndbhost=\"{1}\"\ndbusername=\"{2}\"\ndbpassword=\"{3}\"".format(config.dbname,config.dbhost,config.dbusername,config.dbpassword,time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(sys.path[0]+"/config.py", "w") as c:
        c.write(newconfig)

#初始化数据库
def initDatabase():
    global conn, cursor
    try:
        logout("连接数据库")
        conn = pymysql.connect(host=config.dbhost,user=config.dbusername,password=config.dbpassword,charset="utf8")
        cursor = conn.cursor()
        logout("创建数据库[{0}]".format(config.dbname))
        cursor.execute("drop database if exists {0};".format(config.dbname))
        cursor.execute("create database {0};".format(config.dbname))
        logout("进入到数据库[{0}]".format(config.dbname))
        cursor.execute("use {0};".format(config.dbname))
        logout("创建表[tasks]")
        cursor.execute("create table tasks(id int primary key auto_increment,name varchar(20) not null unique,filename varchar(100) not null default '/usr/bin/python3',args varchar(100) not null,runtime time not null);")
        logout("创建表[logout]")
        cursor.execute("create table logout(id int primary key auto_increment,name varchar(20) not null,outstr varchar(255) not null,time datetime default current_timestamp);")
        logout("创建表[changes]")
        cursor.execute("create table changes(id int primary key auto_increment,name varchar(20) not null,status tinyint not null default 0);")
        logout("关闭连接")
        cursor.close()
        conn.close()
    except:
        return False
    return True

#检查root权限
def isRoot():
    if os.popen("whoami").read().strip() != "root":
        return False
    else:
        return True

#安装本应用
def install():
    if not isRoot():
        logout("install 需要root权限执行")
        return
    initconfig()
    if not initDatabase():
        logout("数据库安装出错，请检查配置。")
        return
    with open("/etc/crontab", 'r') as cr:
        crontabs = cr.readlines()
        mainTask = "*/30 * * * * root {0} update\n".format(os.path.abspath(__file__))
        if mainTask in crontabs:
            logout("检测到安装过本应用")
        else:
            crontabs.append(mainTask)
            with open("/etc/crontab", 'w') as cw:
                cw.writelines(crontabs)
    logout("安装完成")

#更新任务列表
def updateTasks():
    if not isRoot():
        logout("update 需要root权限执行")
        return
    if not connectMysql():
        logout("数据库连接失败")
        return
    add = 0
    change = 0
    delete = 0
    cursor.execute("select id,name,status from changes where status<>3;")
    result = cursor.fetchall()
    for o in result:
        res = None
        if o["status"] != 2:
            cursor.execute("select name,filename,args,runtime from tasks where name=\"{0}\"".format(o["name"]))
            res = cursor.fetchall()[0]
            if " " in res["args"]:
                res["args"] = "\"{0}\"".format(res["args"])
            res["runtime"] = str(res["runtime"]).split(':')
        with open('/etc/crontab','r') as cr:
            crontab = cr.readlines()
            if o['status'] == 0:
                #新增任务
                crontab.append("#myTask[{0}]\n".format(o["name"]))
                crontab.append("{1} {0} * * * root {2} run {5} {3} {4}\n".format(res["runtime"][0],res["runtime"][1],os.path.abspath(__file__),res["filename"],res["args"],o["name"]))
                cursor.execute("update changes set status=3 where id={0}".format(o["id"]))
                cursor.fetchall()
                conn.commit()
                add = add + 1
            elif o['status'] == 1:
                #修改任务
                x = crontab.index("#myTask[{0}]\n".format(o["name"]))
                crontab[x+1] = "{1} {0} * * * root {2} run {5} {3} {4}\n".format(res["runtime"][0],res["runtime"][1],os.path.abspath(__file__),res["filename"],res["args"],o["name"])
                cursor.execute("update changes set status=3 where id={0}".format(o["id"]))
                cursor.fetchall()
                conn.commit()
                change = change + 1
            elif o['status'] == 2:
                #删除任务
                x = crontab.index("#myTask[{0}]\n".format(o["name"]))
                crontab.pop(x)
                crontab.pop(x)
                cursor.execute("update changes set status=3 where id={0}".format(o["id"]))
                cursor.fetchall()
                conn.commit()
                delete = delete + 1
            else:
                logout("数据有误")
            with open('/etc/crontab', 'w') as cw:
                cw.writelines(crontab)
    logout("更新完成，新增{0}个任务，修改{1}个任务，删除{2}个任务".format(add,change,delete))
    closeMysql()

#运行命令并保存回显
def run():
    cmd = sys.argv[3] + " " + sys.argv[4]
    log = os.popen(cmd).read().strip().replace("\n","\\n").replace("\r","\\r").replace("\'","\\'").replace("\"","\\\"")
    if not connectMysql():
        logout("数据库连接失败")
        return
    cursor.execute("insert into logout(name,outstr) values(\"{0}\",\"{1}\")".format(sys.argv[2],log))
    logout("run {0}".format(sys.argv[2]))
    conn.commit()
    closeMysql()

def add():
    if len(sys.argv) > 3 and len(sys.argv) != 6:
        print("参数列表有误")
        return
    name = ""
    filename = "/usr/bin/python3"
    args = ".py"
    runtime = "00:00"
    if len(sys.argv) == 6:
        get = input("name={0} filename={1} args={2} runtime={3} 确定?(Y/n)".format(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])).upper().strip()
        if get!="Y".strip() and get!="YES".strip() and get!="".strip():
            print("已取消操作")
            return
        name=sys.argv[2]
        filename=sys.argv[3]
        args=sys.argv[4]
        runtime=sys.argv[5]
    else:
        name = input("name:")
        filename = input("filename(/usr/bin/python3):")
        if len(sys.argv) == 3:
            args = sys.argv[2]
        args = input("args({0}):".format(args))
        runtime = input("runtime(00:00):")
        filename = filename if filename.strip() != "" else filename
    if not connectMysql():
        logout("数据库连接失败")
        return
    runtime = runtime.split(':')
    runtime = str(runtime[0]).zfill(2)+str(runtime[1]).zfill(2)+"00"
    cursor.execute("insert into tasks(name,filename,args,runtime) values(\"{0}\",\"{1}\",\"{2}\",{3})".format(name,filename,args,runtime))
    cursor.execute("insert into changes(name) values(\"{0}\")".format(name))
    conn.commit()
    closeMysql()
    logout("成功添加任务[{0}]到变更队列 需再次运行sudo ./myTask.py update 更新任务(30分钟自动执行一次)".format(name)) 

#任务列表
def listTask():
    if not connectMysql():
        logout("数据库连接失败")
        return
    cursor.execute("select * from tasks;")
    res = cursor.fetchall()
    if len(res) == 0:
        print("没有任务")
    else:
        print("任务列表\nid  name  command  runtime")
        for t in res:
            print("{0}  {1}  {2}  {3}".format(t["id"],t["name"],t["filename"]+" "+t["args"],t["runtime"]))
    closeMysql()

#删除任务
def deleteTask():
    listTask()
    if not connectMysql():
        logout("数据库连接失败")
        return
    id = input("需删除任务id:").strip()
    if id.strip()!="".strip():
        cursor.execute("select * from tasks where id={0}".format(id))
        res = cursor.fetchall()
        if len(res) == 0:
            print("未查找到该id")
        else:
            get = input("确定删除{0}?(Y/n)".format(res[0]["name"])).upper().strip()
            if get!="Y".strip() and get!="YES".strip() and get!="".strip():
                print("已取消操作")
            else:
                cursor.execute("delete from tasks where id={0}".format(id))
                cursor.execute("insert into changes(name,status) values(\"{0}\",2)".format(res[0]["name"]))
                logout("成功添加任务[{0}]到变更队列 需再次运行sudo ./myTask.py update 更新任务(30分钟自动执行一次)".format(res[0]["name"])) 
    else:
            print("非法id")
    conn.commit()
    closeMysql()

#修改任务
def changes():
    listTask()
    if not connectMysql():
        logout("数据库连接失败")
        return
    id = input("需修改任务id:").strip()
    if id.strip()!="".strip():
        cursor.execute("select * from tasks where id={0}".format(id))
        res = cursor.fetchall()
        if len(res) == 0:
            print("未查找到该id")
        else:
            task = res[0]
            name=input("name({0}):".format(task["name"]))
            filename=input("filename({0}):".format(task["filename"]))
            args=input("args({0}):".format(task["args"]))
            runtime=input("runtime({0}):".format(str(task["runtime"]).split(':')[0]+":"+str(task["runtime"]).split(':')[1]))
            name = name if name.strip()!="" else task["name"]
            filename = filename if filename.strip()!="" else task["filename"]
            args = args if args.strip()!="" else task["args"]
            runtime = runtime if runtime.strip()!="" else runtime["name"]
            runtime = runtime.split(':')
            runtime = runtime[0].zfill(2)+runtime[1].zfill(2)+"00"
            args = "'{0}'".format(args) if " " in args else args
            cursor.execute("update tasks set name=\"{0}\",filename=\"{1}\",args=\"{2}\",runtime={3}".format(name,filename,args,runtime))
            cursor.execute("insert into changes(name,status) values(\"{0}\",1)".format(name))
    else:
        print("非法id")
    conn.commit()
    closeMysql()

#打印帮助信息
def help():
    print(helpstr)

if "install" in sys.argv:
    install()
elif "run" in sys.argv:
    run()
elif "update" in sys.argv:
    updateTasks()
elif "help" in sys.argv:
    help()
elif "add" in sys.argv:
    add()
elif "list" in sys.argv:
    listTask()
elif "delete" in sys.argv:
    deleteTask()
elif "change" in sys.argv:
    changes()
else:
    logout("nothing to do!")
