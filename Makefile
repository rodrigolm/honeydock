up:
	docker-compose up

down:
	docker-compose down

bash-filebeat:
	docker exec -it honeydock-filebeat /bin/bash

up-honeypot:
	docker run --rm -it --log-driver syslog -p 2222:22 --name honeypot rodrigolm/honeydock-ssh

clean:
	docker stop $$(docker ps -aq); docker rm $$(docker ps -aq); docker rmi $$(docker images -f dangling=true -q)