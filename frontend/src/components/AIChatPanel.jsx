import { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { addUserMessage, sendChatMessage } from '../store/chatSlice.js'
import {
  updateFormField,
  setAISuggestedFollowups,
} from '../store/interactionsSlice.js'

export default function AIChatPanel() {
  const dispatch = useDispatch()
  const messages = useSelector((s) => s.chat.messages)
  const status = useSelector((s) => s.chat.status)
  const [draft, setDraft] = useState('')

  const handleSend = async () => {
    if (!draft.trim()) return
    dispatch(addUserMessage(draft))
    setDraft('')

    const result = await dispatch(sendChatMessage(draft))
    if (sendChatMessage.fulfilled.match(result)) {
      const { interaction, ai_suggested_followups } = result.payload

      if (interaction) {
        const fieldMap = {
          hcp_name: interaction.hcp_name,
          interaction_type: interaction.interaction_type,
          date: interaction.date,
          time: interaction.time,
          attendees: interaction.attendees,
          topics_discussed: interaction.topics_discussed,
          materials_shared: interaction.materials_shared,
          samples_distributed: interaction.samples_distributed,
          sentiment: interaction.sentiment,
          outcomes: interaction.outcomes,
          follow_up_actions: interaction.follow_up_actions,
        }
        Object.entries(fieldMap).forEach(([field, value]) => {
          if (value !== null && value !== undefined) {
            dispatch(updateFormField({ field, value }))
          }
        })
        if (interaction.ai_suggested_followups) {
          dispatch(setAISuggestedFollowups(interaction.ai_suggested_followups))
        }
      }

      // Handles standalone suggest_followups calls (e.g. rep asks "what should
      // I follow up on?" later in the conversation, with no interaction update
      // attached) - still refresh the form's follow-ups box in that case.
      if (!interaction && ai_suggested_followups) {
        dispatch(setAISuggestedFollowups(ai_suggested_followups))
      }
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="panel chat-panel">
      <h2 className="panel-title">
        AI Assistant
        <span className="panel-subtitle">Log interaction via chat</span>
      </h2>

      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.content}
            {m.toolCalls && m.toolCalls.length > 0 && (
              <div className="tool-tag">
                used: {m.toolCalls.join(', ')}
              </div>
            )}
          </div>
        ))}
        {status === 'loading' && (
          <div className="chat-bubble assistant loading">Thinking…</div>
        )}
      </div>

      <div className="chat-input-row">
        <input
          placeholder="Describe interaction..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button onClick={handleSend}>Log</button>
      </div>
    </div>
  )
}