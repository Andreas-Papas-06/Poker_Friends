import uvicorn
from backend.api.api import socket_app
import backend.api.sockets   
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)