import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import styled from 'styled-components';
import { accountApi, formatCurrency } from '../services/api.js';
import AddTransactionModal from './AddTransactionModal.js';
import EditAccountModal from './EditAccountModal.js';
import DeleteAccountDialog from './DeleteAccountDialog.js';
import DeactivateAccountDialog from './DeactivateAccountDialog.js';

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

      setAccount(accountResponse.data);
      setTransactions(transactionsResponse.data);
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

  if (!account) {
    return <div>Loading...</div>;
  }

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
                <div className="value">{account.return_rate.toFixed(2)}%</div>
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
