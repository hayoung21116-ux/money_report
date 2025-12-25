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
  
  &.danger {
    background-color: #dc3545;
    color: white;
    
    &:hover {
      background-color: #c82333;
    }
  }
`;

function EditTransactionModal({ isOpen, onClose, transaction, accountId, onTransactionUpdated, accountType }) {
  const [formData, setFormData] = useState({
    type: 'income',
    amount: 0,
    category: '',
    memo: '',
    date: ''
  });

  useEffect(() => {
    if (transaction) {
      setFormData({
        type: transaction.type,
        amount: transaction.amount,
        category: transaction.category,
        memo: transaction.memo,
        date: transaction.date.substring(0, 10)
      });
    }
  }, [transaction]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? parseFloat(value) || 0 : value
    }));
    
    // Update category options when type changes
    if (name === 'type') {
      if (accountType === '투자') {
        setFormData(prev => ({
          ...prev,
          category: value === 'income' ? '이동' : '이동'
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          category: value === 'income' ? '저축' : '지출'
        }));
      }
    }
  };

  const getCategoryOptions = () => {
    if (accountType === '투자') {
      return formData.type === 'income' 
        ? ['이동', '수익'] 
        : ['이동', '손익'];
    } else {
      return formData.type === 'income' 
        ? ['저축', '이자', '이동', '대출'] 
        : ['지출', '투자', '이동'];
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await accountApi.updateTransaction(accountId, transaction.id, formData);
      onTransactionUpdated(response.data);
      
      alert('거래가 성공적으로 수정되었습니다!');
      onClose();
    } catch (error) {
      console.error('Error updating transaction:', error);
      alert('거래 수정 중 오류가 발생했습니다.');
    }
  };

  const handleDelete = async () => {
    if (window.confirm('정말로 이 거래를 삭제하시겠습니까?')) {
      try {
        await accountApi.deleteTransaction(accountId, transaction.id);
        alert('거래가 성공적으로 삭제되었습니다!');
        onClose();
        onTransactionUpdated(); // Refresh the transaction list
      } catch (error) {
        console.error('Error deleting transaction:', error);
        alert('거래 삭제 중 오류가 발생했습니다.');
      }
    }
  };

  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>거래 수정</h2>
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <label htmlFor="edit-type">타입</label>
            <select
              id="edit-type"
              name="type"
              value={formData.type}
              onChange={handleChange}
            >
              <option value="income">수입</option>
              <option value="expense">지출</option>
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-amount">금액</label>
            <input
              type="number"
              id="edit-amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              min="0"
              step="any"
              placeholder="금액을 입력하세요"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-category">카테고리</label>
            <select
              id="edit-category"
              name="category"
              value={formData.category}
              onChange={handleChange}
            >
              {getCategoryOptions().map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-memo">메모</label>
            <textarea
              id="edit-memo"
              name="memo"
              value={formData.memo}
              onChange={handleChange}
              placeholder="메모를 입력하세요"
            />
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-date">날짜</label>
            <input
              type="date"
              id="edit-date"
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
            <Button type="button" className="danger" onClick={handleDelete}>
              삭제
            </Button>
            <Button type="submit" className="primary">
              수정
            </Button>
          </ButtonGroup>
        </Form>
      </ModalContent>
    </ModalOverlay>
  );
}

export default EditTransactionModal;
