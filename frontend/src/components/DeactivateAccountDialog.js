import React from 'react';
import styled from 'styled-components';

const DialogOverlay = styled.div`
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

const DialogContent = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  width: 100%;
  max-width: 400px;
  
  h2 {
    margin-top: 0;
    color: #333;
  }
  
  p {
    font-size: 16px;
    color: #666;
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
    background-color: #ffc107;
    color: #212529;
    
    &:hover {
      background-color: #e0a800;
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

function DeactivateAccountDialog({ isOpen, onClose, onConfirm, accountName, isActivating }) {
  if (!isOpen) return null;

  return (
    <DialogOverlay onClick={onClose}>
      <DialogContent onClick={e => e.stopPropagation()}>
        <h2>{isActivating ? '계좌 활성화' : '계좌 비활성화'}</h2>
        <p>"{accountName}" 계좌를 {isActivating ? '활성화' : '비활성화'}하시겠습니까?</p>
        <ButtonGroup>
          <Button type="button" className="secondary" onClick={onClose}>
            취소
          </Button>
          <Button type="button" className="primary" onClick={onConfirm}>
            {isActivating ? '활성화' : '비활성화'}
          </Button>
        </ButtonGroup>
      </DialogContent>
    </DialogOverlay>
  );
}

export default DeactivateAccountDialog;
