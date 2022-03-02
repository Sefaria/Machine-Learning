cd corpus
gsutil cp "gs://sefaria-mongo-backup/private_dump_small_$(date +'%d.%m.%y').tar.gz" dump_small.tar.gz
tar xzvf dump_small.tar.gz
mongorestore --drop
sudo systemctl restart mongod
