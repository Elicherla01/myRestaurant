import os
import traceback
import json
import requests

from flask import Flask, request

from citieslist2 import CITIES
from messages import get_message, search_keyword

token = os.environ.get('ACCESS_TOKEN')
api_key = os.environ.get('WEATHER_API_KEY')
app = Flask(__name__)


def location_quick_reply(sender, text=None):
    if not text:
        text = get_message('location-button')
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": text,
            "quick_replies": [
                {
                    "content_type": "location",
                }
            ]
        }
    }


def send_attachment(sender, type, payload):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "attachment": {
                "type": type,
                "payload": payload,
            }
        }
    }


def send_text(sender, text):
    return {
        "recipient": {
            "id": sender
        },
        "message": {
            "text": text
        }
    }


def send_message(payload):
    requests.post('https://graph.facebook.com/v2.6/me/messages/?access_token=' + token, json=payload)


def send_weather_info(sender, **kwargs):
    latitude = kwargs.pop('latitude', None)
    longitude = kwargs.pop('longitude', None)
    city_name = kwargs.pop('city_name', None)

    if latitude and longitude:
        query = 'lat={}&lon={}'.format(latitude, longitude)
    elif city_name:
        query = 'q={}'.format(city_name.title())

    url = 'http://api.openweathermap.org/data/2.5/weather?' \
          '{}&appid={}&units={}&lang={}'.format(query,
                                                api_key,
                                                'metric',
                                                'en')

    url1 = 'http://api.openweathermap.org/data/2.5/weather?' \
          '{}&appid={}&units={}&lang={}'.format(query,
                                                api_key,
                                                'metric',
                                                'en')                                             

    r = requests.get(url1)
    response = r.json()

    print(response)

    if 'cod' in response:
        if response['cod'] != 200:
            return 'error'

    name = response['name']
    weather = response['main']
    wind = response['wind']


    temp_text = str(weather['temp'])
    temp_float = float(temp_text)
    
    elements = [{
        'title': name,
        'subtitle': 'Temperature: {} degrees'.format(str(weather['temp'])),
        'image_url': 'http://icons.iconarchive.com/icons/oxygen-icons.org/oxygen/128/Status-weather-clouds-icon.png'
        }]
    
    if temp_float > 20.00:
        elements = [{
        'title': name,
        'subtitle': 'Temperature: {} degrees'.format(str(weather['temp'])),
        'image_url': 'http://icons.iconarchive.com/icons/icons-land/weather/256/Sunny-icon.png'
        }]
    
    elif temp_float < 10.00:
        elements = [{
        'title': name,
        'subtitle': 'Temperature: {} degrees'.format(str(weather['temp'])),
        'image_url': 'http://icons.iconarchive.com/icons/oxygen-icons.org/oxygen/128/Status-weather-clouds-night-icon.png'
        }]

    
    
    for info in response['weather']:
        description = info['description'].capitalize()
        #description = "Other details"
        icon = info['icon']

        weather_data = 'Humidity: {}%\n' \
                       'Pressure: {}\n' \
                       'Wind Speed: {}'.format(weather['humidity'],
                                                          weather['pressure'],
                                                          wind['speed'])

        if 'visibility' in response:
            weather_data = '{}\n Visibility: {}'.format(weather_data, response['visibility'])

        elements.append({
            'title': description,
            'subtitle': weather_data,
            'image_url': 'http://openweathermap.org/img/w/{}.png'.format(icon)
        })

    payload = send_attachment(sender,
                              'template',
                              {
                                  "template_type": "list",
                                  "top_element_style": "large",
                                  "elements": elements,
                                  "buttons": [
                                      {
                                          "title": "Weather",
                                          "type": "postback",
                                          "payload": "do_it_again"
                                      }
                                      
                                  ]
                              })
    
    payload1 = send_attachment(sender,
                              'template',
                              {
                                 "template_type":"button",
                                 "text":"What do you want to do next?",
                                 "buttons":[
                                    {
                                        "type":"web_url",
                                        "url":"https://www.tesco.com",
                                        "title":"Show Website"
                                    },
                                    {
                                        "type":"postback",
                                        "title":"weather",
                                        "payload":"do_it_again"
                                    }
                                    ]
                                   })

    
    
    send_message(payload)
    return None


@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = json.loads(request.data.decode())
            sender = data['entry'][0]['messaging'][0]['sender']['id']

            print(data)

            if 'message' in data['entry'][0]['messaging'][0]:
                message = data['entry'][0]['messaging'][0]['message']

            if 'postback' in data['entry'][0]['messaging'][0]:
                # Action when user first enters the chat
                payload = data['entry'][0]['messaging'][0]['postback']['payload']
                if payload == 'begin_button':
                    message = send_text(sender, 'Hello, how are you? Lets start')
                    send_message(message)

                    payload = location_quick_reply(sender)
                    send_message(payload)

                    return 'Ok'

                # Resend the location button
                if payload == 'do_it_again':
                    payload = location_quick_reply(sender)
                    send_message(payload)


            if 'attachments' in message:
                if 'payload' in message['attachments'][0]:
                    if 'coordinates' in message['attachments'][0]['payload']:
                        location = message['attachments'][0]['payload']['coordinates']
                        latitude = location['lat']
                        longitude = location['long']

                        send_weather_info(sender, latitude=latitude, longitude=longitude)

                        if _return == 'error':
                            message = send_text(sender, get_message('error'))
                            send_message(message)
                        
                            payload = location_quick_reply(sender)
                            send_message(payload)
            else:
                text = message['text']

                for city in CITIES:
                    if text.lower() in city:
                        _return = send_weather_info(sender, city_name=text)

                        if _return == 'error':
                            message = send_text(sender, get_message('error'))
                            send_message(message)

                            # Send location button
                            payload = location_quick_reply(sender)
                            send_message(payload)

                        return 'Ok'

                # If text not in city list...
                chat_message = search_keyword(text)

                if chat_message:
                    # if found keyword, reply with chat stuff
                    message = send_text(sender, get_message('greetings'))
                    send_message(message)
                else:
                    message = send_text(sender, get_message('greetings'))
                    send_message(message)
                    
                    #message = send_text(sender, get_message('not-a-city'))
                    #send_message(message)

                # Send location button
                payload = location_quick_reply(sender)
                send_message(payload)
        except Exception as e:
            print(traceback.format_exc())
    elif request.method == 'GET':
        if request.args.get('hub.verify_token') == os.environ.get('VERIFY_TOKEN'):
            return request.args.get('hub.challenge')
        return "Wrong Verify Token"
    return "Nothing"

if __name__ == '__main__':
    app.run(debug=True)
