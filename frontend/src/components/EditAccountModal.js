import React, { useState, useEffect } from 'react';
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

function EditAccountModal({ isOpen, onClose, account, onAccountUpdated }) {
  const [formData, setFormData] = useState({
    name: '',
    type: '현금',
    color: '#4CAF50',
    balance: 0,
    image_path: '',
    purchase_amount: 0,
    cash_holding: 0,
    evaluated_amount: 0
  });

  const calculateBalance = (account) => {
    if (account.type === '투자') {
      // For investment accounts, use asset_value if available
      return account.asset_value || 0;
    }
    
    // For other account types, calculate balance from transactions
    const income = account.transactions
      ? account.transactions
          .filter(t => t.type === "income")
          .reduce((sum, t) => sum + t.amount, 0)
      : 0;
      
    const expense = account.transactions
      ? account.transactions
          .filter(t => t.type === "expense")
          .reduce((sum, t) => sum + t.amount, 0)
      : 0;
      
    return account.opening_balance + income - expense;
  };

  useEffect(() => {
    if (account) {
      setFormData({
        name: account.name,
        type: account.type,
        color: account.color,
        balance: account.type === '투자' ? account.asset_value : calculateBalance(account),
        image_path: account.image_path || '',
        purchase_amount: account.purchase_amount || 0,
        cash_holding: account.cash_holding || 0,
        evaluated_amount: account.evaluated_amount || 0
      });
    }
  }, [account]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numericFields = ['balance', 'purchase_amount', 'cash_holding', 'evaluated_amount'];
    setFormData(prev => ({
      ...prev,
      [name]: numericFields.includes(name) ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Prepare update data based on account type
      const updateData = {
        name: formData.name,
        type: formData.type,
        color: formData.color,
        image_path: formData.image_path || '',
        opening_balance: 0,
        purchase_amount: 0,
        cash_holding: 0,
        evaluated_amount: 0
      };

      if (formData.type === '투자') {
        // For investment accounts, use the investment-specific fields
        updateData.purchase_amount = formData.purchase_amount || 0;
        updateData.cash_holding = formData.cash_holding || 0;
        updateData.evaluated_amount = formData.evaluated_amount || 0;
      } else {
        // For regular accounts, calculate opening_balance from current balance
        // We need to reverse-calculate: balance = opening_balance + income - expense
        const income = account.transactions
          ? account.transactions
              .filter(t => t.type === "income")
              .reduce((sum, t) => sum + t.amount, 0)
          : 0;
        const expense = account.transactions
          ? account.transactions
              .filter(t => t.type === "expense")
              .reduce((sum, t) => sum + t.amount, 0)
          : 0;
        // If balance changed, adjust opening_balance
        const currentBalance = account.opening_balance + income - expense;
        const balanceDiff = formData.balance - currentBalance;
        updateData.opening_balance = account.opening_balance + balanceDiff;
      }

      const response = await accountApi.updateAccount(account.id, updateData);
      alert('계좌가 성공적으로 수정되었습니다!');
      onClose();
      if (onAccountUpdated) {
        onAccountUpdated(response.data);
      }
    } catch (error) {
      console.error('Error updating account:', error);
      alert('계좌 수정 중 오류가 발생했습니다: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (!isOpen || !account) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>계좌 수정</h2>
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
          
          {formData.type === '투자' ? (
            <>
              <FormGroup>
                <label htmlFor="purchase_amount">매입 금액</label>
                <input
                  type="number"
                  id="purchase_amount"
                  name="purchase_amount"
                  value={formData.purchase_amount || 0}
                  onChange={handleChange}
                  min="0"
                  step="any"
                />
              </FormGroup>
              
              <FormGroup>
                <label htmlFor="cash_holding">보유 현금</label>
                <input
                  type="number"
                  id="cash_holding"
                  name="cash_holding"
                  value={formData.cash_holding || 0}
                  onChange={handleChange}
                  min="0"
                  step="any"
                />
              </FormGroup>
              
              <FormGroup>
                <label htmlFor="evaluated_amount">현재 평가 금액</label>
                <input
                  type="number"
                  id="evaluated_amount"
                  name="evaluated_amount"
                  value={formData.evaluated_amount || 0}
                  onChange={handleChange}
                  min="0"
                  step="any"
                />
              </FormGroup>
            </>
          ) : (
            <FormGroup>
              <label htmlFor="balance">잔액</label>
              <input
                type="number"
                id="balance"
                name="balance"
                value={formData.balance}
                onChange={handleChange}
                min="0"
                step="any"
              />
            </FormGroup>
          )}
          
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
              저장
            </Button>
          </ButtonGroup>
        </Form>
      </ModalContent>
    </ModalOverlay>
  );
}

export default EditAccountModal;
