import { useEffect, useState } from 'react'
import { socket } from './socket'
import Lobby from './Lobby'
import Table from './Table'

const STORAGE_KEY = 'poker'

export default function App() {
  const [playerId, setPlayerId] = useState('')
  const [gameId, setGameId] = useState('')
  const [gameState, setGameState] = useState(null)
  const [joined, setJoined] = useState(false)
  const [error, setError] = useState('')

  // socket listeners
  useEffect(() => {
    function onState(state) {
      setGameState(state)
    }
    function onError(err) {
      setError(err.message)
      setTimeout(() => setError(''), 3000)
      // stale saved session (e.g. server restarted) — drop it and return to lobby
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

  // auto-rejoin on load if we saved a session
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return
    try {
      const { gameId: savedGame, playerId: savedPlayer } = JSON.parse(saved)
      if (savedGame && savedPlayer) joinGame(savedGame, savedPlayer)
    } catch {
      localStorage.removeItem(STORAGE_KEY)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function joinGame(id, name) {
    setGameId(id)
    setPlayerId(name)
    if (!socket.connected) socket.connect()
    socket.emit('join_game', { game_id: id, player_id: name })
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ gameId: id, playerId: name }))
    setJoined(true)
  }

  function leaveGame() {
    socket.emit('leave_game', { game_id: gameId })
    localStorage.removeItem(STORAGE_KEY)
    // keep the socket connected — we just leave this table and return to the lobby
    setJoined(false)
    setGameState(null)
    setGameId('')
    setPlayerId('')
  }

  if (!joined) {
    return <Lobby onJoin={joinGame} error={error} />
  }
  return (
    <Table
      gameState={gameState}
      playerId={playerId}
      gameId={gameId}
      error={error}
      onLeave={leaveGame}
    />
  )
}
