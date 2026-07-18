const SUITS = { H: '♥', D: '♦', S: '♠', C: '♣' }
const RANKS = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' }

export default function Card({ card, back = false }) {
  if (back || !card) {
    return <div className="card card-back" />
  }
  const red = card.suit === 'H' || card.suit === 'D'
  const rank = RANKS[card.rank] || card.rank
  return (
    <div className={`card ${red ? 'card-red' : 'card-black'}`}>
      <span className="card-rank">{rank}</span>
      <span className="card-suit">{SUITS[card.suit]}</span>
    </div>
  )
}
