import { useState } from 'react'

// Sensible starting values per unit. Toggling display resets to these rather
// than converting — converting chip defaults would give a cash game $0.10/$0.20
// blinds, which nobody wants. $1/$2 with a $200 stack is a 100bb cash setup.
const DEFAULTS = {
  chips: { sb: 10, bb: 20, stack: 1000 },     // chips
  cash: { sb: 1, bb: 2, stack: 200 },         // dollars
}

export default function CreateGameSettings({ onClose, onCreate, playerName }) {
  const [display, setDisplay] = useState('chips') // 'chips' | 'cash' — how amounts read
  const [sb, setSb] = useState(DEFAULTS.chips.sb)
  const [bb, setBb] = useState(DEFAULTS.chips.bb)
  const [startingStack, setStartingStack] = useState(DEFAULTS.chips.stack)
  const [style, setStyle] = useState('C') // 'C' normal / 'T' tournament — blind structure, NOT display
  const [rebuy, setRebuy] = useState(true)
  const [blindIncrease, setBlindIncrease] = useState(10)
  const [submitting, setSubmitting] = useState(false)
  const [invalid, setInvalid] = useState('')

  const isCash = display === 'cash'
  const unit = isCash ? '$' : 'chips'
  // the wire is always integer chips; dollars only exist inside this modal
  const toChips = (v) => Math.round(Number(v) * (isCash ? 100 : 1))

  function switchDisplay(next) {
    setDisplay(next)
    setInvalid('')
    setSb(DEFAULTS[next].sb)
    setBb(DEFAULTS[next].bb)
    setStartingStack(DEFAULTS[next].stack)
    // blindIncrease is a hand count, not money — it has no unit to reset
  }

  // Only close once the game actually exists — otherwise a failed create
  // would throw away everything the user typed.
  async function handleCreate() {
    if (submitting) return
    const chips = {
      sb: toChips(sb),
      bb: toChips(bb),
      startingStack: toChips(startingStack),
    }
    // Cash mode lets someone type 0.001, which rounds to 0 chips. A zero big
    // blind seeds last_raise to 0 and collapses the raise slider.
    if (chips.sb < 1 || chips.bb < 1) {
      setInvalid(`Blinds must be at least ${isCash ? '$0.01' : '1 chip'}.`)
      return
    }
    if (chips.bb < chips.sb) {
      setInvalid('Big blind must be at least the small blind.')
      return
    }
    if (chips.startingStack < chips.bb) {
      setInvalid('Starting stack must cover the big blind.')
      return
    }
    setInvalid('')
    setSubmitting(true)
    const ok = await onCreate({ ...chips, style, rebuy, blindIncrease, display })
    if (ok) onClose()
    else setSubmitting(false)
  }

  return (
    <div className="modal-backdrop" onClick={() => { if (!submitting) onClose() }}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <h2 className="modal-title">Game Settings</h2>
        {playerName && (
          <p className="modal-subtitle">Creating a table as {playerName}</p>
        )}

        {invalid && <div className="error-toast">{invalid}</div>}

        <div className="display-toggle">
          <span className={'switch-label' + (isCash ? '' : ' active')}>Chips</span>
          <label className="switch">
            <input
              type="checkbox"
              checked={isCash}
              onChange={(e) => switchDisplay(e.target.checked ? 'cash' : 'chips')}
            />
            <span className="switch-track" />
          </label>
          <span className={'switch-label' + (isCash ? ' active' : '')}>Cash</span>
        </div>

        <div className="settings-row">
          <div className="settings-field">
            <label className="field-label">Small blind ({unit})</label>
            <input
              className="text-input"
              type="number"
              min={isCash ? '0.01' : '1'}
              step={isCash ? '0.01' : '1'}
              value={sb}
              onChange={(e) => setSb(e.target.value)}
            />
          </div>
          <div className="settings-field">
            <label className="field-label">Big blind ({unit})</label>
            <input
              className="text-input"
              type="number"
              min={isCash ? '0.01' : '1'}
              step={isCash ? '0.01' : '1'}
              value={bb}
              onChange={(e) => setBb(e.target.value)}
            />
          </div>
        </div>

        <label className="field-label">Starting stack ({unit})</label>
        <input
          className="text-input"
          type="number"
          min={isCash ? '0.01' : '1'}
          step={isCash ? '0.01' : '1'}
          value={startingStack}
          onChange={(e) => setStartingStack(e.target.value)}
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
          <button className="btn-ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleCreate} disabled={submitting}>
            {submitting ? 'Creating…' : 'Create Game'}
          </button>
        </div>
      </div>
    </div>
  )
}
