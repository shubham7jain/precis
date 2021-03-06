import os
from flask import Flask, render_template, request
import precis.textrank
import json
from flask_cors import CORS, cross_origin
from goose import Goose
from precis import textrank
from precis.html_parser import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.parsers.plaintext import PlaintextParser
import requests
import nltk
from flasgger import Swagger

application = Flask(__name__)
application.debug=True
CORS(application)

Swagger(application)
@application.route('/summary', methods=['POST'])
def index():
    """Summary API to return the summary given the text
    ---
    tags:
      - precis
    parameters:
      - name: text
        type: string
      - name: ratio
        type: float
    responses:
      200:
        description: Summary in Json format
        schema:
          id: summary
          properties:
            summary:
                type: string
    """
    try:
        if request.method == "POST":
            print request.data
            json_dict = json.loads(request.data)
            ratio = json_dict['ratio'] if 'ratio' in json_dict else 0.2
            summary = textrank.textrank(json_dict['text'], ratio)
            summary_data = {'summary':summary}
            print json.dumps(summary_data)
            return json.dumps(summary_data)
    except Exception as e:
        print e

@application.route('/summaryurl', methods=['POST'])
def summaryByUrl():
    """Summary API to return the summary given the URL of a page
    ---
    tags:
      - precis
    parameters:
      - name: URL
        type: string
      - name: ratio
        type: float
    responses:
      200:
        description: Summary in Json format
        schema:
          id: summary
          properties:
            summary:
                type: string
    """
    if request.method == "POST":
        json_dict = json.loads(request.data)
        url = json_dict['url']
        ratio = json_dict['ratio'] if 'ratio' in json_dict else 0.2
        tokenizer = Tokenizer("english")
        parser, meta = get_parser(url, tokenizer)
        all_sentences = ""
        for paragraph in parser.document.paragraphs:
            sentences = paragraph.sentences
            for sentence in sentences:
                all_sentences += str(sentence)
            all_sentences += "\n"
        print all_sentences
        print meta
        summary = textrank.textrank(all_sentences, ratio)
        summary_data = {'summary':summary, 'meta':meta}
        print json.dumps(summary_data)
        return json.dumps(summary_data)


def get_parser(url, tokenizer):
    useragent = ' '.join([
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6)",
        "AppleWebKit/537.36 (KHTML, like Gecko)",
        "Chrome/52.0.2743.116 Safari/537.36"])

    # Scrape Web Page With HTMLParser and Goose and select the best scrape
    html_parser = HtmlParser.from_url(url, tokenizer)
    article = Goose({'browser_user_agent': useragent})

    # Goose raises IndexError when requesting unfamiliar sites.
    try:
        extract = article.extract(url=url)
    except:
        extract = article.extract(raw_html=requests.get(url).text)

    goose_parser = PlaintextParser(extract, tokenizer)

    # Aggregate Site Metadata
    meta = {
        k: v for (k, v) in extract.infos.items()
        if k not in ('cleaned_text', 'links', 'tweets', 'movies')
    }
    # Select Best Parser
    parser = (
        html_parser
        if len(goose_parser.document.words) < len(html_parser.document.words) else  # noqa
        goose_parser)

    return parser, meta

if __name__ == '__main__':
    nltk.download('punkt')
    port = int(os.environ.get("PORT", 33507))
    application.run(host='0.0.0.0', debug=True, port=port)
