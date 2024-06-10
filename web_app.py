from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)
API_URL = 'http://localhost:5000'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/servers')
def servers():
    response = requests.get(f'{API_URL}/servers')
    servers = response.json()
    return render_template('servers.html', servers=servers)

@app.route('/channels/<int:server_id>')
def channels(server_id):
    response = requests.get(f'{API_URL}/channels/{server_id}')
    channels = response.json()
    return render_template('channels.html', channels=channels, server_id=server_id)

@app.route('/messages/<int:channel_id>')
def messages(channel_id):
    response = requests.get(f'{API_URL}/messages/{channel_id}')
    messages = response.json()
    return render_template('messages.html', messages=messages, channel_id=channel_id)

@app.route('/send_message/<int:channel_id>', methods=['POST'])
def send_message(channel_id):
    message = request.form['message']
    response = requests.post(f'{API_URL}/send_message', json={'channel_id': channel_id, 'message': message})
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True, port=8000)
