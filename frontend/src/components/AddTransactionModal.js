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
  
  input, select, textarea {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
  }
  
  textarea {
    min-height: 80px;
    resize: vertical;
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

function AddTransactionModal({ isOpen, onClose, accountId, onTransactionAdded, accountType }) {
  const isInvestment = accountType === '투자';
  const [formData, setFormData] = useState({
    type: isInvestment ? 'buy' : 'income',
    amount: 0,
    category: isInvestment ? '' : '저축',
    memo: '',
    date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    // Reset form when modal opens
    if (isOpen) {
      setFormData({
        type: isInvestment ? 'buy' : 'income',
        amount: 0,
        category: isInvestment ? '' : '저축',
        memo: '',
        date: new Date().toISOString().split('T')[0]
      });
    }
  }, [isOpen, isInvestment]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? parseFloat(value) || 0 : value
    }));
    
    // Update category options when type changes (for non-investment accounts)
    if (name === 'type' && !isInvestment) {
      setFormData(prev => ({
        ...prev,
        category: value === 'income' ? '저축' : '지출'
      }));
    }
  };

  const getCategoryOptions = () => {
    if (isInvestment) {
      return []; // 투자 계좌는 카테고리 없음
    } else {
      return formData.type === 'income' 
        ? ['저축', '이자', '이동', '대출'] 
        : ['지출', '투자', '이동'];
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isInvestment) {
        // 투자 계좌는 valuations에 추가
        const valuationData = {
          evaluated_amount: formData.amount,
          evaluation_date: formData.date + 'T00:00:00Z',
          memo: formData.memo,
          transaction_type: formData.type // 'buy' or 'sell'
        };
        
        const response = await accountApi.addValuation(accountId, valuationData);
        alert('거래가 성공적으로 추가되었습니다!');
        onClose();
        if (onTransactionAdded) {
          onTransactionAdded();
        }
      } else {
        // 일반 계좌는 transactions에 추가
        const transactionData = {
          type: formData.type,
          amount: formData.amount,
          category: formData.category,
          memo: formData.memo,
          date: formData.date + 'T00:00:00Z'
        };
        
        const response = await accountApi.addTransaction(accountId, transactionData);
        alert('거래가 성공적으로 추가되었습니다!');
        onClose();
        if (onTransactionAdded) {
          onTransactionAdded(response.data);
        }
      }
    } catch (error) {
      console.error('Error adding transaction/valuation:', error);
      const errorMessage = error.response?.data?.detail || error.message || '알 수 없는 오류';
      alert('거래 추가 중 오류가 발생했습니다: ' + errorMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>거래 추가</h2>
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <label htmlFor="type">타입</label>
            <select
              id="type"
              name="type"
              value={formData.type}
              onChange={handleChange}
            >
              {isInvestment ? (
                <>
                  <option value="buy">매수</option>
                  <option value="sell">매도</option>
                  <option value="valuation">평가</option>
                </>
              ) : (
                <>
                  <option value="income">수입</option>
                  <option value="expense">지출</option>
                </>
              )}
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="amount">{isInvestment ? '금액' : '금액'}</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              min="0"
              step="any"
              placeholder="금액을 입력하세요"
              required
            />
          </FormGroup>
          
          {!isInvestment && (
            <FormGroup>
              <label htmlFor="category">카테고리</label>
              <select
                id="category"
                name="category"
                value={formData.category}
                onChange={handleChange}
              >
                {getCategoryOptions().map(category => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </FormGroup>
          )}
          
          <FormGroup>
            <label htmlFor="memo">메모</label>
            <textarea
              id="memo"
              name="memo"
              value={formData.memo}
              onChange={handleChange}
              placeholder="메모를 입력하세요"
            />
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="date">날짜</label>
            <input
              type="date"
              id="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              required
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

export default AddTransactionModal;
