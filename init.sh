#!/bin/bash
sudo mkdir -p /var/lib/elastiflow_es && sudo chown -R 1000:1000 /var/lib/elastiflow_es
./dockerclean.sh
sudo docker-compose up
