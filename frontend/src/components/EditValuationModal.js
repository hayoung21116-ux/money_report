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

function EditValuationModal({ isOpen, onClose, valuation, accountId, onValuationUpdated }) {
  const [formData, setFormData] = useState({
    evaluated_amount: 0,
    evaluation_date: '',
    memo: '',
    transaction_type: 'valuation'
  });

  useEffect(() => {
    if (valuation) {
      setFormData({
        evaluated_amount: valuation.evaluated_amount,
        evaluation_date: valuation.evaluation_date.substring(0, 10),
        memo: valuation.memo || '',
        transaction_type: valuation.transaction_type || 'valuation'
      });
    }
  }, [valuation]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'evaluated_amount' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Delete old valuation and create new one (since update API might not exist)
      const deleteResponse = await accountApi.deleteValuation(accountId, valuation.id);
      console.log('Delete response:', deleteResponse);
      
      // Format date to ISO 8601 format
      const dateStr = formData.evaluation_date;
      const isoDate = dateStr.includes('T') ? dateStr : dateStr + 'T00:00:00Z';
      
      const newValuation = {
        evaluated_amount: formData.evaluated_amount,
        evaluation_date: isoDate,
        memo: formData.memo,
        transaction_type: formData.transaction_type
      };
      
      console.log('Adding new valuation:', newValuation);
      await accountApi.addValuation(accountId, newValuation);
      
      alert('평가 기록이 성공적으로 수정되었습니다!');
      onClose();
      if (onValuationUpdated) {
        onValuationUpdated();
      }
    } catch (error) {
      console.error('Error updating valuation:', error);
      const errorMessage = error.response?.data?.detail || error.message || '알 수 없는 오류';
      alert('평가 기록 수정 중 오류가 발생했습니다: ' + errorMessage);
    }
  };

  if (!isOpen) return null;

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>평가 기록 수정</h2>
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <label htmlFor="edit-transaction-type">거래 타입</label>
            <select
              id="edit-transaction-type"
              name="transaction_type"
              value={formData.transaction_type}
              onChange={handleChange}
            >
              <option value="buy">매수</option>
              <option value="sell">매도</option>
              <option value="valuation">평가</option>
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-evaluated-amount">평가 금액</label>
            <input
              type="number"
              id="edit-evaluated-amount"
              name="evaluated_amount"
              value={formData.evaluated_amount}
              onChange={handleChange}
              min="0"
              step="any"
              placeholder="평가 금액을 입력하세요"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="edit-evaluation-date">평가 날짜</label>
            <input
              type="date"
              id="edit-evaluation-date"
              name="evaluation_date"
              value={formData.evaluation_date}
              onChange={handleChange}
              required
            />
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
          
          <ButtonGroup>
            <Button type="button" className="secondary" onClick={onClose}>
              취소
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

export default EditValuationModal;

