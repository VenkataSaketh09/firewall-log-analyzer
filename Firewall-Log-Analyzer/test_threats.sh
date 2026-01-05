#!/bin/bash

API_KEY="WRx7nN_Nfj18W6B56XAkbejUDWQ9ChcNJIh65JM5VRs"
BASE_URL="http://localhost:8000"

echo "Generating Brute Force attack..."
curl -X POST ${BASE_URL}/api/logs/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "logs": [
      "Jan  1 10:00:00 hostname sshd[12345]: Failed password for admin from 192.168.1.100 port 54321 ssh2",
      "Jan  1 10:01:00 hostname sshd[12346]: Failed password for admin from 192.168.1.100 port 54321 ssh2",
      "Jan  1 10:02:00 hostname sshd[12347]: Failed password for admin from 192.168.1.100 port 54321 ssh2",
      "Jan  1 10:03:00 hostname sshd[12348]: Failed password for admin from 192.168.1.100 port 54321 ssh2",
      "Jan  1 10:04:00 hostname sshd[12349]: Failed password for admin from 192.168.1.100 port 54321 ssh2"
    ],
    "log_source": "auth.log"
  }'

echo -e "\n\nGenerating Port Scan..."
curl -X POST ${BASE_URL}/api/logs/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "logs": [
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=22",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=80",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=443",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=21",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=25",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=53",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=110",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=143",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=993",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=3306",
      "[UFW AUDIT] IN=eth0 OUT= SRC=192.168.1.200 DST=192.168.1.10 PROTO=TCP DPT=5432"
    ],
    "log_source": "ufw.log"
  }'

echo -e "\n\nDone! Check the Threats page in a few seconds."