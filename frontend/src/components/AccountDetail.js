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
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { accountApi, formatCurrency } from '../services/api.js';
import AddTransactionModal from './AddTransactionModal.js';
import EditTransactionModal from './EditTransactionModal.js';
import EditValuationModal from './EditValuationModal.js';
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
  Filler,
  ChartDataLabels
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
    
    tr:hover {
      background-color: #f5f5f5;
    }
    
    tr[style*="cursor: pointer"]:hover {
      background-color: #e3f2fd;
      transform: scale(1.01);
      transition: all 0.2s;
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
  
  // Investment account table (4 columns)
  .investment-transactions-table {
    // Set column widths for 4 columns
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
  }
  
  // Cash account table (5 columns)
  .cash-transactions-table {
    // Set column widths for 5 columns with memo column being the widest
    th:nth-child(1), td:nth-child(1) { // 타입
      width: 5%;
    }
    th:nth-child(2), td:nth-child(2) { // 금액
      width: 10%;
    }
    th:nth-child(3), td:nth-child(3) { // 카테고리
      width: 10%;
    }
    th:nth-child(4), td:nth-child(4) { // 메모
      width: 40%;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    th:nth-child(5), td:nth-child(5) { // 날짜
      width: 10%;
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
  const [isEditTransactionModalOpen, setIsEditTransactionModalOpen] = useState(false);
  const [isEditValuationModalOpen, setIsEditValuationModalOpen] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState(null);
  const [selectedValuation, setSelectedValuation] = useState(null);
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

  const handleTransactionClick = (transaction) => {
    setSelectedTransaction(transaction);
    setIsEditTransactionModalOpen(true);
  };

  const handleTransactionUpdated = () => {
    fetchAccountDetails();
    setIsEditTransactionModalOpen(false);
    setSelectedTransaction(null);
  };

  const handleValuationClick = (valuation) => {
    setSelectedValuation(valuation);
    setIsEditValuationModalOpen(true);
  };

  const handleValuationUpdated = () => {
    fetchAccountDetails();
    setIsEditValuationModalOpen(false);
    setSelectedValuation(null);
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
      await accountApi.toggleAccountStatus(id);
      setIsDeactivateAccountDialogOpen(false);
      fetchAccountDetails(); // Refresh the account details
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

    // Build pairs: 매수-매도 pair만 생성
    const pairs = [];
    const unpairedBuyValuations = []; // 페어링되지 않은 buy 기록들

    sortedValuations.forEach((valuation) => {
      if (valuation.transaction_type === 'buy') {
        // buy 기록은 unpaired 목록에 추가
        unpairedBuyValuations.push(valuation);
      } else if (valuation.transaction_type === 'sell') {
        // sell 기록이면 가장 오래된 unpaired buy와 페어링
        if (unpairedBuyValuations.length > 0) {
          const buyVal = unpairedBuyValuations.shift();
          const sellAmount = valuation.evaluated_amount;
          const buyAmount = buyVal.evaluated_amount;
          const returnRate = ((sellAmount - buyAmount) / buyAmount) * 100;
          
          pairs.push({
            buyDate: buyVal.evaluation_date,
            buyAmount: buyAmount,
            sellDate: valuation.evaluation_date,
            sellAmount: sellAmount,
            returnRate: returnRate,
            buyValuation: buyVal,
            sellValuation: valuation
          });
        }
      } else if (valuation.transaction_type === 'valuation') {
        // valuation 기록이면 가장 오래된 unpaired buy와 페어링
        if (unpairedBuyValuations.length > 0) {
          // 이미 이 buy와 페어링된 pair가 있는지 확인
          const buyVal = unpairedBuyValuations[0];
          let existingPairIndex = -1;
          for (let i = 0; i < pairs.length; i++) {
            if (pairs[i].buyValuation?.id === buyVal.id && pairs[i].sellValuation?.transaction_type === 'valuation') {
              existingPairIndex = i;
              break;
            }
          }
          
          if (existingPairIndex >= 0) {
            // 기존에 valuation과 페어링된 pair가 있으면 제거
            pairs.splice(existingPairIndex, 1);
          } else {
            // 새로운 pair를 만들기 위해 unpaired에서 제거
            unpairedBuyValuations.shift();
          }
          
          // 새로운 valuation과 페어링
          const sellAmount = valuation.evaluated_amount;
          const buyAmount = buyVal.evaluated_amount;
          const returnRate = ((sellAmount - buyAmount) / buyAmount) * 100;
          
          pairs.push({
            buyDate: buyVal.evaluation_date,
            buyAmount: buyAmount,
            sellDate: valuation.evaluation_date,
            sellAmount: sellAmount,
            returnRate: returnRate,
            buyValuation: buyVal,
            sellValuation: valuation
          });
        }
      }
    });

    if (pairs.length === 0 && unpairedBuyValuations.length === 0) {
      return null;
    }

    // 모든 날짜 수집 (매수 날짜, 매도 날짜, 페어링되지 않은 매수 날짜)
    const allDatesSet = new Set();
    pairs.forEach((pair) => {
      allDatesSet.add(new Date(pair.buyDate).getTime());
      allDatesSet.add(new Date(pair.sellDate).getTime());
    });
    unpairedBuyValuations.forEach((buyVal) => {
      allDatesSet.add(new Date(buyVal.evaluation_date).getTime());
    });
    const allDates = Array.from(allDatesSet).map(time => new Date(time)).sort((a, b) => a - b);
    const allLabels = allDates.map(date => 
      date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
    );

    // 각 pair별로 데이터셋 생성
    const datasets = pairs.map((pair, pairIndex) => {
      const buyDate = new Date(pair.buyDate);
      const sellDate = new Date(pair.sellDate);
      
      // 각 날짜에 대한 데이터 포인트 생성 (해당 pair의 두 점에만 값, 나머지는 null)
      const pairData = allDates.map((date) => {
        if (date.getTime() === buyDate.getTime()) {
          return pair.buyAmount;
        } else if (date.getTime() === sellDate.getTime()) {
          return pair.sellAmount;
        }
        return null;
      });

      return {
        label: pairIndex === 0 ? '금액 (원)' : '',
        data: pairData,
        borderColor: account.color || '#007bff',
        backgroundColor: `${account.color || '#007bff'}20`,
        fill: false,
        tension: 0.4,
        spanGaps: true,
        pointRadius: (ctx) => {
          const date = allDates[ctx.dataIndex];
          if (date && (date.getTime() === buyDate.getTime() || date.getTime() === sellDate.getTime())) {
            return 6;
          }
          return 0;
        },
        pointHoverRadius: 8,
        pointBackgroundColor: (ctx) => {
          const date = allDates[ctx.dataIndex];
          if (date && date.getTime() === buyDate.getTime()) {
            return '#ffc107'; // 노란색 (매수)
          } else if (date && date.getTime() === sellDate.getTime()) {
            return account.color || '#007bff'; // 계좌 색상 (매도)
          }
          return 'transparent';
        },
        pointBorderColor: (ctx) => {
          const date = allDates[ctx.dataIndex];
          if (date && date.getTime() === buyDate.getTime()) {
            return '#ffc107'; // 노란색 (매수)
          } else if (date && date.getTime() === sellDate.getTime()) {
            return account.color || '#007bff'; // 계좌 색상 (매도)
          }
          return 'transparent';
        },
      };
    });

    // 페어링되지 않은 매수 거래를 점으로 표시
    unpairedBuyValuations.forEach((buyVal) => {
      const buyDate = new Date(buyVal.evaluation_date);
      const buyAmount = buyVal.evaluated_amount;
      
      const unpairedData = allDates.map((date) => {
        if (date.getTime() === buyDate.getTime()) {
          return buyAmount;
        }
        return null;
      });

      datasets.push({
        label: '',
        data: unpairedData,
        borderColor: '#ffc107',
        backgroundColor: '#ffc107',
        fill: false,
        showLine: false, // 선을 표시하지 않고 점만 표시
        pointRadius: (ctx) => {
          const date = allDates[ctx.dataIndex];
          if (date && date.getTime() === buyDate.getTime()) {
            return 6;
          }
          return 0;
        },
        pointHoverRadius: 8,
        pointBackgroundColor: '#ffc107',
        pointBorderColor: '#ffc107',
      });
    });

    return {
      labels: allLabels,
      datasets: datasets,
      pairs: pairs, // 차트에 pair 정보 저장 (tooltip에서 사용)
      unpairedBuyValuations: unpairedBuyValuations, // 페어링되지 않은 매수 정보 저장 (tooltip에서 사용)
      allDates: allDates // 날짜 배열 저장 (tooltip에서 사용)
    };
  };

  const chartData = calculateReturnRateData();

  // 투자 계좌의 자산과 수익률 계산
  const calculateInvestmentInfo = () => {
    if (!account || account.type !== '투자' || valuations.length === 0) {
      return { asset: account?.asset_value || 0, returnRate: account?.return_rate || 0 };
    }

    // Sort valuations by date
    const sortedValuations = [...valuations].sort((a, b) => 
      new Date(a.evaluation_date) - new Date(b.evaluation_date)
    );

    // Build pairs와 unpaired buys (차트 로직과 동일)
    const pairs = [];
    const unpairedBuys = [];
    const unpairedBuyValuations = [];

    sortedValuations.forEach((valuation) => {
      if (valuation.transaction_type === 'buy') {
        unpairedBuys.push({
          buyDate: valuation.evaluation_date,
          buyAmount: valuation.evaluated_amount,
          buyValuation: valuation
        });
        unpairedBuyValuations.push(valuation);
      } else if (valuation.transaction_type === 'sell') {
        if (unpairedBuys.length > 0) {
          const buy = unpairedBuys.shift();
          const buyVal = unpairedBuyValuations.shift();
          const sellAmount = valuation.evaluated_amount;
          const returnRate = ((sellAmount - buy.buyAmount) / buy.buyAmount) * 100;
          
          pairs.push({
            buyDate: buy.buyDate,
            buyAmount: buy.buyAmount,
            sellDate: valuation.evaluation_date,
            sellAmount: sellAmount,
            returnRate: returnRate,
            buyValuations: [buyVal],
            sellValuation: valuation
          });
        }
      } else if (valuation.transaction_type === 'valuation') {
        if (unpairedBuys.length > 0) {
          const buy = unpairedBuys[0];
          const buyVal = unpairedBuyValuations[0];
          
          let existingPairIndex = -1;
          for (let i = 0; i < pairs.length; i++) {
            if (pairs[i].buyValuations[0]?.id === buyVal.id) {
              existingPairIndex = i;
              break;
            }
          }
          
          if (existingPairIndex >= 0) {
            pairs.splice(existingPairIndex, 1);
          } else {
            unpairedBuys.shift();
            unpairedBuyValuations.shift();
          }
          
          const sellAmount = valuation.evaluated_amount;
          const returnRate = ((sellAmount - buy.buyAmount) / buy.buyAmount) * 100;
          
          pairs.push({
            buyDate: buy.buyDate,
            buyAmount: buy.buyAmount,
            sellDate: valuation.evaluation_date,
            sellAmount: sellAmount,
            returnRate: returnRate,
            buyValuations: [buyVal],
            sellValuation: valuation
          });
        }
      }
    });

    // 자산 계산: 최신 valuation 또는 account의 evaluated_amount 사용
    let asset = 0;
    const latestValuation = sortedValuations
      .filter(v => v.transaction_type === 'valuation')
      .sort((a, b) => new Date(b.evaluation_date) - new Date(a.evaluation_date))[0];
    
    if (latestValuation) {
      asset = latestValuation.evaluated_amount;
    } else if (account.evaluated_amount > 0) {
      asset = account.evaluated_amount;
    }

    // 수익률: 가장 최신 pair의 수익률
    let returnRate = 0;
    if (pairs.length > 0) {
      const latestPair = pairs.sort((a, b) => 
        new Date(b.sellDate) - new Date(a.sellDate)
      )[0];
      returnRate = latestPair.returnRate;
    }

    return { asset, returnRate };
  };

  const investmentInfo = account?.type === '투자' ? calculateInvestmentInfo() : null;

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
                <div className="value">{formatCurrency(investmentInfo?.asset || account.asset_value || 0)}</div>
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
                <div className="value">{investmentInfo?.returnRate != null ? investmentInfo.returnRate.toFixed(1) : (account.return_rate != null ? account.return_rate.toFixed(1) : '0.0')}%</div>
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
                  <table className="investment-transactions-table">
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
                              <tr 
                                key={item.id} 
                                className={item.category === '이동' ? 'transfer' : ''}
                                onClick={() => handleTransactionClick(item)}
                                style={{ cursor: 'pointer' }}
                              >
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
                              <tr 
                                key={item.id} 
                                className="valuation"
                                onClick={() => handleValuationClick(item)}
                                style={{ cursor: 'pointer' }}
                              >
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
                        datalabels: {
                          display: true,
                          color: '#333',
                          anchor: 'end',
                          align: 'top',
                          formatter: function(value) {
                            // 금액으로 표시
                            return (value / 10000).toFixed(0) + '만원';
                          },
                          font: {
                            size: 11,
                            weight: 'bold'
                          }
                        },
                        tooltip: {
                          mode: 'index',
                          intersect: false,
                          callbacks: {
                            label: function(context) {
                              const pairs = chartData.pairs || [];
                              const unpairedBuyValuations = chartData.unpairedBuyValuations || [];
                              const allDates = chartData.allDates || [];
                              const datasetIndex = context.datasetIndex;
                              const dataIndex = context.dataIndex;
                              
                              // Pair 데이터셋 처리
                              if (datasetIndex < pairs.length && dataIndex < allDates.length) {
                                const pair = pairs[datasetIndex];
                                const date = allDates[dataIndex];
                                const buyDate = new Date(pair.buyDate);
                                const sellDate = new Date(pair.sellDate);
                                
                                if (date.getTime() === buyDate.getTime()) {
                                  // 매수 시점
                                  return [
                                    `매수 금액: ${context.parsed.y.toLocaleString()}원`,
                                    `매수일: ${buyDate.toLocaleDateString('ko-KR')}`
                                  ];
                                } else if (date.getTime() === sellDate.getTime()) {
                                  // 매도 시점
                                  return [
                                    `매도 금액: ${context.parsed.y.toLocaleString()}원`,
                                    `매수: ${pair.buyAmount.toLocaleString()}원`,
                                    `매도: ${pair.sellAmount.toLocaleString()}원`,
                                    `수익률: ${pair.returnRate.toFixed(1)}%`
                                  ];
                                }
                              }
                              
                              // 페어링되지 않은 매수 데이터셋 처리
                              const unpairedStartIndex = pairs.length;
                              if (datasetIndex >= unpairedStartIndex && datasetIndex < unpairedStartIndex + unpairedBuyValuations.length && dataIndex < allDates.length) {
                                const buyVal = unpairedBuyValuations[datasetIndex - unpairedStartIndex];
                                const date = allDates[dataIndex];
                                const buyDate = new Date(buyVal.evaluation_date);
                                
                                if (date.getTime() === buyDate.getTime()) {
                                  return [
                                    `매수 금액: ${context.parsed.y.toLocaleString()}원`,
                                    `매수일: ${buyDate.toLocaleDateString('ko-KR')}`,
                                    `(미매도)`
                                  ];
                                }
                              }
                              
                              return `금액: ${context.parsed.y.toLocaleString()}원`;
                            }
                          }
                        }
                      },
                      scales: {
                        y: {
                          beginAtZero: false,
                          ticks: {
                            callback: function(value) {
                              // 금액으로 표시 (만원 단위)
                              return (value / 10000).toFixed(0) + '만원';
                            }
                          },
                          title: {
                            display: true,
                            text: '금액 (원)'
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
            <table className="cash-transactions-table">
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
                  <tr 
                    key={transaction.id} 
                    className={transaction.category === '이동' ? 'transfer' : ''}
                    onClick={() => handleTransactionClick(transaction)}
                    style={{ cursor: 'pointer' }}
                  >
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

      <EditTransactionModal
        isOpen={isEditTransactionModalOpen}
        onClose={() => {
          setIsEditTransactionModalOpen(false);
          setSelectedTransaction(null);
        }}
        transaction={selectedTransaction}
        accountId={id}
        onTransactionUpdated={handleTransactionUpdated}
        accountType={account.type}
      />

      <EditValuationModal
        isOpen={isEditValuationModalOpen}
        onClose={() => {
          setIsEditValuationModalOpen(false);
          setSelectedValuation(null);
        }}
        valuation={selectedValuation}
        accountId={id}
        onValuationUpdated={handleValuationUpdated}
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
