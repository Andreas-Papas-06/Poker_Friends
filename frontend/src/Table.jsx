import Board from './components/Board'
import Seat from './components/Seat'
import ActionBar from './components/ActionBar'
import ShowdownBanner from './components/ShowdownBanner'

export default function Table({ game }) {
  const { gameState: state, playerId, gameId, error, act, startGame, leaveGame } = game

  if (!state) return <div className="center-msg">Connecting…</div>

  const me = state.players.find((p) => p.id === playerId)
  const others = state.players.filter((p) => p.id !== playerId)
  const inHand = state.phase !== 'WAITING' && state.phase !== 'SHOWDOWN'
  const myTurn = state.action_turn === playerId

  return (
    <div className="table-screen">
      <div className="topbar">
        <span className="game-code">Table {gameId}</span>
        <button className="btn-ghost" onClick={leaveGame}>
          Leave
        </button>
      </div>

      {error && <div className="error-toast">{error}</div>}

      <div className="felt">
        <div className="opponents">
          {others.map((p) => (
            <Seat
              key={p.id}
              player={p}
              isTurn={state.action_turn === p.id}
              isDealer={state.dealer === p.id}
            />
          ))}
        </div>

        <Board board={state.board} pot={state.pot} />

        {state.waiting.length > 0 && (
          <div className="waiting-note">
            Waiting to join: {state.waiting.join(', ')}
          </div>
        )}

        {me && (
          <div className="you-seat">
            <Seat
              player={me}
              isYou
              isTurn={myTurn}
              isDealer={state.dealer === me.id}
            />
          </div>
        )}
      </div>

      <div className="controls">
        {state.phase === 'WAITING' && (
          <div className="pregame">
            <div className="invite">
              Invite code: <strong>{gameId}</strong>
              <button
                className="btn-ghost"
                onClick={() => navigator.clipboard?.writeText(gameId)}
              >
                Copy
              </button>
            </div>
            <button className="btn-primary" onClick={startGame}>
              Start Game
            </button>
          </div>
        )}
        {state.phase === 'SHOWDOWN' && (
          <ShowdownBanner showdown={state.showdown || []} onNext={startGame} />
        )}
        {inHand && myTurn && (
          <ActionBar
            options={state.options}
            state={state}
            playerId={playerId}
            onAct={act}
          />
        )}
        {inHand && !myTurn && (
          <div className="waiting-turn">Waiting for {state.action_turn}…</div>
        )}
      </div>
    </div>
  )
}
