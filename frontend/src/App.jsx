import { useGameState } from './useGameState'
import Lobby from './Lobby'
import Table from './Table'

export default function App() {
  const game = useGameState()

  if (!game.joined) {
    return <Lobby onJoin={game.joinGame} error={game.error} />
  }
  return <Table game={game} />
}
