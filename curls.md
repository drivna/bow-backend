# Register User
curl --location 'http://127.0.0.1:4000/users/register' \
--header 'Content-Type: application/json' \
--data-raw '{
    "user_name":"kamran",
    "email":"mk@gmail.com",
    "password":"admin"
}'

