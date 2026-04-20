import socketio
import uvicorn
from fastapi import FastAPI
from backend import engine


#app = FastAPI()

sio = socketio.Server()

@sio.event
def connect(sid, environ):
    print(sid, 'connected')

@sio.event
def disconnect(sid):
    print(sid, 'disconnected')

@sio.event
def action(sid, player, action, amount=0):
    if action == 'fold':
        pass
    elif action == 'call':
        pass
    elif action == 'raise':
        pass
