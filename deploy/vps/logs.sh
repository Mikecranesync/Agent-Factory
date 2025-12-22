#!/bin/bash
# Tail bot logs in real-time
# Run: ssh root@72.60.175.144 'bash -s' < deploy/vps/logs.sh

journalctl -u agent-factory-bot -f
