docker run \
  -v $(pwd)/output:/home/schcrwlr/share \
  --rm -it \
  --entrypoint=/bin/bash \
  schemacrawler/schemacrawler


schemacrawler \
  --server=mysql \
  --database=terafarma_clone \
  --host=172.17.0.1 \
  --port=3306 \
  --user=root \
  --password=root_password \
  --command=serialize \
  --info-level=maximum \
  --title="Business Data Dictionary (Users & Orders)" \
  --output-format=json \
  --output-file="/home/schcrwlr/share/schema_dump.json"