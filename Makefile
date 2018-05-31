ELK_VERSION=6.2.4
LOGSTASH_HOST=$$(docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' logstash)
PROJECT_PATH=$$(pwd)


elk-up:
	docker-compose -f elk/docker-compose.yml up -d

elk-down:
	docker-compose -f elk/docker-compose.yml down

logstash:
	docker run \
		--name logstash \
		--rm \
		-e "LOGSPOUT=ignore" \
		-v $(PROJECT_PATH)/elk/logstash/pipeline/:/usr/share/logstash/pipeline/ \
		-v $(PROJECT_PATH)/elk/logstash/patterns/:/usr/share/logstash/patterns/ \
		-p 5000:5000 \
		docker.elastic.co/logstash/logstash-oss:$(ELK_VERSION)

elasticsearch:
	docker run \
		--name elasticsearch \
		--rm \
		-e "LOGSPOUT=ignore" \
		-p 9200:9200 \
		docker.elastic.co/elasticsearch/elasticsearch-oss:$(ELK_VERSION)

kibana:
	docker run \
		--name kibana \
		--rm \
		-e "LOGSPOUT=ignore" \
		-p 5601:5601 \
		docker.elastic.co/kibana/kibana-oss:$(ELK_VERSION)

logspout:
	docker run \
		--name logspout \
		--rm \
		-e "LOGSPOUT=ignore" \
		-v /var/run/docker.sock:/var/run/docker.sock \
		gliderlabs/logspout \
		syslog+tcp://$(LOGSTASH_HOST):5000

cowrie:
	docker run \
		--name cowrie \
		--rm \
		-e "DOCKER=yes" \
		-P \
		-v $(PROJECT_PATH)/honeypot/cowrie/cowrie.cfg:/cowrie/cowrie-git/cowrie.cfg \
		cowrie/cowrie

clean:
	docker stop $$(docker ps -qa)
	docker rm $$(docker ps -qa)
	docker network rm $$(docker network ls -qf type=custom)
	docker rmi $$(docker images -qf dangling=true)
	docker volume rm $$(docker volume ls -qf dangling=true)
