elk-up:
	docker-compose -f elk/docker-compose.yml up -d

elk-down:
	docker-compose -f elk/docker-compose.yml down

honeypot-up:
	docker-compose -f honeypot/docker-compose.yml up -d

honeypot-down:
	docker-compose -f honeypot/docker-compose.yml down

clean:
	docker stop $$(docker ps -aq);
	docker rm $$(docker ps -aq);
	docker rmi $$(docker images -f dangling=true -q);
	docker volume rm $$(docker volume ls -f dangling=true -q)
