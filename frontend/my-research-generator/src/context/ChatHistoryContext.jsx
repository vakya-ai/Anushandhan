// src/context/ChatHistoryContext.js
import { createContext, useContext, useReducer, useEffect } from 'react';
import PropTypes from 'prop-types';

const ADD_CHAT = 'ADD_CHAT';
const SELECT_CHAT = 'SELECT_CHAT';
const UPDATE_MESSAGES = 'UPDATE_MESSAGES';
const DELETE_CHAT = 'DELETE_CHAT';

const initialState = {
  chats: [],
  selectedChatId: null
};

function chatReducer(state, action) {
  switch (action.type) {
    case ADD_CHAT:
      return {
        ...state,
        chats: [...state.chats, action.payload],
        selectedChatId: action.payload.id
      };
    case SELECT_CHAT:
      return {
        ...state,
        selectedChatId: action.payload
      };
    case UPDATE_MESSAGES:
      return {
        ...state,
        chats: state.chats.map(chat =>
          chat.id === state.selectedChatId
            ? { ...chat, messages: action.payload }
            : chat
        )
      };
      case DELETE_CHAT: {
        const remainingChats = state.chats.filter(chat => chat.id !== action.payload);
        return {
          ...state,
          chats: remainingChats,
          selectedChatId: state.selectedChatId === action.payload 
            ? (remainingChats.length > 0 ? remainingChats[0].id : null)
            : state.selectedChatId
        };
      }
      
    default:
      return state;
  }
}

const ChatHistoryContext = createContext();

export function ChatHistoryProvider({ children }) {
  const [state, dispatch] = useReducer(chatReducer, initialState, () => {
    const savedState = localStorage.getItem('chatHistory');
    return savedState ? JSON.parse(savedState) : initialState;
  });

  useEffect(() => {
    localStorage.setItem('chatHistory', JSON.stringify(state));
  }, [state]);

  const addChat = (topic) => {
    const newChat = {
      id: Date.now().toString(),
      topic,
      createdAt: new Date().toISOString(),
      messages: []
    };
    dispatch({ type: ADD_CHAT, payload: newChat });
    return newChat.id;
  };

  const selectChat = (chatId) => {
    dispatch({ type: SELECT_CHAT, payload: chatId });
  };

  const updateMessages = (messages) => {
    dispatch({ type: UPDATE_MESSAGES, payload: messages });
  };

  const deleteChat = (chatId) => {
    dispatch({ type: DELETE_CHAT, payload: chatId });
  };

  const getCurrentChat = () => {
    return state.chats.find(chat => chat.id === state.selectedChatId) || null;
  };

  return (
    <ChatHistoryContext.Provider
      value={{
        chats: state.chats,
        selectedChatId: state.selectedChatId,
        addChat,
        selectChat,
        updateMessages,
        deleteChat,
        getCurrentChat
      }}
    >
      {children}
    </ChatHistoryContext.Provider>
  );
}

export function useChatHistory() {
  const context = useContext(ChatHistoryContext);
  if (!context) {
    throw new Error('useChatHistory must be used within a ChatHistoryProvider');
  }
  return context;
}

ChatHistoryProvider.propTypes = {
  children: PropTypes.node.isRequired,
};