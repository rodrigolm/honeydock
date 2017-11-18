honeypot-build:
	docker build honeypot -t honeydock

elk-up:
	docker-compose -f docker-compose-elk.yml up

filebeat-up:
	docker-compose up

honeypot-up:
	docker run --rm -d -p 2222:22 honeydock

elk-down:
	docker-compose -f docker-compose-elk.yml down

filebeat-down:
	docker-compose down

filebeat-bash:
	docker exec -it honeydock-filebeat /bin/bash

clean:
	docker stop $$(docker ps -aq); docker rm $$(docker ps -aq); docker rmi $$(docker images -f dangling=true -q)