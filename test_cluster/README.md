Spark Standalone Test Cluster
=============================

This directory provides all required components to setup a test cluster with
MobileInsight and Spark in Standalone mode. This is useful for verify workload
partitioning in Spark.

Dependencies
------------

One of the following set of dependencies is needed on the host system

- `Docker` or `Podman`
- `Docker Compose` or `Podman Compose`

Setting up the Cluster
----------------------

To setup the cluster, follow the instructions listed below:

```bash
# Edit default settings
#
# It is *highly recommended* to set BUILD_MAX_THREADS to the number of
# available cores
#
# MacOS users should set HOME to "/user"
$ emacs .env

# Start docker-compose for the first time
$ docker-compose up -d

# Later runs can reuse built images
$ docker-compose start

# Stop the running Spark test cluster
$ docker-compose stop

# Cleanup any existing containers and images
# Useful if you don't need the test cluster again
$ docker-compose down
```

Contribution Guidelines
-----------------------

Please try to keep the `Dockerfile` compatible with both arm64 and amd64
architectures.

Please also keep the `docker-compose.yml` compatible with both `docker-compose`
and `podman-compose` syntax.
