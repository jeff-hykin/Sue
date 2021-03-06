import flask

from sue.models import Message

app = flask.current_app
bp = flask.Blueprint('webapis', __name__)

@bp.route('/wiki')
def wiki():
    """!wiki <... topic ...>"""
    import wikipedia as wikip

    msg = Message._create_message(flask.request.form)
    searchTerm = msg.textBody

    try:
        data = wikip.summary(searchTerm,sentences=1)
        if len(data) < 50:
            data = wikip.summary(searchTerm,sentences=2)
        return str(data)
    except:
        return "Hmm, couldn't find that..."

@bp.route('/wikis')
def wikis():
    """!wiki <... topic ...> , <... search filter ...>"""
    import wikipedia as wikip
    msg = Message._create_message(flask.request.form)
    searchTerm = msg.textBody.split(',',1)

    if len(searchTerm) != 2:
        return ('Please separate the topic and search term with a comma.\
        \nEx: !wikis george washington, was born')

    from nltk.tokenize import sent_tokenize
    searchTerm = [x.lower().strip() for x in searchTerm]
    data = sent_tokenize(wikip.page(searchTerm[0]).content)
    data = [x for x in data if searchTerm[1] in x.lower()]
    data = data[:10] # we don't want too many sentences.
    if len(data) == 0:
        return 'No sentences match that...'
    for sent in data:
        return str(sent)

@bp.route('/wolf')
def wolf():
    """!wolf <... question ...>"""
    import wolframalpha

    responses = []

    msg = Message._create_message(flask.request.form)
    inputQuestion = msg.textBody

    client = wolframalpha.Client('HWP8QY-EL2KR2KKLW')

    res = client.query(inputQuestion)

    interp = [pod for pod in res.pods if pod['@title'] == 'Input interpretation']
    results = [pod for pod in res.pods if pod['@title'] == 'Result']

    # TODO: "integral of sigmoid function" returns empty interp and results.
    #       there are more things that still need extraction.

    if interp:
        responses.append('Input:')
        for item in interp:
            try:
                print(item['subpod']['img']['@alt'])
            except:
                pass # didn't have the right keys.
        responses.append('\nResult:')

    # TODO: if results is empty, the answer was in image form. extract that.
    for res in results:
        try:
            responses.append(res['subpod']['img']['@alt'])
        except:
            pass # didn't have the right keys.
    
    return responses

@bp.route('/ud')
def urbanDictionary():
    """!ud <... term ...>"""
    import sys
    import json
    import requests

    msg = Message._create_message(flask.request.form)
    term = msg.textBody

    responses = []

    if term:
        if sys.version < '3':
            from urllib import quote as urlquote
        else:
            from urllib.parse import quote as urlquote
        url = 'http://api.urbandictionary.com/v0/define?term=' + urlquote(term)
    else:
        # no term provided. Send a random one.
        url = 'http://api.urbandictionary.com/v0/random'

    r = requests.get(url)
    data = json.loads(r.content)
    if not data['list']:
        return ["Sorry, couldn't find that..."]
    
    clean = lambda x: x.replace('\r\n', '\n').strip()
    for entry in data['list'][:1]:
        responses.append(str(data['list'][0]['word']))
        output = 'def: ' + clean(entry['definition']) + '\n'
        output += 'ex: ' + clean(entry['example'])
        responses.append(str(output))
    
    return responses

@bp.route('/img')
def searchImage():
    """!img <... query ...>"""
    # use imgur's API to return the link to the first non-album result.
    from json import loads
    import random

    import requests

    msg = Message._create_message(flask.request.form)
    searchText = msg.textBody

    url = "https://api.imgur.com/3/gallery/search/{{sort}}/{{window}}/{{page}}"
    querystring = {"q":searchText}
    headers = {'authorization': 'Client-ID 01aa1688f43ca6c'}
    response = requests.request("GET", url, headers=headers, params=querystring)

    a = loads(response.text)['data']
    # a = filter(lambda x: 'imgur.com/a/' not in x['link'], a)

    if len(a) > 0:
        # imageUrl = a[0]['link']
        # return random.choice(a)['link']
        try:
            return random.choice(a)['link']
        except:
            # there was an error finding a link key in the item's dict.
            return "Sorry, I couldn't find a photo of that..."
    else:
        return "Sorry, I couldn't find a photo of that..."