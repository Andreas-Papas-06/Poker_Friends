import { useState } from 'react'
import { socket } from './socket'

const SUITS = { H: '♥', D: '♦', S: '♠', C: '♣' }
const RANKS = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' }

function cardLabel(card) {
  if (!card) return '🂠'
  return `${RANKS[card.rank] || card.rank}${SUITS[card.suit] || card.suit}`
}

function Card({ card }) {
  const red = card && (card.suit === 'H' || card.suit === 'D')
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '8px 10px',
        margin: 4,
        border: '1px solid #999',
        borderRadius: 6,
        background: card ? '#fff' : '#446',
        color: red ? 'crimson' : card ? 'black' : '#fff',
        minWidth: 22,
        textAlign: 'center',
        fontWeight: 'bold',
      }}
    >
      {cardLabel(card)}
    </span>
  )
}

export default function Table({ gameState, playerId, gameId, error, onLeave }) {
  const [raiseAmount, setRaiseAmount] = useState(20)

  if (!gameState) return <p style={{ padding: 40 }}>Connecting…</p>

  const myTurn = gameState.action_turn === playerId
  const inHand =
    gameState.phase !== 'WAITING' && gameState.phase !== 'SHOWDOWN'

  function act(action) {
    socket.emit('player_action', {
      game_id: gameId,
      action,
      amount: action === 'raise' || action === 'bet' ? Number(raiseAmount) : 0,
    })
  }

  function startGame() {
    socket.emit('start_game', { game_id: gameId })
  }

  return (
    <div style={{ padding: 40, fontFamily: 'sans-serif', maxWidth: 600 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Table {gameId}</h2>
        <button onClick={onLeave} style={{ padding: '6px 12px' }}>
          Leave table
        </button>
      </div>
      {error && <p style={{ color: 'crimson' }}>{error}</p>}
      <p>
        Phase: <strong>{gameState.phase}</strong> &nbsp;|&nbsp; Pot:{' '}
        <strong>{gameState.pot}</strong> &nbsp;|&nbsp; Current bet:{' '}
        <strong>{gameState.current_bet}</strong>
      </p>

      <div style={{ margin: '20px 0' }}>
        <strong>Board:</strong>{' '}
        {gameState.board.length === 0
          ? '—'
          : gameState.board.map((c, i) => <Card key={i} card={c} />)}
      </div>

      <div>
        <strong>Players:</strong>
        {gameState.players.map((p) => (
          <div
            key={p.id}
            style={{
              padding: 10,
              margin: '6px 0',
              background: p.id === gameState.action_turn ? '#ffd' : '#f4f4f4',
              border:
                p.id === playerId ? '2px solid #393' : '1px solid #ddd',
              borderRadius: 6,
            }}
          >
            <div>
              {p.id} {p.id === playerId && '(you)'} — chips: {p.chips}, bet:{' '}
              {p.current_bet}
              {p.folded && ' · folded'}
              {p.all_in && ' · all-in'}
            </div>
            <div>
              {p.hand ? (
                p.hand.map((c, i) => <Card key={i} card={c} />)
              ) : (
                <>
                  <Card card={null} />
                  <Card card={null} />
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 24 }}>
        {gameState.phase === 'WAITING' && (
          <button onClick={startGame} style={{ padding: '10px 16px' }}>
            Start Game
          </button>
        )}
        {gameState.phase === 'SHOWDOWN' && (
          <button onClick={startGame} style={{ padding: '10px 16px' }}>
            Next Hand
          </button>
        )}
        {inHand && myTurn && (
          <div>
            <p>
              <strong>Your turn:</strong>
            </p>
            <button onClick={() => act('fold')}>Fold</button>{' '}
            <button onClick={() => act('check')}>Check</button>{' '}
            <button onClick={() => act('call')}>Call</button>{' '}
            <button onClick={() => act('raise')}>Raise</button>
            <input
              type="number"
              value={raiseAmount}
              onChange={(e) => setRaiseAmount(e.target.value)}
              style={{ width: 70, marginLeft: 8 }}
            />
          </div>
        )}
        {inHand && !myTurn && (
          <p style={{ color: '#888' }}>
            Waiting for {gameState.action_turn} to act…
          </p>
        )}
      </div>
    </div>
  )
}
