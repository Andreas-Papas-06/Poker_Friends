export default function ShowdownBanner({ showdown, onNext }) {
  return (
    <div className="showdown-banner">
      <div className="showdown-results">
        {showdown.length === 0
          ? 'Hand over'
          : showdown.map((w, i) => (
              <span key={i} className="showdown-win">
                {w.player_id} wins {w.amount}
              </span>
            ))}
      </div>
      <button className="btn-primary" onClick={onNext}>
        Next Hand
      </button>
    </div>
  )
}
