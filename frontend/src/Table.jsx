import Board from './components/Board'
import Seat from './components/Seat'
import ActionBar from './components/ActionBar'
import ShowdownBanner from './components/ShowdownBanner'
import { useState } from 'react'
import ConfirmDialog from './components/ConfirmDialog'
import { formatAmount } from './format'

export default function Table({ game }) {
  const { gameState: state, playerId, gameId, error, act, startGame, leaveGame, rebuy } = game
  // hooks must run before any conditional return, or the "Connecting…" render
  // (which calls none) and the loaded render disagree on hook count
  const [confirmLeave, setConfirmLeave] = useState(false)

  if (!state) return <div className="center-msg">Connecting…</div>

  const me = state.players.find((p) => p.id === playerId)
  const others = state.players.filter((p) => p.id !== playerId)
  const inHand = state.phase !== 'WAITING' && state.phase !== 'SHOWDOWN'
  const myTurn = state.action_turn === playerId
  const display = state.display   // 'chips' | 'cash' — fixed at game creation

  return (
    <div className="table-screen">
      <div className="topbar">
        <span className="game-code">Table {gameId}</span>
        <button className="btn-ghost" onClick={() => setConfirmLeave(true)}>
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
              display={display}
            />
          ))}
        </div>

        <Board board={state.board} pot={state.pot} display={display} />

        {state.waiting.length > 0 && (
          <div className="waiting-note">
            Waiting to join: {state.waiting.join(', ')}
          </div>
        )}

        {state.spectators?.length > 0 && (
          <div className="waiting-note">
            Spectating: {state.spectators.join(', ')}
          </div>
        )}

        {me && (
          <div className="you-seat">
            <Seat
              player={me}
              isYou
              isTurn={myTurn}
              isDealer={state.dealer === me.id}
              display={display}
            />
          </div>
        )}
      </div>

      <div className="controls">
        {state.can_rebuy && (
          <button className="btn-primary" onClick={rebuy}>
            Rebuy {formatAmount(state.starting_stack, display)}
          </button>
        )}
        {state.spectating && !state.can_rebuy && (
          <div className="waiting-turn">Spectating</div>
        )}
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
          <ShowdownBanner showdown={state.showdown || []} onNext={startGame} display={display} />
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
      {confirmLeave && (
        <ConfirmDialog
          title="Leave table?"
          message={
            inHand
              ? 'You are in a hand — leaving folds you and forfeits the chips you have already bet.'
              : 'You can rejoin later with the invite code.'
          }
          confirmLabel="Leave"
          onConfirm={leaveGame}
          onCancel={() => setConfirmLeave(false)}
        />
      )}
    </div>
  )
}
