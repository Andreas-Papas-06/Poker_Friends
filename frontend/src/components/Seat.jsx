import Card from './Card'

export default function Seat({ player, isYou, isTurn, isDealer }) {
  const { id, chips, current_bet, folded, all_in, hand } = player

  return (
    <div
      className={
        'seat' +
        (isTurn ? ' seat-turn' : '') +
        (folded ? ' seat-folded' : '')
      }
    >
      <div className="seat-cards">
        {hand ? (
          hand.map((c, i) => <Card key={i} card={c} />)
        ) : (
          <>
            <Card back />
            <Card back />
          </>
        )}
      </div>

      <div className="seat-info">
        <div className="seat-name">
          {isDealer && <span className="dealer-button">D</span>}
          {id} {isYou && <span className="you-tag">(you)</span>}
        </div>
        <div className="seat-chips">{chips}</div>
        {all_in && <div className="seat-tag tag-allin">ALL IN</div>}
        {folded && <div className="seat-tag tag-folded">folded</div>}
      </div>

      {current_bet > 0 && <div className="seat-bet">{current_bet}</div>}
    </div>
  )
}
