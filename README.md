# work assistant

telegram bot for simplifying some work processes


## preparing to run

just copy source into some directory, change to that directory by `cd <my_dir>` and run `re-run-bot.sh`.



## run as a service

(for instructions thanks to 
[Dr. Shubham Dipt and his article](https://www.shubhamdipt.com/blog/how-to-create-a-systemd-service-in-linux/))


- create directory `/opt/work_assistant` and go into it: 
    ```bash
    mkdir /opt/work_assistant
    ```
- clone project into it
    ```bash
    git clone git@github.com:atronah/work_assistant.git work_assistant
    ```
- create and activate Python virtual environment
    ```bash
    python3 -m venv venv
    source ./venv/bin/activate
    ```
- install work_assistant
    ```bash
    pip3 install .
    ```
- create `work_assistant_bot.service` in `/etc/systemd/system` with following content:
    ```service
    [Unit]
    Description=Telegram bot to assist you in work processes (https://github.com/atronah/work_assistant)
    
    [Service]
    User=atronah
    WorkingDirectory=/opt/work_assistant
    ExecStart=/bin/bash -c 'cd /opt/work_assistant/venv/bin && source ./activate && ./work_assistant_bot'
    Restart=always
    
    [Install]
    WantedBy=multi-user.target
    ```
- restore SELinux context for new .service file
    ```bash
    sudo restorecon -v /etc/systemd/system/work_assistant_bot.service
    ```
- reload services `sudo systemctl daemon-reload`
- start service by command `sudo systemctl start work_assistant_bot`
- check status by command `sudo systemctl status work_assistant_bot`
- enable service on every reboot `sudo systemctl enable work_assistant_bot`
- edit config `/opt/work_assistant/venv/bin/conf.yaml`