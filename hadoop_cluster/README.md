How to use this hadoop cluster
==============================

1. Copy any files you want in hdfs to mnt
2. Start the docker-container with `docker-compose up -d`
3. Start a bash shell inside the namenode using `docker container exec -it hadoop_cluster-namenode-1 bash`
4. Copy `/mnt` into hdfs:
   - `hdfs dfs -mkdir /data`
   - `hfds dfs -cp /mnt/* /data`
5. Start a spark cluster, point the file paths to `hdfs://namenode:8020/data`
