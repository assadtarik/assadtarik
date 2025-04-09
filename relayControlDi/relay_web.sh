[Unit]
Description=Start Relay Control Webpage

[Service]
ExecStart=/home/radxa/scripts/relayControlDi/relay_web.sh
Restart=always
User=radxa

[Install]
WantedBy=multi-user.target
