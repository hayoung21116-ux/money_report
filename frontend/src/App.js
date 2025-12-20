import React, { useState } from 'react';
import styled from 'styled-components';
import { Routes, Route } from 'react-router-dom';
import AccountList from './components/AccountList';
import AccountDetail from './components/AccountDetail';
import Stats from './components/Stats';
import AddAccountModal from './components/AddAccountModal';
import AddSalaryModal from './components/AddSalaryModal';

const AppContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'NanumSquare', sans-serif;
  position: relative;
  min-height: 100vh;
  
  @media (max-width: 768px) {
    padding: 10px;
  }
`;

const Header = styled.header`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 14px 0;
  
  h1 {
    color: #333;
    font-size: 20px;
    font-weight: bold;
    margin: 0;
  }
  
  .header-buttons {
    display: flex;
    gap: 10px;
  }
  
  .header-button {
    padding: 8px 16px;
    font-weight: bold;
    border-radius: 4px;
    cursor: pointer;
    border: none;
    background-color: #007bff;
    color: white;
    
    &:hover {
      background-color: #0056b3;
    }
  }
  
  @media (max-width: 768px) {
    h1 {
      font-size: 18px;
    }
    
    .header-button {
      padding: 6px 12px;
      font-size: 14px;
    }
  }
`;

const Navigation = styled.nav`
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  border-bottom: 1px solid #ddd;
  padding-bottom: 10px;
  
  a {
    text-decoration: none;
    color: #007bff;
    font-weight: bold;
    padding: 10px 0;
    
    &.active {
      color: #000;
      border-bottom: 3px solid #007bff;
    }
  }
  
  @media (max-width: 768px) {
    gap: 15px;
    overflow-x: auto;
    
    a {
      white-space: nowrap;
    }
  }
`;

function App() {
  const [isAddAccountModalOpen, setIsAddAccountModalOpen] = useState(false);
  const [isAddSalaryModalOpen, setIsAddSalaryModalOpen] = useState(false);

  // Listen for custom event to open add account modal
  React.useEffect(() => {
    const handleOpenModal = () => setIsAddAccountModalOpen(true);
    window.addEventListener('openAddAccountModal', handleOpenModal);
    return () => window.removeEventListener('openAddAccountModal', handleOpenModal);
  }, []);

  const handleAddAccount = () => {
    setIsAddAccountModalOpen(true);
  };

  const handleAddSalary = () => {
    setIsAddSalaryModalOpen(true);
  };

  const handleAccountAdded = () => {
    // Refresh the account list
    window.location.reload();
  };

  const handleSalaryAdded = () => {
    // Refresh the stats page if it's currently open
    window.location.reload();
  };

  return (
    <AppContainer>
      <Header>
        <h1>가계부</h1>
        <div className="header-buttons">
          <button className="header-button" onClick={handleAddSalary}>$월</button>
          <button className="header-button" onClick={handleAddAccount}>계좌 추가</button>
        </div>
      </Header>

      <Navigation>
        <a href="/">계좌 목록</a>
        <a href="/stats">통계</a>
      </Navigation>

      <Routes>
        <Route path="/" element={<AccountList />} />
        <Route path="/account/:id" element={<AccountDetail />} />
        <Route path="/stats" element={<Stats />} />
      </Routes>

      <AddAccountModal
        isOpen={isAddAccountModalOpen}
        onClose={() => setIsAddAccountModalOpen(false)}
        onAccountAdded={handleAccountAdded}
      />

      <AddSalaryModal
        isOpen={isAddSalaryModalOpen}
        onClose={() => setIsAddSalaryModalOpen(false)}
        onSalaryAdded={handleSalaryAdded}
      />
    </AppContainer>
  );
}

export default App;
