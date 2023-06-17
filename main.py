from flask import Flask, request
from twilio.twiml.voice_response import Gather, VoiceResponse
from twilio.rest import Client
import openai
import requests
import urllib.request
from flask import Flask, request, url_for
import random
import os

messages = []

app = Flask(__name__)

@app.route('/')
def index():
  return 'Hello I am your Saarthi'


@app.route("/call")
def call():

  args = request.args
  number = args.get("num", default="9619199593", type=str)
  
  account_sid = os.getenv('ACCOUNT_SID')
  auth_token = os.getenv('AUTH_TOKEN')
  client = Client(account_sid, auth_token)

  record_url = 'https:' + url_for("record", _external=True).split(':')[1]
  call = client.calls.create(
    to="+91" + number,  # Saurabh
    #to="+919920413760", # Mayur
    from_="+14067177408",
    #url="https://call.reetikgupta.repl.co/call"
    url=record_url
    #url="https://call.reetikgupta.repl.co/message" # Timepass
  )

  print(call.sid)

  return 'OK', 200


@app.route("/record", methods=['GET', 'POST'])
def record():
  """Returns TwiML which prompts the caller to record a message"""
  response = VoiceResponse()
  response.say('Please leave a message after the beep.')
  response.record(action='/handleRecording', finish_on_key='*')
  return str(response)


@app.route("/handleRecording", methods=['POST'])
def handleRecording():
  record_url = 'https:' + url_for("record", _external=True).split(':')[1]
  print(request.form["RecordingUrl"])
  transcription = transcribe(request.form["RecordingUrl"])
  if not transcription:
    response = VoiceResponse()
    response.redirect(record_url, method='POST')
    return str(response)
  #transcription_text = transcription["text"] + "Limit your answer to 100 words only."
  #transcription_text = transcription["text"] + ". Give me a concise answer with minimum number of words and limit it to a maximum of 100 words."
  #transcription_text = transcription["text"] + " Create a very short answer that uses 100 completion_tokens or less…"
  transcription_text = transcription["text"] + " Create a very short answer that uses a minimum of 25 completion_tokens and a maximum of 100 completion_tokens"
  print(transcription_text)
  messages.append({"role": "user", "content": transcription_text})
  print('Text given to chatgpt')
  result = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
  result_text = result['choices'][0]['message']['content']
  print('result from chatgpt')
  messages.append({
    "role": "assistant",
    "content": result_text
  })
  response = VoiceResponse()
  print(result_text)
  print('Before say')
  gather = Gather(action='/record', method='GET')
  gather.say(result_text)
  response.append(gather)
  #response.say(result_text)
  print('After say')
  response.redirect(record_url, method='POST')
  return str(response)


@app.route("/message", methods=['GET', 'POST'])
def message():
  response = VoiceResponse()
  response.say('...')
  return str(response)


def transcribe(recording_url):
  print(recording_url)

  hash = str(random.getrandbits(32))
  try:
    urllib.request.urlretrieve(recording_url, hash + ".wav")
  except:
    return None

  openai.api_key = os.getenv('OPENAI_API')

  audio_file = open(hash + ".wav", "rb")
  transcript = openai.Audio.transcribe("whisper-1", audio_file)

  os.remove(hash + ".wav")

  return transcript


if __name__ == "__main__":
  app.run(debug=True, host='0.0.0.0', port=8080)

