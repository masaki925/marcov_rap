import os
import json

from flask import Flask, request

from GenerateText import GenerateText

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello world! 2'

@app.route('/rap', methods=['POST'])
def rap():
    generator = GenerateText()
    if request.form:
        verse = request.form['verse']
    elif request.data:
        jsons = str(request.data, encoding='utf-8')
        data = json.loads(jsons)
        verse = data['verse']

    gen_txt = generator.generate(verse)
    return gen_txt

if __name__ == '__main__':
    app.run(host='0.0.0.0')
