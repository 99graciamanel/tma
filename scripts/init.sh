#!/bin/bash
sudo mkdir -p /var/lib/elastiflow_es && sudo chown -R 1000:1000 /var/lib/elastiflow_es
./dockerclean.sh
interfaces=($(python3 scripts/list_interfaces.py))
echo "Select interface:"
select opt in "${interfaces[@]}"
do
  echo $opt
  sed "s/net-interface/$opt/" docker-compose.yml > docker-compose-configured-$opt.yml
  break
done
sudo docker-compose -f docker-compose-configured-$opt up
