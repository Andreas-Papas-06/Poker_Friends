import { useState, useEffect } from 'react'

export default function ActionBar({ options, state, playerId, onAct }) {
  const me = state.players.find((p) => p.id === playerId)
  const myBet = me ? me.current_bet : 0
  const myChips = me ? me.chips : 0
  const toCall = Math.max(0, state.current_bet - myBet)

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
          Call {toCall}
        </button>
      )}
      {canRaise && (
        <div className="raise-group">
          <input
            type="range"
            min={minRaiseTo}
            max={maxRaiseTo}
            value={raiseTo}
            onChange={(e) => setRaiseTo(Number(e.target.value))}
          />
          <input
            type="number"
            min={minRaiseTo}
            max={maxRaiseTo}
            value={raiseTo}
            onChange={(e) => setRaiseTo(Number(e.target.value))}
            className="raise-input"
          />
          {/* engine's player_bet adds chips to current_bet, so send the delta */}
          <button
            className="btn-action btn-raise"
            onClick={() => onAct('raise', raiseTo - myBet)}
          >
            {raiseLabel} to {raiseTo}
          </button>
        </div>
      )}
    </div>
  )
}
