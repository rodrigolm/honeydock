# HoneyDock
An architecture for honeypot based on Docker

## ELK 6.2.4

### Requirements

* [Docker](https://docs.docker.com/v17.09/engine/installation/linux/docker-ce/ubuntu/)
* [Docker Compose](https://docs.docker.com/compose/install/#install-compose)

### Docker Images

* [Elasticsearch](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)
* [Logstach](https://www.elastic.co/guide/en/logstash/current/docker.html)
* [Kibana](https://www.elastic.co/guide/en/kibana/current/docker.html)

```bash
docker pull docker.elastic.co/logstash/logstash-oss:6.2.4
docker pull docker.elastic.co/elasticsearch/elasticsearch-oss:6.2.4
docker pull docker.elastic.co/kibana/kibana-oss:6.2.4
```

### Configuration

If you use linux you have to configure a [virtual memory](https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html) to use the elasticsearch
```bash
echo vm.max_map_count=262144 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
```

If you need to set a specific configuration for ELK, you can add environment variables in the docker composition file or create an .yml file and uncomment the volume configuration line
> ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
> ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml
> ./kibana/config/kibana.yml:/usr/share/kibana/config/kibana.yml

#### Logstash

You should use [grok plugin](https://www.elastic.co/guide/en/logstash/current/plugins-filters-grok.html) to create a custom [patterns](https://github.com/Alissonrgs/honeydock/tree/master/elk/logstash/patterns) file and configure the [pipeline](https://github.com/Alissonrgs/honeydock/tree/master/elk/logstash/pipeline/pipeline.conf) to parse your log

#### Kibana

You can create some visualizations and dashboards or import the [default](https://github.com/Alissonrgs/honeydock/tree/master/elk/kibana/exports)

## Honeypot

TODO

### Requirements

* [Docker](https://docs.docker.com/v17.09/engine/installation/linux/docker-ce/ubuntu/)
* Install the honeydock python requirements

### Docker Images

* [Logspout](https://github.com/gliderlabs/logspout)
* [Cowrie](https://github.com/micheloosterhof/cowrie)
```bash
docker pull gliderlabs/logspout:latest
docker pull cowrie/cowrie
```

### Configuration

#### Cowrie

TODO