import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client.js'

export const createInteraction = createAsyncThunk(
  'interactions/create',
  async (payload) => {
    const { data } = await api.post('/api/interactions', payload)
    return data
  }
)

export const fetchInteractions = createAsyncThunk(
  'interactions/fetchAll',
  async () => {
    const { data } = await api.get('/api/interactions')
    return data
  }
)

const emptyForm = {
  hcp_name: '',
  interaction_type: 'Meeting',
  date: '',
  time: '',
  attendees: [],
  topics_discussed: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: 'neutral',
  outcomes: '',
  follow_up_actions: '',
}

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    list: [],
    currentForm: emptyForm,
    aiSuggestedFollowups: [],
    status: 'idle',
    error: null,
  },
  reducers: {
    updateFormField(state, action) {
      const { field, value } = action.payload
      state.currentForm[field] = value
    },
    resetForm(state) {
      state.currentForm = emptyForm
      state.aiSuggestedFollowups = []
    },
    setAISuggestedFollowups(state, action) {
      state.aiSuggestedFollowups = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(createInteraction.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.list.unshift(action.payload)
        state.currentForm = emptyForm
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.list = action.payload
      })
  },
})

export const { updateFormField, resetForm, setAISuggestedFollowups } =
  interactionsSlice.actions
export default interactionsSlice.reducer
