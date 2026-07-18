import Card from './Card'

export default function Board({ board, pot }) {
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
      <div className="pot">Pot: {pot}</div>
    </div>
  )
}
