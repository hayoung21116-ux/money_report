import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import styled from 'styled-components';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { accountApi, formatCurrency } from '../services/api.js';
import AddTransactionModal from './AddTransactionModal.js';
import EditAccountModal from './EditAccountModal.js';
import DeleteAccountDialog from './DeleteAccountDialog.js';
import DeactivateAccountDialog from './DeactivateAccountDialog.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const AccountDetailContainer = styled.div`
  .account-header {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    margin-bottom: 30px;
    
    h2 {
      margin-top: 0;
      color: #333;
      margin-bottom: 0; /* Remove bottom margin to align better in flex container */
    }

    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 15px;
    }

    .header-actions {
      display: flex;
      gap: 10px;
    }
    
    .account-info {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
      margin-top: 15px;
    }
    
    .info-item {
      flex: 1;
      min-width: 200px;
      
      .label {
        font-weight: 600;
        color: #666;
        margin-bottom: 5px;
      }
      
      .value {
        font-size: 1.2rem;
        font-weight: 700;
      }
    }
  }
  
  .tabs-container {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow: hidden;
  }
  
  .tabs-header {
    display: flex;
    border-bottom: 2px solid #e0e0e0;
    background-color: #f8f9fa;
    
    .tab-button {
      flex: 1;
      padding: 15px 20px;
      background: none;
      border: none;
      cursor: pointer;
      font-size: 16px;
      font-weight: 600;
      color: #666;
      transition: all 0.3s;
      border-bottom: 3px solid transparent;
      
      &:hover {
        background-color: #e9ecef;
        color: #333;
      }
      
      &.active {
        color: #007bff;
        border-bottom-color: #007bff;
        background-color: white;
      }
    }
  }
  
  .tab-content {
    padding: 20px;
  }
  
  .transactions-table {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    overflow-x: auto;
    
    .transactions-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h3 {
        margin: 0;
      }
    }
  }
  
  .chart-container {
    padding: 20px;
    min-height: 400px;
  }
  
  .action-buttons {
    gap: 10px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    /* .action-buttons class might be unused now, but keeping generic styles just in case, 
       or we can repurpose .action-button styles which are effectively global in this scope */
  }
  
  .action-button {
    padding: 10px 15px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    
    &:hover {
      background-color: #0056b3;
    }
    
    &.edit {
      background-color: #28a745;
      
      &:hover {
        background-color: #218838;
      }
    }
    
    &.delete {
      background-color: #dc3545;
      
      &:hover {
        background-color: #c82333;
      }
    }
    
    &.deactivate {
      background-color: #ffc107;
      color: #212529;
      
      &:hover {
        background-color: #e0a800;
      }
    }
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    
    th, td {
      padding: 12px 15px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }
    
    th {
      background-color: #f8f9fa;
      font-weight: 600;
    }
    
    // Set column widths
    th:nth-child(1), td:nth-child(1) { // 타입
      width: 5%;
    }
    th:nth-child(2), td:nth-child(2) { // 금액
      width: 5%;
    }
    th:nth-child(3), td:nth-child(3) { // 메모
      width: 40%;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    th:nth-child(4), td:nth-child(4) { // 날짜
      width: 10%;
    }
    
    tr:hover {
      background-color: #f5f5f5;
    }
    
    .income {
      color: #28a745;
    }
    
    .expense {
      color: #dc3545;
    }
    
    .transfer {
      background-color: #fffacd;
    }
    
    .valuation {
      background-color: #e7f3ff;
    }
    
    .valuation-type {
      color: #0066cc;
      font-weight: 600;
    }
  }
  
  @media (max-width: 768px) {
    .account-header {
      padding: 15px;
    }
    
    .transactions-table {
      padding: 15px;
    }
    
    .action-buttons {
      flex-direction: column;
    }
    
    .action-button {
      width: 100%;
      margin-bottom: 10px;
    }
    
    table {
      font-size: 0.9rem;
      
      th, td {
        padding: 8px 10px;
      }
    }
  }
`;

function AccountDetail() {
  const { id } = useParams();
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [valuations, setValuations] = useState([]);
  const [activeTab, setActiveTab] = useState('transactions'); // 'transactions' or 'chart'
  const [isAddTransactionModalOpen, setIsAddTransactionModalOpen] = useState(false);
  const [isEditAccountModalOpen, setIsEditAccountModalOpen] = useState(false);
  const [isDeleteAccountDialogOpen, setIsDeleteAccountDialogOpen] = useState(false);
  const [isDeactivateAccountDialogOpen, setIsDeactivateAccountDialogOpen] = useState(false);

  useEffect(() => {
    fetchAccountDetails();
  }, [id]);

  const fetchAccountDetails = async () => {
    try {
      const [accountResponse, transactionsResponse] = await Promise.all([
        accountApi.getAccount(id),
        accountApi.getTransactions(id)
      ]);

      const accountData = accountResponse.data;
      setAccount(accountData);
      setTransactions(transactionsResponse.data);
      
      // Fetch valuations if it's an investment account
      if (accountData.type === '투자') {
        try {
          const valuationsResponse = await accountApi.getValuations(id);
          setValuations(valuationsResponse.data || []);
        } catch (error) {
          console.error('Error fetching valuations:', error);
          setValuations([]);
        }
      } else {
        setValuations([]);
      }
    } catch (error) {
      console.error('Error fetching account details:', error);
    }
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

  const handleAddTransaction = () => {
    setIsAddTransactionModalOpen(true);
  };

  const handleTransactionAdded = () => {
    // Refresh the transaction list
    fetchAccountDetails();
  };

  const handleEditAccount = () => {
    setIsEditAccountModalOpen(true);
  };

  const handleAccountUpdated = () => {
    // Refresh the account details
    fetchAccountDetails();
  };

  const handleDeleteAccount = () => {
    setIsDeleteAccountDialogOpen(true);
  };

  const handleDeleteAccountConfirm = async () => {
    try {
      // In a real implementation, we would call the API to delete the account
      // await accountApi.deleteAccount(id);
      // onClose();
      // window.location.href = '/'; // Navigate back to account list

      // For now, we'll just simulate the API call
      console.log('Deleting account with id:', id);
      alert('계좌가 성공적으로 삭제되었습니다!');
      setIsDeleteAccountDialogOpen(false);
      // In a real implementation, we would navigate back to the account list
      // window.location.href = '/';
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('계좌 삭제 중 오류가 발생했습니다.');
    }
  };

  const handleDeactivateAccount = () => {
    setIsDeactivateAccountDialogOpen(true);
  };

  const handleDeactivateAccountConfirm = async () => {
    try {
      // In a real implementation, we would call the API to deactivate the account
      // await accountApi.toggleAccountStatus(id);
      // onClose();
      // fetchAccountDetails(); // Refresh the account details

      // For now, we'll just simulate the API call
      console.log('Toggling account status with id:', id);
      const action = account.status === 'dead' ? '활성화' : '비활성화';
      alert(`계좌가 성공적으로 ${action}되었습니다!`);
      setIsDeactivateAccountDialogOpen(false);
      // In a real implementation, we would refresh the account details
      // fetchAccountDetails();
    } catch (error) {
      console.error('Error toggling account status:', error);
      const action = account.status === 'dead' ? '활성화' : '비활성화';
      alert(`계좌 ${action} 중 오류가 발생했습니다.`);
    }
  };

  const calculateReturnRateData = () => {
    if (!account || account.type !== '투자' || valuations.length === 0) {
      return null;
    }

    // Sort valuations by date
    const sortedValuations = [...valuations].sort((a, b) => 
      new Date(a.evaluation_date) - new Date(b.evaluation_date)
    );

    // Calculate return rate for each valuation point
    const labels = [];
    const returnRates = [];
    const baseAmount = account.purchase_amount || 0;
    
    sortedValuations.forEach((valuation) => {
      const date = new Date(valuation.evaluation_date);
      labels.push(date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' }));
      
      // Calculate return rate: ((current_value - purchase_amount) / purchase_amount) * 100
      if (baseAmount > 0) {
        const returnRate = ((valuation.evaluated_amount - baseAmount) / baseAmount) * 100;
        returnRates.push(returnRate);
      } else {
        // If no purchase amount, show 0% or calculate from first valuation
        returnRates.push(0);
      }
    });

    return {
      labels,
      datasets: [
        {
          label: '수익률 (%)',
          data: returnRates,
          borderColor: account.color || '#007bff',
          backgroundColor: `${account.color || '#007bff'}20`,
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6,
        }
      ]
    };
  };

  const chartData = calculateReturnRateData();

  if (!account) {
    return <div>Loading...</div>;
  }

  const isInvestmentAccount = account.type === '투자';

  return (
    <AccountDetailContainer>
      <div className="account-header">

        <div className="header-top">
          <h2>{account.name} ({account.type})</h2>
          <div className="header-actions">
            <button className="action-button edit" onClick={handleEditAccount}>계좌 수정</button>
            <button className="action-button deactivate" onClick={handleDeactivateAccount}>
              {account.status === 'dead' ? '계좌 활성화' : '계좌 비활성화'}
            </button>
            <button className="action-button delete" onClick={handleDeleteAccount}>계좌 삭제</button>
          </div>
        </div>
        <div className="account-info">
          {account.type === '투자' ? (
            <>
              <div className="info-item">
                <div className="label">자산</div>
                <div className="value">{formatCurrency(account.asset_value)}</div>
              </div>
              <div className="info-item">
                <div className="label">매입금액</div>
                <div className="value">{formatCurrency(account.purchase_amount)}</div>
              </div>
              <div className="info-item">
                <div className="label">평가금액</div>
                <div className="value">{formatCurrency(account.evaluated_amount)}</div>
              </div>
              <div className="info-item">
                <div className="label">수익률</div>
                <div className="value">{account.return_rate != null ? account.return_rate.toFixed(2) : '0.00'}%</div>
              </div>
            </>
          ) : (
            <>
              <div className="info-item">
                <div className="label">잔액</div>
                <div className="value">{formatCurrency(calculateBalance(account))}</div>
              </div>
            </>
          )}
        </div>
      </div>

      {isInvestmentAccount ? (
        <div className="tabs-container">
          <div className="tabs-header">
            <button
              className={`tab-button ${activeTab === 'transactions' ? 'active' : ''}`}
              onClick={() => setActiveTab('transactions')}
            >
              거래 내역
            </button>
            <button
              className={`tab-button ${activeTab === 'chart' ? 'active' : ''}`}
              onClick={() => setActiveTab('chart')}
            >
              수익률 차트
            </button>
          </div>
          <div className="tab-content">
            {activeTab === 'transactions' ? (
              <div className="transactions-table">
                <div className="transactions-header">
                  <h3>거래 내역</h3>
                  <button className="action-button" onClick={handleAddTransaction}>거래 추가</button>
                </div>
                {(transactions.length > 0 || valuations.length > 0) ? (
                  <table>
                    <thead>
                      <tr>
                        <th>타입</th>
                        <th>금액</th>
                        <th>메모</th>
                        <th>날짜</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        // Combine transactions and valuations, sorted by date
                        ...transactions.map(t => ({ ...t, itemType: 'transaction' })),
                        ...valuations.map(v => ({ ...v, itemType: 'valuation' }))
                      ]
                        .sort((a, b) => {
                          const dateA = a.itemType === 'transaction' ? a.date : a.evaluation_date;
                          const dateB = b.itemType === 'transaction' ? b.date : b.evaluation_date;
                          return new Date(dateB) - new Date(dateA); // 최신순
                        })
                        .map(item => {
                          if (item.itemType === 'transaction') {
                            return (
                              <tr key={item.id} className={item.category === '이동' ? 'transfer' : ''}>
                                <td className={item.type === 'income' ? 'income' : 'expense'}>
                                  {item.type === 'income' ? '수입' : '지출'}
                                </td>
                                <td>{formatCurrency(item.amount)}</td>
                                <td>{item.memo}</td>
                                <td>{item.date.substring(0, 10)}</td>
                              </tr>
                            );
                          } else {
                            // Valuation record
                            const typeLabel = item.transaction_type === 'buy' ? '매수' : 
                                            item.transaction_type === 'sell' ? '매도' : '평가';
                            return (
                              <tr key={item.id} className="valuation">
                                <td className="valuation-type">{typeLabel}</td>
                                <td>{formatCurrency(item.evaluated_amount)}</td>
                                <td>{item.memo || '-'}</td>
                                <td>{item.evaluation_date.substring(0, 10)}</td>
                              </tr>
                            );
                          }
                        })}
                    </tbody>
                  </table>
                ) : (
                  <p>거래 내역이 없습니다.</p>
                )}
              </div>
            ) : (
              <div className="chart-container">
                <h3>수익률 추이</h3>
                {chartData && valuations.length > 0 ? (
                  <Line
                    data={chartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: true,
                      plugins: {
                        legend: {
                          display: true,
                          position: 'top',
                        },
                        tooltip: {
                          mode: 'index',
                          intersect: false,
                          callbacks: {
                            label: function(context) {
                              return `수익률: ${context.parsed.y.toFixed(2)}%`;
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: false,
                          ticks: {
                            callback: function(value) {
                              return value.toFixed(2) + '%';
                            }
                          },
                          title: {
                            display: true,
                            text: '수익률 (%)'
                          }
                        },
                        x: {
                          title: {
                            display: true,
                            text: '날짜'
                          }
                        }
                      }
                    }}
                  />
                ) : (
                  <p>수익률 데이터가 없습니다. 평가 기록을 추가해주세요.</p>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="transactions-table">
          <div className="transactions-header">
            <h3>거래 내역</h3>
            <button className="action-button" onClick={handleAddTransaction}>거래 추가</button>
          </div>
          {transactions.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>타입</th>
                  <th>금액</th>
                  <th>카테고리</th>
                  <th>메모</th>
                  <th>날짜</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map(transaction => (
                  <tr key={transaction.id} className={transaction.category === '이동' ? 'transfer' : ''}>
                    <td className={transaction.type === 'income' ? 'income' : 'expense'}>
                      {transaction.type === 'income' ? '수입' : '지출'}
                    </td>
                    <td>{formatCurrency(transaction.amount)}</td>
                    <td>{transaction.category}</td>
                    <td>{transaction.memo}</td>
                    <td>{transaction.date.substring(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>거래 내역이 없습니다.</p>
          )}
        </div>
      )}

      <AddTransactionModal
        isOpen={isAddTransactionModalOpen}
        onClose={() => setIsAddTransactionModalOpen(false)}
        accountId={id}
        onTransactionAdded={handleTransactionAdded}
        accountType={account.type}
      />

      <EditAccountModal
        isOpen={isEditAccountModalOpen}
        onClose={() => setIsEditAccountModalOpen(false)}
        account={account}
        onAccountUpdated={handleAccountUpdated}
      />

      <DeleteAccountDialog
        isOpen={isDeleteAccountDialogOpen}
        onClose={() => setIsDeleteAccountDialogOpen(false)}
        onConfirm={handleDeleteAccountConfirm}
        accountName={account.name}
      />

      <DeactivateAccountDialog
        isOpen={isDeactivateAccountDialogOpen}
        onClose={() => setIsDeactivateAccountDialogOpen(false)}
        onConfirm={handleDeactivateAccountConfirm}
        accountName={account.name}
        isActivating={account.status === 'dead'}
      />
    </AccountDetailContainer>
  );
}

export default AccountDetail;
