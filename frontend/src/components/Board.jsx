import Card from './Card'
import { formatAmount } from '../format'

export default function Board({ board, pot, display }) {
  return (
    <div className="board">
      <div className="board-cards">
        {[0, 1, 2, 3, 4].map((i) =>
          board[i] ? (
            <Card key={i} card={board[i]} />
          ) : (
            <div key={i} className="card card-placeholder" />
          )
        )}
      </div>
      <div className="pot">Pot: {formatAmount(pot, display)}</div>
    </div>
  )
}
