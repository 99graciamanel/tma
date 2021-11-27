#!/bin/bash

# Clean opened dockers
./dockerclean.sh

# Get interface to record in
interfaces=($(python3 scripts/list_interfaces.py))
echo "Select interface:"
select opt in "${interfaces[@]}"
do
  echo $opt
  interface=$opt
  break
done

# Select collector address
read -p 'Collector address: ' collector_address

config_filename=sflow-compose-config-$interface-$collector_address.yml
# TODO: Check if file exists
cp sflow-compose.yml $config_filename
sed -i "s/net-interface/$interface/" $config_filename
sed -i "s/flow-collector-address/$collector_address/" $config_filename

# Start docker
sudo docker-compose -f $config_filename up
