import { useState } from 'react'
import { API_BASE } from './socket'

export default function Lobby({ onJoin, error }) {
  const [name, setName] = useState('')
  const [code, setCode] = useState('')

  async function createGame() {
    if (!name) return
    const res = await fetch(`${API_BASE}/games`, { method: 'POST' })
    const data = await res.json()
    onJoin(data.game_id, name)
  }

  function joinExisting() {
    if (!name || !code) return
    onJoin(code.trim(), name)
  }

  return (
    <div style={{ padding: 40, fontFamily: 'sans-serif', maxWidth: 420 }}>
      <h1>♠ Poker Friends</h1>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}

      <div style={{ margin: '20px 0' }}>
        <input
          placeholder="Your name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          style={{ padding: 8, width: '100%' }}
        />
      </div>

      <button onClick={createGame} style={{ padding: '10px 16px' }}>
        Create New Game
      </button>

      <hr style={{ margin: '24px 0' }} />

      <div style={{ display: 'flex', gap: 8 }}>
        <input
          placeholder="Game code"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          style={{ padding: 8, flex: 1 }}
        />
        <button onClick={joinExisting} style={{ padding: '8px 16px' }}>
          Join
        </button>
      </div>
    </div>
  )
}
