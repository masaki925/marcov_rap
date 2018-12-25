APP_URL=http://localhost:5000/rap
# APP_URL=https://dj-marco.herokuapp.com/rap
QUERY=おまえの母ちゃんでべそ

test:
	curl -v -H "Accept: application/json" -H "Content-type: application/json" -X POST -d "{ \"verse\": \"$(QUERY)\" }" $(APP_URL)

build:
	docker build -t registry.heroku.com/dj-marco/web .

server:
	docker run -p 5000:5000 -e PORT=5000 registry.heroku.com/dj-marco/web:latest

push:
	docker push registry.heroku.com/dj-marco/web

# heroku_push:
# 	heroku container:push web -a dj-marco

heroku_release:
	heroku container:release web -a dj-marco

