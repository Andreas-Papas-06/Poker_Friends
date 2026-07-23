import { useState } from 'react'
import { API_BASE } from './socket'
import CreateGameSettings from './components/CreateGameSettings'

export default function Lobby({ onJoin, error }) {
  const [showSettings, setShowSettings] = useState(false)
  const [name, setName] = useState('')
  const [code, setCode] = useState('')
  const [busy, setBusy] = useState(false)

  async function createGame(settings) {         
    if (busy) return
    setBusy(true)
    const params = new URLSearchParams({
      sb: settings.sb, bb: settings.bb,
      starting_stack: settings.startingStack,
      rebuy: settings.rebuy, style: settings.style,
      blind_increase: settings.blindIncrease,
    })
    try {
      const res = await fetch(`${API_BASE}/games?${params}`, { method: 'POST' })
      const data = await res.json()
      onJoin(data.game_id, name.trim())          
    } catch { setBusy(false) }
  }

  function joinExisting() {
    if (!name.trim() || !code.trim()) return
    onJoin(code.trim(), name.trim())
  }

  return (
    <div className="lobby">
      <div className="header-bar">
        <img src="media/pf_logo_v1.svg"></img>
      </div>
      <div className="lobby-card">
        <h1 className="lobby-title">♠ Poker Friends</h1>

        {error && <div className="error-toast">{error}</div>}

        <label className="field-label">Your name</label>
        <input
          className="text-input"
          placeholder="Enter Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <button
          className="btn-primary btn-block"
          onClick={() => setShowSettings(true)}
          disabled={!name.trim() || busy}
        >
          {busy ? 'Creating…' : 'Create New Game'}
        </button>

        <div className="lobby-divider">
          <span>or join with a code</span>
        </div>

        <div className="join-row">
          <input
            className="text-input"
            placeholder="Game code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
          />
          <button
            className="btn-secondary"
            onClick={joinExisting}
            disabled={!name.trim() || !code.trim()}
          >
            Join
          </button>
        </div>
      </div>
      {showSettings && (<CreateGameSettings onClose={() => setShowSettings(false)} onCreate={createGame} playerName={name}/>)}
    </div>
  )
}
