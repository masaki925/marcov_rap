# APP_URL=http://localhost:5000/rap
APP_URL=https://salty-chamber-85775.herokuapp.com/rap
QUERY=おまえの母ちゃんでべそ

curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d '{ "verse": "おまえの母ちゃんでべそ" }' ${APP_URL}


