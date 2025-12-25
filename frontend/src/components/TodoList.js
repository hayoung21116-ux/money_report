import React, { useState, useEffect } from 'react';
import styled from 'styled-components';

const TodoContainer = styled.div`
  position: fixed;
  top: 60px;
  right: 20px;
  width: 300px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
`;

const TodoHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  h3 {
    margin: 0;
    font-size: 16px;
    color: #333;
  }
  
  button {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #666;
    
    &:hover {
      color: #333;
    }
  }
`;

const TodoInput = styled.div`
  padding: 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  gap: 8px;
  
  input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }
  
  button {
    padding: 8px 12px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    
    &:hover {
      background-color: #0056b3;
    }
  }
`;

const TodoListContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  max-height: 300px;
`;

const TodoItem = styled.div`
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  gap: 10px;
  
  &:last-child {
    border-bottom: none;
  }
`;

const Checkbox = styled.input`
  margin: 0;
`;

const TodoText = styled.span`
  flex: 1;
  font-size: 14px;
  color: #333;
  
  ${props => props.completed && `
    text-decoration: line-through;
    color: #999;
  `}
`;

const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #ff6b6b;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  
  &:hover {
    color: #ff5252;
  }
`;

function TodoList({ isOpen, onClose }) {
  const [todos, setTodos] = useState([]);
  const [newTodo, setNewTodo] = useState('');

  // Load todos from localStorage on component mount
  useEffect(() => {
    const savedTodos = localStorage.getItem('todos');
    if (savedTodos) {
      setTodos(JSON.parse(savedTodos));
    }
  }, []);

  // Save todos to localStorage whenever todos change
  useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos));
  }, [todos]);

  const addTodo = () => {
    if (newTodo.trim() !== '') {
      setTodos([
        ...todos,
        {
          id: Date.now(),
          text: newTodo,
          completed: false
        }
      ]);
      setNewTodo('');
    }
  };

  const toggleTodo = (id) => {
    setTodos(todos.map(todo => 
      todo.id === id ? { ...todo, completed: !todo.completed } : todo
    ));
  };

  const deleteTodo = (id) => {
    setTodos(todos.filter(todo => todo.id !== id));
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      addTodo();
    }
  };

  if (!isOpen) return null;

  return (
    <TodoContainer>
      <TodoHeader>
        <h3>할 일 목록</h3>
        <button onClick={onClose}>&times;</button>
      </TodoHeader>
      
      <TodoInput>
        <input
          type="text"
          value={newTodo}
          onChange={(e) => setNewTodo(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="새로운 할 일 추가"
        />
        <button onClick={addTodo}>추가</button>
      </TodoInput>
      
      <TodoListContainer>
        {todos.length === 0 ? (
          <TodoItem>
            <TodoText>할 일이 없습니다</TodoText>
          </TodoItem>
        ) : (
          todos.map(todo => (
            <TodoItem key={todo.id}>
              <Checkbox
                type="checkbox"
                checked={todo.completed}
                onChange={() => toggleTodo(todo.id)}
              />
              <TodoText completed={todo.completed}>
                {todo.text}
              </TodoText>
              <DeleteButton onClick={() => deleteTodo(todo.id)}>
                &times;
              </DeleteButton>
            </TodoItem>
          ))
        )}
      </TodoListContainer>
    </TodoContainer>
  );
}

export default TodoList;
