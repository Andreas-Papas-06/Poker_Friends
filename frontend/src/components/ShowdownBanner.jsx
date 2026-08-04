import { formatAmount } from '../format'

export default function ShowdownBanner({ showdown, onNext, display }) {
  return (
    <div className="showdown-banner">
      <div className="showdown-results">
        {showdown.length === 0
          ? 'Hand over'
          : showdown.map((w, i) => (
              <span key={i} className="showdown-win">
                {w.player_id} wins {formatAmount(w.amount, display)}
              </span>
            ))}
      </div>
      <button className="btn-primary" onClick={onNext}>
        Next Hand
      </button>
    </div>
  )
}
