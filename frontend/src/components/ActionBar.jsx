import { useState, useEffect } from 'react'
import { formatAmount } from '../format'

export default function ActionBar({ options, state, playerId, onAct }) {
  const me = state.players.find((p) => p.id === playerId)
  const myBet = me ? me.current_bet : 0
  const myChips = me ? me.chips : 0
  const toCall = Math.max(0, state.current_bet - myBet)
  const display = state.display

  // raiseTo is always chips — the engine's unit. Only the number input is
  // shown in the display unit, converted at that one boundary.
  const isCash = display === 'cash'
  const toInput = (chips) => (isCash ? chips / 100 : chips)
  // Math.round matters: 40.01 * 100 is 4000.9999999999995, and the engine
  // does integer chip arithmetic.
  const fromInput = (val) => Math.round(Number(val) * (isCash ? 100 : 1))

  // engine-computed raise-to bounds (fall back to local calc if absent)
  const maxRaiseTo = state.max_raise ?? myBet + myChips
  const minRaiseTo = Math.min(state.min_raise ?? state.current_bet + 1, maxRaiseTo)
  const [raiseTo, setRaiseTo] = useState(minRaiseTo)

  // keep the chosen amount within the valid range as the hand progresses
  useEffect(() => {
    setRaiseTo((v) => Math.min(Math.max(v, minRaiseTo), maxRaiseTo))
  }, [minRaiseTo, maxRaiseTo])

  const canRaise = options.includes('raise') && maxRaiseTo > state.current_bet
  const raiseLabel = toCall === 0 ? 'Bet' : 'Raise'

  // Pot-relative sizing. Standard convention is that you call first and then bet
  // a fraction of the resulting pot, so a full "Pot" raise puts you at
  // current_bet + pot + toCall. state.pot already includes this street's bets.
  // These only move the slider — the player still confirms.
  const clamp = (v) => Math.min(Math.max(Math.round(v), minRaiseTo), maxRaiseTo)
  const sizeTo = (fraction) =>
    setRaiseTo(clamp(state.current_bet + fraction * (state.pot + toCall)))

  return (
    <div className="action-bar">
      {options.includes('fold') && (
        <button className="btn-action btn-fold" onClick={() => onAct('fold')}>
          Fold
        </button>
      )}
      {options.includes('check') && (
        <button className="btn-action" onClick={() => onAct('check')}>
          Check
        </button>
      )}
      {options.includes('call') && (
        <button className="btn-action btn-call" onClick={() => onAct('call')}>
          Call {formatAmount(toCall, display)}
        </button>
      )}
      {canRaise && (
        <div className="raise-group">
          <div className="bet-sizes">
            <button className="btn-size" onClick={() => sizeTo(0.25)}>¼ Pot</button>
            <button className="btn-size" onClick={() => sizeTo(0.5)}>½ Pot</button>
            <button className="btn-size" onClick={() => sizeTo(1)}>Pot</button>
            <button className="btn-size" onClick={() => setRaiseTo(maxRaiseTo)}>Max</button>
          </div>
          <div className="raise-row">
          <input
            type="range"
            min={minRaiseTo}
            max={maxRaiseTo}
            value={raiseTo}
            onChange={(e) => setRaiseTo(Number(e.target.value))}
          />
          <input
            type="number"
            min={toInput(minRaiseTo)}
            max={toInput(maxRaiseTo)}
            step={isCash ? '0.01' : '1'}
            value={toInput(raiseTo)}
            onChange={(e) => {
              if (e.target.value === '') return   // don't zero state mid-edit
              setRaiseTo(fromInput(e.target.value))
            }}
            className="raise-input"
          />
          {/* engine's player_bet adds chips to current_bet, so send the delta */}
          <button
            className="btn-action btn-raise"
            onClick={() => onAct('raise', raiseTo - myBet)}
          >
            {raiseLabel} to {formatAmount(raiseTo, display)}
          </button>
          </div>
        </div>
      )}
    </div>
  )
}
