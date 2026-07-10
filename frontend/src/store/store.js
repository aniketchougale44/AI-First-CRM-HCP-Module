import { configureStore } from '@reduxjs/toolkit'
import interactionsReducer from './interactionsSlice.js'
import chatReducer from './chatSlice.js'

export const store = configureStore({
  reducer: {
    interactions: interactionsReducer,
    chat: chatReducer,
  },
})
