up:
	docker-compose up

down:
	docker-compose down

bash-filebeat:
	docker exec -it honeydock-filebeat /bin/bash

up-ubuntu:
	docker run --rm -it -v honeydock_logdata:/var/log/ ubuntu /bin/bash

clean:
	docker stop $$(docker ps -aq); docker rm $$(docker ps -aq); docker rmi $$(docker images -f dangling=true -q)