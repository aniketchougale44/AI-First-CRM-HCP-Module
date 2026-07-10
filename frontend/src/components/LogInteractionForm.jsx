import { useSelector, useDispatch } from 'react-redux'
import {
  updateFormField,
  createInteraction,
} from '../store/interactionsSlice.js'

const SENTIMENTS = ['positive', 'neutral', 'negative']

export default function LogInteractionForm() {
  const dispatch = useDispatch()
  const form = useSelector((s) => s.interactions.currentForm)
  const aiFollowups = useSelector((s) => s.interactions.aiSuggestedFollowups)

  const set = (field) => (e) =>
    dispatch(updateFormField({ field, value: e.target.value }))

  const setList = (field) => (e) =>
    dispatch(
      updateFormField({
        field,
        value: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
      })
    )

  const handleSubmit = () => {
    if (!form.hcp_name) return
    dispatch(createInteraction(form))
  }

  return (
    <div className="panel form-panel">
      <h2 className="panel-title">Interaction Details</h2>

      <div className="row two-col">
        <Field label="HCP Name">
          <input
            placeholder="Search or select HCP..."
            value={form.hcp_name}
            onChange={set('hcp_name')}
          />
        </Field>
        <Field label="Interaction Type">
          <select value={form.interaction_type} onChange={set('interaction_type')}>
            <option>Meeting</option>
            <option>Call</option>
            <option>Email</option>
            <option>Conference</option>
          </select>
        </Field>
      </div>

      <div className="row two-col">
        <Field label="Date">
          <input type="date" value={form.date} onChange={set('date')} />
        </Field>
        <Field label="Time">
          <input type="time" value={form.time} onChange={set('time')} />
        </Field>
      </div>

      <Field label="Attendees">
        <input
          placeholder="Enter names or search..."
          value={form.attendees.join(', ')}
          onChange={setList('attendees')}
        />
      </Field>

      <Field label="Topics Discussed">
        <textarea
          placeholder="Enter key discussion points..."
          value={form.topics_discussed}
          onChange={set('topics_discussed')}
        />
      </Field>

      <div className="row two-col">
        <Field label="Materials Shared">
          <input
            placeholder="No materials added"
            value={form.materials_shared.join(', ')}
            onChange={setList('materials_shared')}
          />
        </Field>
        <Field label="Samples Distributed">
          <input
            placeholder="No samples added"
            value={form.samples_distributed.join(', ')}
            onChange={setList('samples_distributed')}
          />
        </Field>
      </div>

      <Field label="Observed / Inferred HCP Sentiment">
        <div className="sentiment-row">
          {SENTIMENTS.map((s) => (
            <label key={s} className="sentiment-option">
              <input
                type="radio"
                name="sentiment"
                checked={form.sentiment === s}
                onChange={() =>
                  dispatch(updateFormField({ field: 'sentiment', value: s }))
                }
              />
              {s[0].toUpperCase() + s.slice(1)}
            </label>
          ))}
        </div>
      </Field>

      <Field label="Outcomes">
        <textarea
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={set('outcomes')}
        />
      </Field>

      <Field label="Follow-up Actions">
        <textarea
          placeholder="Enter next steps or tasks..."
          value={form.follow_up_actions}
          onChange={set('follow_up_actions')}
        />
      </Field>

      {aiFollowups.length > 0 && (
        <div className="ai-followups">
          <div className="ai-followups-title">AI Suggested Follow-ups:</div>
          <ul>
            {aiFollowups.map((f, i) => (
              <li key={i}>+ {f}</li>
            ))}
          </ul>
        </div>
      )}

      <button className="log-btn" onClick={handleSubmit}>
        Log Interaction
      </button>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="field">
      <label>{label}</label>
      {children}
    </div>
  )
}
