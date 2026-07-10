import LogInteractionForm from './components/LogInteractionForm.jsx'
import AIChatPanel from './components/AIChatPanel.jsx'

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">Log HCP Interaction</header>
      <div className="content-grid">
        <LogInteractionForm />
        <AIChatPanel />
      </div>
    </div>
  )
}
