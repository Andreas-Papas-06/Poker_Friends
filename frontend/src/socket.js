import { io } from 'socket.io-client'

export const API_BASE = 'http://localhost:8000'

// Single shared connection. autoConnect: false so we only connect
// once the player actually joins a game.
export const socket = io(API_BASE, { autoConnect: false })
