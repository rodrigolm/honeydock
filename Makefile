elk-up:
	docker-compose -f elk/docker-compose.yml up -d

cowrie-up:
	docker run --rm -d -P -v $$(pwd)/honeypot/config/cowrie.cfg:/cowrie-git/cowrie.cfg:shared cowrie/cowrie

clean:
	docker stop $$(docker ps -aq); docker rm $$(docker ps -aq); docker rmi $$(docker images -f dangling=true -q)