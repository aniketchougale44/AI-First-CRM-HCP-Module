import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import api from '../api/client.js'

const SESSION_ID = 'session-' + Math.random().toString(36).slice(2)

export const sendChatMessage = createAsyncThunk(
  'chat/send',
  async (message) => {
    const { data } = await api.post('/api/chat', {
      session_id: SESSION_ID,
      message,
    })
    return data
  }
)

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    messages: [
      {
        role: 'assistant',
        content:
          'Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.',
      },
    ],
    status: 'idle',
  },
  reducers: {
    addUserMessage(state, action) {
      state.messages.push({ role: 'user', content: action.payload })
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = 'loading'
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded'
        state.messages.push({
          role: 'assistant',
          content: action.payload.reply,
          toolCalls: action.payload.tool_calls,
        })
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'failed'
        state.messages.push({
          role: 'assistant',
          content: 'Sorry, something went wrong reaching the AI assistant.',
        })
      })
  },
})

export const { addUserMessage } = chatSlice.actions
export default chatSlice.reducer
