import { useEffect, useState } from 'react'
import { socket } from './socket'
import Lobby from './Lobby'
import Table from './Table'

export default function App() {
  const [playerId, setPlayerId] = useState('')
  const [gameId, setGameId] = useState('')
  const [gameState, setGameState] = useState(null)
  const [joined, setJoined] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    function onState(state) {
      setGameState(state)
    }
    function onError(err) {
      setError(err.message)
      setTimeout(() => setError(''), 3000)
    }
    socket.on('game_state', onState)
    socket.on('error', onError)
    return () => {
      socket.off('game_state', onState)
      socket.off('error', onError)
    }
  }, [])

  function joinGame(id, name) {
    setGameId(id)
    setPlayerId(name)
    if (!socket.connected) socket.connect()
    socket.emit('join_game', { game_id: id, player_id: name })
    setJoined(true)
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
    />
  )
}
