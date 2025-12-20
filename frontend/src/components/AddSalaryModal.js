import React, { useState } from 'react';
import styled from 'styled-components';
import { statsApi } from '../services/api';

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

function AddSalaryModal({ isOpen, onClose, onSalaryAdded }) {
  const currentYear = new Date().getFullYear();
  const [formData, setFormData] = useState({
    amount: 0,
    year: currentYear.toString(),
    month: (new Date().getMonth() + 1).toString(),
    person: '민규',
    classification: '월급'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'amount' ? parseFloat(value) || 0 : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Combine year and month for API call
      const month = `${formData.year}-${formData.month.toString().padStart(2, '0')}`;
      
      // Call the API to add the salary
      await statsApi.addSalary(formData.amount, month, formData.person, formData.classification);
      
      console.log('Salary added successfully');
      alert('월급이 성공적으로 추가되었습니다!');
      onClose();
      onSalaryAdded();
    } catch (error) {
      console.error('Error adding salary:', error);
      alert('월급 추가 중 오류가 발생했습니다.');
    }
  };

  if (!isOpen) return null;

  // Generate year options (2020-2040)
  const yearOptions = [];
  for (let year = 2020; year <= 2040; year++) {
    yearOptions.push(
      <option key={year} value={year}>
        {year}년
      </option>
    );
  }

  // Generate month options (1-12)
  const monthOptions = [];
  for (let month = 1; month <= 12; month++) {
    monthOptions.push(
      <option key={month} value={month}>
        {month}월
      </option>
    );
  }

  return (
    <ModalOverlay onClick={onClose}>
      <ModalContent onClick={e => e.stopPropagation()}>
        <h2>월급 입력</h2>
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <label htmlFor="year">년</label>
            <select
              id="year"
              name="year"
              value={formData.year}
              onChange={handleChange}
            >
              {yearOptions}
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="month">월</label>
            <select
              id="month"
              name="month"
              value={formData.month}
              onChange={handleChange}
            >
              {monthOptions}
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="person">이름</label>
            <select
              id="person"
              name="person"
              value={formData.person}
              onChange={handleChange}
            >
              <option value="민규">민규</option>
              <option value="하영">하영</option>
            </select>
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="amount">금액</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              min="0"
              placeholder="금액을 입력하세요"
              required
            />
          </FormGroup>
          
          <FormGroup>
            <label htmlFor="classification">구분</label>
            <select
              id="classification"
              name="classification"
              value={formData.classification}
              onChange={handleChange}
            >
              <option value="월급">월급</option>
              <option value="보너스">보너스</option>
            </select>
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

export default AddSalaryModal;
