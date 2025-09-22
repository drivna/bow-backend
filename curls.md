# Register User
curl --location 'http://127.0.0.1:4000/users/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "user_name":"kamran",
    "email":"mk@gmail.com",
    "password":"admin"
}'

curl http://localhost:6333/collections/pdf_chunks
curl -X POST "http://localhost:6333/collections/pdf_chunks/points/scroll" \
  -H 'Content-Type: application/json' \
  -d '{
    "limit": 5
  }'
