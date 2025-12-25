import React, { useState } from 'react';
import styled from 'styled-components';
import { accountApi } from '../services/api';

const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
`;

const ModalContent = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  
  h2 {
    margin-top: 0;
    color: #333;
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 15px;
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 5px;
  
  label {
    font-weight: 600;
    color: #333;
  }
  
  input, select {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
  }
  
  input[type="color"] {
    height: 40px;
    padding: 2px;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 20px;
`;

const Button = styled.button`
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
  
  &.primary {
    background-color: #007bff;
    color: white;
    
    &:hover {
      background-color: #0056b3;
    }
  }
  
  &.secondary {
    background-color: #6c757d;
    color: white;
    
    &:hover {
      background-color: #545b62;
    }
  }
`;

function AddAccountModal({ isOpen, onClose, onAccountAdded }) {
  const [formData, setFormData] = useState({
    name: '',
    type: '현금',
    color: '#4CAF50',
    balance: 0,
    image_path: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'balance' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Prepare the account data
      const accountData = {
        name: formData.name,
        type: formData.type,
        color: formData.color,
        opening_balance: formData.balance,
        image_path: formData.image_path
      };

      console.log('Creating account with data:', accountData);
      await accountApi.createAccount(accountData);

      alert('계좌가 성공적으로 추가되었습니다!');
      onClose();
      onAccountAdded();
    } catch (error) {
      console.error('Error creating account:', error);
      const errorMessage = error.response?.data?.detail
        ? (typeof error.response.data.detail === 'object' ? JSON.stringify(error.response.data.detail) : error.response.data.detail)
        : error.message;
      alert('계좌 추가 중 오류가 발생했습니다: ' + errorMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>계좌 추가</h2>
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <label htmlFor="name">계좌명</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="계좌명을 입력하세요"
              required
            />
          </FormGroup>

          <FormGroup>
            <label htmlFor="type">계좌 유형</label>
            <select
              id="type"
              name="type"
              value={formData.type}
              onChange={handleChange}
            >
              <option value="현금">현금</option>
              <option value="투자">투자</option>
              <option value="소비">소비</option>
            </select>
          </FormGroup>

          <FormGroup>
            <label htmlFor="balance">초기 잔액</label>
            <input
              type="number"
              id="balance"
              name="balance"
              value={formData.balance}
              onChange={handleChange}
              min="0"
              step="1"
            />
          </FormGroup>

          <FormGroup>
            <label htmlFor="color">색상</label>
            <input
              type="color"
              id="color"
              name="color"
              value={formData.color}
              onChange={handleChange}
            />
          </FormGroup>

          <ButtonGroup>
            <Button type="button" className="secondary" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" className="primary">
              추가
            </Button>
          </ButtonGroup>
        </Form>
      </ModalContent>
    </ModalOverlay>
  );
}

export default AddAccountModal;
