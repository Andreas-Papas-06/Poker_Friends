import { useState } from 'react'

export default function CreateGameSettings({ onClose, onCreate, playerName }) {
  const [sb, setSb] = useState(10)
  const [bb, setBb] = useState(20)
  const [startingStack, setStartingStack] = useState(1000)
  const [style, setStyle] = useState('C') // 'C' cash / 'T' tournament
  const [rebuy, setRebuy] = useState(true)
  const [blindIncrease, setBlindIncrease] = useState(10)

  function handleCreate() {
    onCreate({ sb, bb, startingStack, style, rebuy, blindIncrease })
    onClose()
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-title">Game Settings</h2>
        {playerName && (
          <p className="modal-subtitle">Creating a table as {playerName}</p>
        )}

        <div className="settings-row">
          <div className="settings-field">
            <label className="field-label">Small blind</label>
            <input
              className="text-input"
              type="number"
              min="1"
              value={sb}
              onChange={(e) => setSb(Number(e.target.value))}
            />
          </div>
          <div className="settings-field">
            <label className="field-label">Big blind</label>
            <input
              className="text-input"
              type="number"
              min="1"
              value={bb}
              onChange={(e) => setBb(Number(e.target.value))}
            />
          </div>
        </div>

        <label className="field-label">Starting stack</label>
        <input
          className="text-input"
          type="number"
          min="1"
          value={startingStack}
          onChange={(e) => setStartingStack(Number(e.target.value))}
        />

        <label className="field-label">Game style</label>
        <select
          className="text-input"
          value={style}
          onChange={(e) => setStyle(e.target.value)}
        >
          <option value="C">Normal (fixed blinds)</option>
          <option value="T">Tournament (rising blinds)</option>
        </select>

        {style === 'T' && (
          <>
            <label className="field-label">Increase blinds every (hands)</label>
            <input
              className="text-input"
              type="number"
              min="1"
              value={blindIncrease}
              onChange={(e) => setBlindIncrease(Number(e.target.value))}
            />
          </>
        )}

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={rebuy}
            onChange={(e) => setRebuy(e.target.checked)}
          />
          Allow rebuy
        </label>

        <div className="modal-actions">
          <button className="btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleCreate}>
            Create Game
          </button>
        </div>
      </div>
    </div>
  )
}
