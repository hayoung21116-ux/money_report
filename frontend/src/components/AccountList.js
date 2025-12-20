import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { accountApi, statsApi, formatCurrency, getTextColor } from '../services/api';

const AccountGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(auto-fill, minmax(100%, 1fr));
    gap: 15px;
  }
`;

const AccountCard = styled.div`
  background-color: ${props => props.color || '#f8f9fa'};
  border-radius: 16px;
  height: 100px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 16px 16px 16px 16px;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
  
  .account-icon {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    font-weight: 800;
    font-size: 16px;
    color: #000000;
  }
  
  .account-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  
  .account-name {
    font-size: 14px;
    font-weight: 400;
    margin-bottom: 4px;
    color: ${props => props.textColor || '#333'};
  }
  
  .account-balance {
    font-size: 22px;
    font-weight: 800;
    color: ${props => props.textColor || '#333'};
  }
`;

const AddAccountButton = styled.button`
  background-color: #28a745;
  color: white;
  border: none;
  border-radius: 50%;
  width: 60px;
  height: 60px;
  font-size: 2rem;
  cursor: pointer;
  position: fixed;
  bottom: 30px;
  right: 30px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease-in-out;
  
  &:hover {
    background-color: #218838;
    transform: scale(1.1);
  }
`;

const TotalAssets = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 30px;
  
  .total-amount {
    font-size: 1.8rem;
    font-weight: 700;
    color: #007bff;
    text-align: center;
  }
`;

function AccountList() {
  const [accounts, setAccounts] = useState([]);
  const [totalAssets, setTotalAssets] = useState(0);
  const [totalCash, setTotalCash] = useState(0);

  useEffect(() => {
    fetchAccounts();
    fetchTotalAssets();
  }, []);

  const fetchAccounts = async () => {
    try {
      console.log('Fetching accounts...'); // Debug log
      const response = await accountApi.getAllAccounts();
      console.log('Accounts API response:', response); // Debug log
      console.log('Accounts data:', response.data); // Debug log
      
      if (!response.data || !Array.isArray(response.data)) {
        console.error('Invalid accounts data received:', response.data);
        return;
      }
      
      // Sort accounts to match the desktop app behavior
      const sortedAccounts = response.data.sort((a, b) => {
        // First by status (active first)
        if (a.status === "dead" && b.status !== "dead") return 1;
        if (a.status !== "dead" && b.status === "dead") return -1;
        
        // Then by type order
        const typeOrder = {"현금": 0, "투자": 1, "소비": 2};
        const aTypeOrder = typeOrder[a.type] !== undefined ? typeOrder[a.type] : 3;
        const bTypeOrder = typeOrder[b.type] !== undefined ? typeOrder[b.type] : 3;
        if (aTypeOrder !== bTypeOrder) return aTypeOrder - bTypeOrder;
        
        // Finally by name (민규 first)
        const aHasMinGyu = a.name.includes("민규") ? 0 : 1;
        const bHasMinGyu = b.name.includes("민규") ? 0 : 1;
        return aHasMinGyu - bHasMinGyu;
      });
      console.log('Sorted accounts:', sortedAccounts); // Debug log
      setAccounts(sortedAccounts);
    } catch (error) {
      console.error('Error fetching accounts:', error);
      console.error('Error details:', error.response?.data || error.message);
    }
  };

  const fetchTotalAssets = async () => {
    try {
      const [assetsResponse, cashResponse] = await Promise.all([
        statsApi.getTotalAssets(),
        statsApi.getTotalCash()
      ]);
      setTotalAssets(assetsResponse.data.total_assets);
      setTotalCash(cashResponse.data.total_cash);
    } catch (error) {
      console.error('Error fetching total assets:', error);
    }
  };

  const formatCurrency = (amount) => {
    if (amount === undefined || amount === null) return '₩0';
    return `₩${amount.toLocaleString()}`;
  };

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

  return (
    <div>
      <TotalAssets>
        <div className="total-amount">
          총 자산: {formatCurrency(totalAssets)} / 현금: {formatCurrency(totalCash)}
        </div>
      </TotalAssets>
      
      <AccountGrid>
        {accounts.map(account => {
          const bgColor = account.status === "dead" ? "#808080" : account.color;
          const textColor = getTextColor(bgColor);
          console.log(`Account ${account.name}: bgColor=${bgColor}, textColor=${textColor}`); // Debug log
          return (
            <AccountCard 
              key={account.id}
              color={bgColor}
              textColor={textColor}
              onClick={() => window.location.href = `#/account/${account.id}`}
            >
              <div className="account-icon">
                {account.name.charAt(0)}
              </div>
              <div className="account-info">
                <div className="account-name">{account.name}</div>
                <div className="account-balance">
                  {account.type === '투자' 
                    ? formatCurrency(account.asset_value) 
                    : formatCurrency(calculateBalance(account))}
                </div>
              </div>
            </AccountCard>
          );
        })}
      </AccountGrid>
      
      <AddAccountButton onClick={() => alert('계좌 추가 기능은 다음 단계에서 구현됩니다.')}>
        +
      </AddAccountButton>
    </div>
  );
}

export default AccountList;
