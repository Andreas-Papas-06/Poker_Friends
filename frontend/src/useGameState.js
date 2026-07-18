import { useEffect, useState, useCallback } from 'react'
import { socket } from './socket'

const STORAGE_KEY = 'poker'

// Owns the socket connection, game state, and all emit helpers.
// Components consume this hook and stay pure presentation — the networking
// layer here is what would carry over to a future React Native client.
export function useGameState() {
  const [playerId, setPlayerId] = useState('')
  const [gameId, setGameId] = useState('')
  const [gameState, setGameState] = useState(null)
  const [joined, setJoined] = useState(false)
  const [error, setError] = useState('')

  // stable: doesn't depend on current gameId/playerId (it sets them)
  const joinGame = useCallback((id, name) => {
    setGameId(id)
    setPlayerId(name)
    if (!socket.connected) socket.connect()
    socket.emit('join_game', { game_id: id, player_id: name })
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ gameId: id, playerId: name }))
    setJoined(true)
  }, [])

  const leaveGame = useCallback(() => {
    socket.emit('leave_game', { game_id: gameId })
    localStorage.removeItem(STORAGE_KEY)
    setJoined(false)
    setGameState(null)
    setGameId('')
    setPlayerId('')
  }, [gameId])

  const startGame = useCallback(() => {
    socket.emit('start_game', { game_id: gameId })
  }, [gameId])

  const act = useCallback((action, amount = 0) => {
    socket.emit('player_action', { game_id: gameId, action, amount })
  }, [gameId])

  // socket listeners (attached once)
  useEffect(() => {
    function onState(state) {
      setGameState(state)
    }
    function onError(err) {
      setError(err.message)
      setTimeout(() => setError(''), 3000)
      if (err.message === 'Game not found') {
        localStorage.removeItem(STORAGE_KEY)
        setJoined(false)
        setGameState(null)
      }
    }
    socket.on('game_state', onState)
    socket.on('error', onError)
    return () => {
      socket.off('game_state', onState)
      socket.off('error', onError)
    }
  }, [])

  // auto-rejoin on load if a session was saved
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return
    try {
      const { gameId: g, playerId: p } = JSON.parse(saved)
      if (g && p) joinGame(g, p)
    } catch {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [joinGame])

  return { playerId, gameId, gameState, joined, error, joinGame, leaveGame, startGame, act }
}
