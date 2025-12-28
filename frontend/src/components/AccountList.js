import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { accountApi, statsApi, formatCurrency, getTextColor } from '../services/api';

const AccountSection = styled.div`
  margin-bottom: 30px;
`;

const AccountTypeHeader = styled.h3`
  margin: 0 0 15px 0;
  padding: 0;
  color: #333;
  font-size: 1.2rem;
  font-weight: 600;
`;

const AccountGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  
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
  const navigate = useNavigate();
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

      // 투자 계좌의 valuations를 가져오기
      const accountsWithValuations = await Promise.all(
        response.data.map(async (account) => {
          if (account.type === '투자') {
            try {
              const valuationsResponse = await accountApi.getValuations(account.id);
              return {
                ...account,
                valuations: valuationsResponse.data || []
              };
            } catch (error) {
              console.error(`Error fetching valuations for account ${account.id}:`, error);
              return {
                ...account,
                valuations: []
              };
            }
          }
          return account;
        })
      );

      // Sort accounts to match the desktop app behavior
      const sortedAccounts = accountsWithValuations.sort((a, b) => {
        // First by status (active first)
        if (a.status === "dead" && b.status !== "dead") return 1;
        if (a.status !== "dead" && b.status === "dead") return -1;

        // Then by type order
        const typeOrder = { "현금": 0, "투자": 1, "소비": 2 };
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

  const calculateInvestmentAsset = (account) => {
    console.log(`Calculating asset for ${account.name}:`, {
      valuations: account.valuations?.length || 0,
      asset_value: account.asset_value,
      evaluated_amount: account.evaluated_amount
    });
    
    // valuations가 없거나 빈 배열이면 기존 값 사용
    if (!account.valuations || account.valuations.length === 0) {
      // asset_value가 있으면 사용, 없으면 evaluated_amount 사용
      const fallbackValue = account.asset_value || account.evaluated_amount || 0;
      console.log(`No valuations, using fallback: ${fallbackValue}`);
      return fallbackValue;
    }

    // Sort valuations by date
    const sortedValuations = [...account.valuations].sort((a, b) => 
      new Date(a.evaluation_date) - new Date(b.evaluation_date)
    );

    // AccountDetail과 동일한 그룹화 로직 사용
    const groups = [];
    let currentGroup = { buys: [] };

    sortedValuations.forEach((valuation) => {
      if (valuation.transaction_type === 'buy') {
        currentGroup.buys.push({
          date: new Date(valuation.evaluation_date),
          amount: valuation.evaluated_amount,
          valuation: valuation
        });
      } else if (valuation.transaction_type === 'sell') {
        if (currentGroup.buys.length > 0) {
          currentGroup.sell = {
            date: new Date(valuation.evaluation_date),
            amount: valuation.evaluated_amount,
            valuation: valuation
          };
          groups.push(currentGroup);
          currentGroup = { buys: [] };
        }
      }
    });

    if (currentGroup.buys.length > 0) {
      groups.push(currentGroup);
    }

    // 누적 금액 계산 (AccountDetail과 동일한 로직)
    let cumulativeAmount = 0;
    groups.forEach((group) => {
      if (group.sell) {
        const totalBuyAmount = group.buys.reduce((sum, buy) => sum + buy.amount, 0);
        const buyCumulativeAmount = cumulativeAmount + totalBuyAmount;
        cumulativeAmount = buyCumulativeAmount - totalBuyAmount + group.sell.amount;
      } else {
        const totalBuyAmount = group.buys.reduce((sum, buy) => sum + buy.amount, 0);
        cumulativeAmount += totalBuyAmount;
      }
    });

    console.log(`Calculated cumulative amount: ${cumulativeAmount}`);
    return cumulativeAmount;
  };

  const calculateBalance = (account) => {
    if (account.type === '투자') {
      // 투자 계좌는 자산 계산 로직 사용
      return calculateInvestmentAsset(account);
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

  // Separate active and dead accounts
  const activeAccounts = accounts.filter(account => account.status !== "dead");
  const deadAccounts = accounts.filter(account => account.status === "dead");
  
  // Categorize investment accounts
  const categorizeInvestmentAccount = (account) => {
    const name = account.name;
    if (name.includes("연금")) return "연금";
    if (name.includes("코인")) return "코인";
    if (name.includes("주식") || name.includes("증권") || name.includes("나무") || 
        name.includes("한국투자") || name.includes("IBK") || name.includes("OK저축은행")) {
      return "주식";
    }
    return "기타";
  };

  // Group active accounts by type
  const groupedActiveAccounts = activeAccounts.reduce((groups, account) => {
    const type = account.type;
    if (!groups[type]) {
      groups[type] = [];
    }
    groups[type].push(account);
    return groups;
  }, {});

  // Sort investment accounts by category
  if (groupedActiveAccounts["투자"]) {
    groupedActiveAccounts["투자"].sort((a, b) => {
      const categoryA = categorizeInvestmentAccount(a);
      const categoryB = categorizeInvestmentAccount(b);
      
      // Define category order
      const categoryOrder = { "주식": 0, "연금": 1, "코인": 2, "기타": 3 };
      const orderA = categoryOrder[categoryA] !== undefined ? categoryOrder[categoryA] : 4;
      const orderB = categoryOrder[categoryB] !== undefined ? categoryOrder[categoryB] : 4;
      
      if (orderA !== orderB) {
        return orderA - orderB;
      }
      
      // If same category, sort by name
      return a.name.localeCompare(b.name);
    });
  }

  return (
    <div>
      <TotalAssets>
        <div className="total-amount">
          총 자산: {formatCurrency(totalAssets)} / 현금: {formatCurrency(totalCash)}
        </div>
      </TotalAssets>

      {Object.entries(groupedActiveAccounts).map(([type, accountsOfType]) => (
        <AccountSection key={type}>
          <AccountTypeHeader>{type} 계좌</AccountTypeHeader>
          <AccountGrid>
            {accountsOfType.map(account => {
              const bgColor = account.color;
              const textColor = getTextColor(bgColor);
              console.log(`Account ${account.name}: bgColor=${bgColor}, textColor=${textColor}`); // Debug log
              return (
                <AccountCard
                  key={account.id}
                  color={bgColor}
                  textColor={textColor}
                  onClick={() => navigate(`/account/${account.id}`)}
                >
                  <div className="account-icon">
                    {account.name.charAt(0)}
                  </div>
                  <div className="account-info">
                    <div className="account-name">{account.name}</div>
                    <div className="account-balance">
                      {formatCurrency(calculateBalance(account))}
                    </div>
                  </div>
                </AccountCard>
              );
            })}
          </AccountGrid>
        </AccountSection>
      ))}

      {deadAccounts.length > 0 && (
        <AccountSection>
          <AccountTypeHeader>비활성화된 계좌</AccountTypeHeader>
          <AccountGrid>
            {deadAccounts.map(account => {
              const bgColor = "#808080";
              const textColor = getTextColor(bgColor);
              return (
                <AccountCard
                  key={account.id}
                  color={bgColor}
                  textColor={textColor}
                  onClick={() => navigate(`/account/${account.id}`)}
                >
                  <div className="account-icon">
                    {account.name.charAt(0)}
                  </div>
                  <div className="account-info">
                    <div className="account-name">{account.name}</div>
                    <div className="account-balance">
                      {formatCurrency(calculateBalance(account))}
                    </div>
                  </div>
                </AccountCard>
              );
            })}
          </AccountGrid>
        </AccountSection>
      )}

      <AddAccountButton onClick={() => window.dispatchEvent(new CustomEvent('openAddAccountModal'))}>
        +
      </AddAccountButton>
    </div>
  );
}

export default AccountList;
