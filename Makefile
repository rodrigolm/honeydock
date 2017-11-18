up-elk:
	docker-compose -f docker-compose-elk.yml up -d

up-filebeat:
	docker-compose up -d

up-honeypot:
	docker run --rm -it -p 2222:22 --name honeypot rodrigolm/honeydock-ssh

down-elk:
	docker-compose -f docker-compose-elk.yml down

down-filebeat:
	docker-compose down

bash-filebeat:
	docker exec -it honeydock-filebeat /bin/bash

clean:
	docker stop $$(docker ps -aq); docker rm $$(docker ps -aq); docker rmi $$(docker images -f dangling=true -q)