myTask Help:
    myTask是一个简单的任务定时管理器，主要用于管理一些Pythone的每日任务。
    myTask用户命令:
        ./myTask.py install -- 初始化安装myTask
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

