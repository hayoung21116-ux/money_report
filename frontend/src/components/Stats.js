import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { statsApi, formatCurrency } from '../services/api';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';
import ChartDataLabels from 'chartjs-plugin-datalabels';

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

const StatsContainer = styled.div`
  .stats-header {
    display: flex;
    align-items: center;
    margin-bottom: 30px;
    gap: 20px;
    
    h2 {
      color: #333;
      font-size: 1.8rem;
      margin: 0;
    }
  }
  
  .year-selector {
    select {
      padding: 8px 12px;
      border-radius: 4px;
      border: 1px solid #ddd;
      font-size: 1rem;
    }
  }
  
  .tabs {
    display: flex;
    border-bottom: 1px solid #ddd;
    margin-bottom: 30px;
    
    .tab {
      padding: 12px 20px;
      cursor: pointer;
      border-bottom: 3px solid transparent;
      
      &.active {
        border-bottom: 3px solid #007bff;
        color: #007bff;
        font-weight: 600;
      }
      
      &:hover {
        background-color: #f8f9fa;
      }
    }
  }
  
  .tab-content {
      .summary {
        background-color: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 30px;
        position: relative; /* Add this line */
      
      .summary-text {
        font-size: 1.1rem;
        line-height: 1.6;
      }
    }
    
    .chart-container {
      background-color: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      margin-bottom: 30px;
      min-height: 400px;
      display: flex;
      align-items: center;
      justify-content: center;
      
      .chart-placeholder {
        text-align: center;
        color: #666;
        
        p {
          margin: 10px 0;
        }
      }
    }
  }
  
  @media (max-width: 768px) {
    .stats-header {
      flex-direction: column;
      align-items: flex-start;
      
      h2 {
        font-size: 1.5rem;
      }
    }
    
    .tabs {
      overflow-x: auto;
      
      .tab {
        white-space: nowrap;
      }
    }
  }
`;

const StatCard = styled.div`
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
  margin-bottom: 20px;
  
  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #007bff;
    margin: 10px 0;
  }
  
  .stat-label {
    font-size: 1.1rem;
    color: #666;
  }
`;

function Stats() {
  const [activeTab, setActiveTab] = useState('portfolio');
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());
  const [assetAllocation, setAssetAllocation] = useState({});
  const [totalAssets, setTotalAssets] = useState(0);
  const [totalCash, setTotalCash] = useState(0);
  const [salaries, setSalaries] = useState([]);
  const [minGuiMedianSalary, setMinGuiMedianSalary] = useState(0); // Add state for MinGui median
  const [haYoungMedianSalary, setHaYoungMedianSalary] = useState(0); // Add state for HaYoung median
  const [monthlySalaryTotals, setMonthlySalaryTotals] = useState({}); // Add state for monthly totals
  const [hoveredBar, setHoveredBar] = useState(null);
  const [editingSalary, setEditingSalary] = useState(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [snapshots, setSnapshots] = useState([]);
  const [growthData, setGrowthData] = useState(null);
  const [baselineSnapshotId, setBaselineSnapshotId] = useState('');
  const [newSnapshotLabel, setNewSnapshotLabel] = useState('');
  const [growthError, setGrowthError] = useState(null);
  const [stockPortfolio, setStockPortfolio] = useState({ 민규: [], 하영: [] });
  const [stockError, setStockError] = useState(null);
  const [showStockAdd, setShowStockAdd] = useState({ 민규: false, 하영: false });
  const [stockForm, setStockForm] = useState({
    민규: { category: '지수', market: '국장', name: '', amount: '' },
    하영: { category: '지수', market: '국장', name: '', amount: '' },
  });

  const GROWTH_CATEGORY_ORDER = ['현금', '부동산', '코인', '주식', '연금', '기타'];
  const STOCK_CATEGORY_COLORS = {
    '지수': '#1976D2',      // blue
    '섹터 ETF': '#2E7D32',  // green
    '종목': '#F57C00',      // orange
  };

  const rgbaFromHex = (hex, alpha) => {
    const h = (hex || '').replace('#', '');
    if (h.length !== 6) return hex;
    const r = parseInt(h.slice(0, 2), 16);
    const g = parseInt(h.slice(2, 4), 16);
    const b = parseInt(h.slice(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const formatReturnPct = (p) => {
    if (p === null || p === undefined) return '—';
    const sign = p >= 0 ? '+' : '';
    return `${sign}${p.toFixed(2)}%`;
  };

  const formatSnapshotWhen = (iso) => {
    if (!iso) return '';
    try {
      return new Date(iso).toLocaleString('ko-KR', { dateStyle: 'medium', timeStyle: 'short' });
    } catch {
      return iso;
    }
  };

  // Debugging: Log hoveredBar state changes
  useEffect(() => {
    console.log('hoveredBar state changed:', hoveredBar);
  }, [hoveredBar]);

  useEffect(() => {
    fetchStats();
  }, []);

  const [monthlyIncome, setMonthlyIncome] = useState({});

  const fetchStats = async () => {
    try {
      const [allocationResponse, assetsResponse, cashResponse, incomeResponse, salaryResponse, minGuiMedianResponse, haYoungMedianResponse, monthlyTotalsResponse] = await Promise.all([
        statsApi.getAssetAllocation(),
        statsApi.getTotalAssets(),
        statsApi.getTotalCash(),
        statsApi.getMonthlyIncomeBreakdown(selectedYear),
        statsApi.getSalaries(selectedYear),
        statsApi.getSalaryMedian(selectedYear, '민규'), // Fetch MinGui median
        statsApi.getSalaryMedian(selectedYear, '하영'), // Fetch HaYoung median
        statsApi.getMonthlySalaryTotals(selectedYear) // Fetch monthly totals
      ]);

      setAssetAllocation(allocationResponse.data);
      setTotalAssets(assetsResponse.data.total_assets);
      setTotalCash(cashResponse.data.total_cash);
      setMonthlyIncome(incomeResponse.data);
      setSalaries(salaryResponse.data);
      setMinGuiMedianSalary(minGuiMedianResponse.data.median_salary || 0); // Set MinGui median
      setHaYoungMedianSalary(haYoungMedianResponse.data.median_salary || 0); // Set HaYoung median
      setMonthlySalaryTotals(monthlyTotalsResponse.data.monthly_totals || {}); // Set monthly totals

      // In a full implementation, we would also set the other data
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [selectedYear]);

  useEffect(() => {
    if (activeTab !== 'growth') return undefined;
    let cancelled = false;
    (async () => {
      try {
        setGrowthError(null);
        const snapRes = await statsApi.getAssetSnapshots();
        if (cancelled) return;
        setSnapshots(snapRes.data || []);
        try {
          const growthRes = await statsApi.getAssetGrowth(baselineSnapshotId || undefined);
          if (!cancelled) {
            setGrowthData(growthRes.data);
          }
        } catch (ge) {
          if (!cancelled) {
            setGrowthData(null);
            setGrowthError(ge.response?.data?.detail || '증감 데이터를 불러오지 못했습니다.');
          }
        }
      } catch (e) {
        if (!cancelled) {
          setSnapshots([]);
          setGrowthData(null);
          setGrowthError(e.response?.data?.detail || '데이터를 불러오지 못했습니다.');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeTab, baselineSnapshotId]);

  useEffect(() => {
    if (activeTab !== 'stock') return undefined;
    let cancelled = false;
    (async () => {
      try {
        setStockError(null);
        const res = await statsApi.getStockPortfolio();
        if (!cancelled) {
          setStockPortfolio(res.data || { 민규: [], 하영: [] });
        }
      } catch (e) {
        if (!cancelled) {
          setStockPortfolio({ 민규: [], 하영: [] });
          setStockError(e.response?.data?.detail || '주식 포폴 데이터를 불러오지 못했습니다.');
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [activeTab]);

  const handleAddStockEntry = async (person) => {
    try {
      const f = stockForm[person];
      const amountNum = typeof f.amount === 'string' ? parseFloat(f.amount) : f.amount;
      await statsApi.addStockEntry(person, f.category, f.market, f.name, amountNum);
      setStockForm((prev) => ({ ...prev, [person]: { ...prev[person], name: '', amount: '' } }));
      const res = await statsApi.getStockPortfolio();
      setStockPortfolio(res.data || { 민규: [], 하영: [] });
      setStockError(null);
    } catch (e) {
      alert(e.response?.data?.detail || '추가에 실패했습니다.');
    }
  };

  const handleDeleteStockEntry = async (person, entryId) => {
    if (!window.confirm('이 항목을 삭제할까요?')) return;
    try {
      await statsApi.deleteStockEntry(person, entryId);
      const res = await statsApi.getStockPortfolio();
      setStockPortfolio(res.data || { 민규: [], 하영: [] });
      setStockError(null);
    } catch (e) {
      alert(e.response?.data?.detail || '삭제에 실패했습니다.');
    }
  };

  const handleCreateAssetSnapshot = async () => {
    try {
      await statsApi.createAssetSnapshot(newSnapshotLabel.trim());
      setNewSnapshotLabel('');
      const snapRes = await statsApi.getAssetSnapshots();
      setSnapshots(snapRes.data || []);
      const growthRes = await statsApi.getAssetGrowth(baselineSnapshotId || undefined);
      setGrowthData(growthRes.data);
      setGrowthError(null);
      alert('저장 지점이 추가되었습니다.');
    } catch (e) {
      alert(e.response?.data?.detail || '저장에 실패했습니다.');
    }
  };

  const handleDeleteSnapshot = async (id) => {
    if (!window.confirm('이 저장 지점을 삭제할까요?')) return;
    try {
      await statsApi.deleteAssetSnapshot(id);
      const nextBaseline = baselineSnapshotId === id ? '' : baselineSnapshotId;
      setBaselineSnapshotId(nextBaseline);
      const snapRes = await statsApi.getAssetSnapshots();
      setSnapshots(snapRes.data || []);
      try {
        const growthRes = await statsApi.getAssetGrowth(nextBaseline || undefined);
        setGrowthData(growthRes.data);
        setGrowthError(null);
      } catch (ge) {
        setGrowthData(null);
        setGrowthError(ge.response?.data?.detail || '증감을 다시 불러오지 못했습니다.');
      }
    } catch (e) {
      alert(e.response?.data?.detail || '삭제에 실패했습니다.');
    }
  };

  const renderPortfolioTab = () => {
    const legendMargin = {
      id: 'legendMargin',
      beforeInit(chart) {
        if (chart.legend) {
          const originalFit = chart.legend.fit;
          chart.legend.fit = function fit() {
            if (originalFit) {
              originalFit.bind(chart.legend)();
            }
            this.width += 100; // Increase width reserve
          };
        }
      },
      afterUpdate(chart) {
        // Shift the legend text to the right to create visual gap
        if (chart.legend) {
          chart.legend.left += 80;
        }
      }
    };

    const getColorForCategory = (category) => {
      const colors = {
        "현금": "#4CAF50",
        "부동산": "#2196F3",
        "코인": "#FF9800",
        "연금": "#FF5722", // Distinct color for pension
        "주식": "#9C27B0",
        "기타": "#607D8B"
      };
      return colors[category] || "#9E9E9E";
    };

    const calculatePercentage = (value, total) => {
      return total > 0 ? ((value / total) * 100).toFixed(1) : 0;
    };

    const total = Object.values(assetAllocation).reduce((sum, value) => sum + value, 0);

    const chartData = {
      labels: Object.keys(assetAllocation),
      datasets: [
        {
          data: Object.values(assetAllocation),
          backgroundColor: Object.keys(assetAllocation).map(category => getColorForCategory(category)),
          borderColor: Object.keys(assetAllocation).map(category => getColorForCategory(category)),
          borderWidth: 1,
        },
      ],
    };

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            font: {
              size: 14,
            },
            generateLabels: (chart) => {
              const data = chart.data;
              const total = Object.values(assetAllocation).reduce((sum, value) => sum + value, 0);
              if (data.labels.length && data.datasets.length) {
                return data.labels.map((label, i) => {
                  const style = data.datasets[0].backgroundColor[i];
                  const value = data.datasets[0].data[i];
                  const percentage = calculatePercentage(value, total);
                  return {
                    text: label,
                    fillStyle: style,
                    strokeStyle: style,
                    lineWidth: 1,
                    hidden: isNaN(value) || chart.getDatasetMeta(0).data[i].hidden,
                    index: i,
                  };
                });
              }
              return [];
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              const label = context.label || '';
              const value = context.parsed;
              const percentage = calculatePercentage(value, total);
              return `${label}: ${formatCurrency(value)} (${percentage}%)`;
            }
          }
        },
        datalabels: {
          color: '#fff',
          formatter: (value, context) => {
            const percentage = calculatePercentage(value, total);
            return percentage > 0 ? `${percentage}%` : '';
          },
          font: {
            weight: 'bold',
            size: 14,
          },
          display: function (context) {
            // Only display datalabels if the segment is large enough to show the label clearly
            // You might need to adjust this threshold based on your chart size and data distribution
            return context.dataset.data[context.dataIndex] / total * 100 > 5;
          }
        }
      },
    };

    return (
      <div className="tab-content">
        <div className="summary">
          <div className="summary-text">
            {Object.keys(assetAllocation).length > 0 ? (
              <>
                {Object.entries(assetAllocation).map(([category, value]) => (
                  <div key={category}>
                    {category}: {formatCurrency(value)} ({calculatePercentage(value, total)}%)
                  </div>
                ))}
              </>
            ) : (
              "자산 데이터가 없습니다."
            )}
          </div>
        </div>

        <div className="chart-container">
          {Object.keys(assetAllocation).length > 0 ? (
            <div style={{ width: '100%', maxWidth: '500px', height: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Doughnut data={chartData} options={chartOptions} plugins={[legendMargin]} />
            </div>
          ) : (
            <div className="chart-placeholder">
              <p>자산 데이터가 없습니다.</p>
              <p>계좌를 추가하고 거래를 등록해보세요.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderGrowthTab = () => {
    const baseline = growthData?.baseline_snapshot;
    const byCat = growthData?.by_category || {};
    const totalRow = growthData?.total;

    return (
      <div className="tab-content">
        <div className="summary">
          <div className="summary-text">
            <p style={{ fontSize: '1.7rem', fontWeight: 'bold', marginBottom: '12px' }}>자라나라 자산자산</p>
            <p style={{ fontSize: '0.95rem', color: '#555', marginBottom: '16px' }}>
            「지금 자산 저장」으로 현재 포트폴리오를 저장 지점으로 남기면, 이후 같은 방식으로 쌓인 시점과 비교해
              카테고리별·총 수익률을 볼 수 있습니다.
              <br />
              비교 기준은 기본적으로 <strong>가장 최근 저장 지점</strong>이며, 아래에서 과거 저장 지점을 고를 수 있습니다.
            </p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'flex-end', marginBottom: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label htmlFor="baseline-snapshot">비교 기준 시점</label>
                <select
                  id="baseline-snapshot"
                  value={baselineSnapshotId}
                  onChange={(e) => setBaselineSnapshotId(e.target.value)}
                  style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd', minWidth: '260px' }}
                >
                  <option value="">가장 최근 저장 지점 (기본)</option>
                  {snapshots.map((s) => (
                    <option key={s.id} value={s.id}>
                      {formatSnapshotWhen(s.created_at)}
                      {s.label ? ` — ${s.label}` : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: '1 1 200px' }}>
                <label htmlFor="snapshot-label">메모 (선택)</label>
                <input
                  id="snapshot-label"
                  type="text"
                  value={newSnapshotLabel}
                  onChange={(e) => setNewSnapshotLabel(e.target.value)}
                  placeholder="예: 연말 결산"
                  style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd' }}
                />
              </div>
              <button
                type="button"
                onClick={handleCreateAssetSnapshot}
                style={{
                  padding: '10px 16px',
                  background: '#007bff',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: 600,
                }}
              >
                지금 자산 저장
              </button>
            </div>

            {growthError && (
              <p style={{ color: '#c62828', marginBottom: '12px' }}>{growthError}</p>
            )}

            {baseline && (
              <p style={{ marginBottom: '8px', color: '#333' }}>
                <strong>기준 시점</strong>: {formatSnapshotWhen(baseline.created_at)}
                {baseline.label ? ` (${baseline.label})` : ''}
                {' · '}
                <strong>기준 총액</strong> {formatCurrency(baseline.total)}
              </p>
            )}
          </div>
        </div>

        <div className="chart-container" style={{ minHeight: 'auto', display: 'block', padding: '16px' }}>
          {growthData && totalRow && (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #ddd', textAlign: 'left' }}>
                    <th style={{ padding: '10px 8px' }}>구분</th>
                    <th style={{ padding: '10px 8px' }}>기준 금액</th>
                    <th style={{ padding: '10px 8px' }}>현재 금액</th>
                    <th style={{ padding: '10px 8px' }}>증감</th>
                    <th style={{ padding: '10px 8px' }}>수익률</th>
                  </tr>
                </thead>
                <tbody>
                  {GROWTH_CATEGORY_ORDER.map((key) => {
                    const row = byCat[key];
                    if (!row) return null;
                    return (
                      <tr key={key} style={{ borderBottom: '1px solid #eee' }}>
                        <td style={{ padding: '10px 8px', fontWeight: 600 }}>{key}</td>
                        <td style={{ padding: '10px 8px' }}>{formatCurrency(row.baseline)}</td>
                        <td style={{ padding: '10px 8px' }}>{formatCurrency(row.current)}</td>
                        <td style={{ padding: '10px 8px', color: row.delta >= 0 ? '#2e7d32' : '#c62828' }}>
                          {row.delta >= 0 ? '+' : ''}
                          {formatCurrency(row.delta)}
                        </td>
                        <td style={{ padding: '10px 8px' }}>{formatReturnPct(row.return_pct)}</td>
                      </tr>
                    );
                  })}
                  <tr style={{ borderTop: '2px solid #333', fontWeight: 700 }}>
                    <td style={{ padding: '12px 8px' }}>총합</td>
                    <td style={{ padding: '12px 8px' }}>{formatCurrency(totalRow.baseline)}</td>
                    <td style={{ padding: '12px 8px' }}>{formatCurrency(totalRow.current)}</td>
                    <td
                      style={{
                        padding: '12px 8px',
                        color: totalRow.delta >= 0 ? '#2e7d32' : '#c62828',
                      }}
                    >
                      {totalRow.delta >= 0 ? '+' : ''}
                      {formatCurrency(totalRow.delta)}
                    </td>
                    <td style={{ padding: '12px 8px' }}>{formatReturnPct(totalRow.return_pct)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {snapshots.length > 0 && (
            <div style={{ marginTop: '24px' }}>
              <p style={{ fontWeight: 600, marginBottom: '8px' }}>저장 지점 목록</p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {snapshots.map((s) => (
                  <li
                    key={s.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 0',
                      borderBottom: '1px solid #eee',
                      gap: '12px',
                    }}
                  >
                    <span>
                      {formatSnapshotWhen(s.created_at)}
                      {s.label ? ` — ${s.label}` : ''}
                      {' · '}
                      {formatCurrency(s.total)}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleDeleteSnapshot(s.id)}
                      style={{
                        padding: '6px 10px',
                        fontSize: '0.85rem',
                        border: '1px solid #ccc',
                        borderRadius: '4px',
                        background: '#fff',
                        cursor: 'pointer',
                      }}
                    >
                      삭제
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderStockPortfolioTab = () => {
    const people = ['민규', '하영'];

    const buildChart = (entries) => {
      const amountOf = (e) => {
        if (e == null) return 0;
        const a = Number(e.amount);
        if (!Number.isNaN(a) && a > 0) return a;
        // Back-compat: if old data used weight field, treat it as amount to keep chart visible
        const w = Number(e.weight);
        if (!Number.isNaN(w) && w > 0) return w;
        return 0;
      };
      const cleaned = (entries || []).filter((e) => e && e.name && amountOf(e) > 0);
      const total = cleaned.reduce((sum, e) => sum + amountOf(e), 0) || 0;
      const labels = cleaned.map((e) => `${e.name}`);
      const data = cleaned.map((e) => amountOf(e));
      const backgroundColor = cleaned.map((e) => {
        const base = STOCK_CATEGORY_COLORS[e.category] || '#9E9E9E';
        const alpha = e.market === '미장' ? 0.45 : 0.95; // market by transparency
        return rgbaFromHex(base, alpha);
      });
      const borderColor = cleaned.map((e) => {
        const base = STOCK_CATEGORY_COLORS[e.category] || '#9E9E9E';
        return rgbaFromHex(base, 1);
      });
      return {
        total,
        chartData: {
          labels,
          datasets: [
            {
              data,
              backgroundColor,
              borderColor,
              borderWidth: 1,
            },
          ],
        },
      };
    };

    const chartOptions = (personEntries) => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: {
            boxWidth: 12,
            font: { size: 12 },
            generateLabels: (chart) => {
              const ds = chart.data.datasets[0] || {};
              return (chart.data.labels || []).map((label, i) => {
                const e = (personEntries || [])[i];
                const cat = e?.category || '';
                const mk = e?.market || '';
                return {
                  text: `${label}${cat || mk ? ` (${cat}${cat && mk ? ', ' : ''}${mk})` : ''}`,
                  fillStyle: ds.backgroundColor?.[i],
                  strokeStyle: ds.borderColor?.[i],
                  lineWidth: 1,
                  hidden: chart.getDatasetMeta(0).data[i]?.hidden,
                  index: i,
                };
              });
            },
          },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const w = Number(ctx.parsed || 0);
              const total = (ctx.dataset.data || []).reduce((s, v) => s + Number(v || 0), 0) || 1;
              const pct = (w / total) * 100;
              const e = (personEntries || [])[ctx.dataIndex];
              const cat = e?.category || '';
              const mk = e?.market || '';
              return `${ctx.label}: ${w} (${pct.toFixed(1)}%)${cat || mk ? ` · ${cat}/${mk}` : ''}`;
            },
          },
        },
        datalabels: {
          color: '#111',
          formatter: (value, ctx) => {
            const total = (ctx.chart.data.datasets[0].data || []).reduce((s, v) => s + Number(v || 0), 0) || 0;
            if (!total) return '';
            const pct = (Number(value) / total) * 100;
            return pct >= 6 ? `${pct.toFixed(0)}%` : ''; // hide tiny labels
          },
        },
      },
    });

    const renderPerson = (person) => {
      const entries = stockPortfolio?.[person] || [];
      const { total, chartData } = buildChart(entries);
      return (
        <div style={{ flex: 1, minWidth: '320px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '10px' }}>
            <p style={{ fontSize: '1.3rem', fontWeight: 700, margin: 0 }}>{person}</p>
            <span style={{ color: '#666', fontSize: '0.95rem' }}>총액: {formatCurrency(total)}</span>
          </div>

          <div style={{ height: '320px', background: '#fff', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.08)', padding: '12px', marginBottom: '14px' }}>
            {entries.length ? (
              <Doughnut data={chartData} options={chartOptions(entries)} />
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
                아직 입력된 종목이 없습니다.
              </div>
            )}
          </div>

          <div style={{ background: '#fff', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.08)', padding: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <p style={{ fontWeight: 700, marginTop: 0, marginBottom: 0 }}>보유 종목</p>
              <button
                type="button"
                onClick={() => setShowStockAdd((prev) => ({ ...prev, [person]: !prev[person] }))}
                style={{
                  padding: '8px 12px',
                  border: '1px solid #ccc',
                  borderRadius: '6px',
                  background: '#fff',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
              >
                {showStockAdd[person] ? '닫기' : '추가하기'}
              </button>
            </div>

            {showStockAdd[person] && (
              <div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.9rem', color: '#444' }}>카테고리</label>
                <select
                  value={stockForm[person].category}
                  onChange={(e) =>
                    setStockForm((prev) => ({
                      ...prev,
                      [person]: { ...prev[person], category: e.target.value },
                    }))
                  }
                  style={{ padding: '8px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="지수">지수</option>
                  <option value="섹터 ETF">섹터 ETF</option>
                  <option value="종목">종목</option>
                </select>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.9rem', color: '#444' }}>시장</label>
                <select
                  value={stockForm[person].market}
                  onChange={(e) =>
                    setStockForm((prev) => ({
                      ...prev,
                      [person]: { ...prev[person], market: e.target.value },
                    }))
                  }
                  style={{ padding: '8px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                >
                  <option value="국장">국장</option>
                  <option value="미장">미장</option>
                </select>
              </div>
                </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '10px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.9rem', color: '#444' }}>종목명</label>
                <input
                  value={stockForm[person].name}
                  onChange={(e) =>
                    setStockForm((prev) => ({
                      ...prev,
                      [person]: { ...prev[person], name: e.target.value },
                    }))
                  }
                  placeholder="예: VOO / QQQ / 삼성전자"
                  style={{ padding: '8px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <label style={{ fontSize: '0.9rem', color: '#444' }}>금액</label>
                <input
                  type="number"
                  min="0"
                  step="1000"
                  value={stockForm[person].amount}
                  onChange={(e) =>
                    setStockForm((prev) => ({
                      ...prev,
                      [person]: { ...prev[person], amount: e.target.value },
                    }))
                  }
                  placeholder="예: 1000000"
                  style={{ padding: '8px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={() => handleAddStockEntry(person)}
              style={{
                width: '100%',
                padding: '10px 12px',
                border: 'none',
                borderRadius: '6px',
                background: '#111',
                color: '#fff',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              추가
            </button>
              </div>
            )}

            {entries.length > 0 && (
              <div style={{ marginTop: '14px' }}>
                <p style={{ fontWeight: 700, marginBottom: '8px' }}>현재 목록</p>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {entries.map((e) => (
                    <li
                      key={e.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 0',
                        borderBottom: '1px solid #eee',
                        gap: '10px',
                      }}
                    >
                      <span style={{ fontSize: '0.95rem' }}>
                        <strong>{e.name}</strong> — {formatCurrency(Number(e.amount || e.weight || 0))} ({e.category}/{e.market})
                      </span>
                      <button
                        type="button"
                        onClick={() => handleDeleteStockEntry(person, e.id)}
                        style={{
                          padding: '6px 10px',
                          fontSize: '0.85rem',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          background: '#fff',
                          cursor: 'pointer',
                        }}
                      >
                        삭제
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      );
    };

    return (
      <div className="tab-content">
        <div className="summary">
          <div className="summary-text">
            <p style={{ fontSize: '1.7rem', fontWeight: 'bold', marginBottom: '12px' }}>주식 포폴</p>
            <p style={{ fontSize: '0.95rem', color: '#555', marginBottom: '0' }}>
              각자 종목 비중을 입력하면 원그래프로 비율을 보여줍니다. 색상은 카테고리(지수/섹터 ETF/종목)별로 다르고,
              투명도는 시장(국장/미장)으로 구분됩니다.
            </p>
            {stockError && <p style={{ color: '#c62828', marginTop: '10px' }}>{stockError}</p>}
          </div>
        </div>

        <div className="chart-container" style={{ minHeight: 'auto', display: 'block', padding: '16px' }}>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            {people.map((p) => renderPerson(p))}
          </div>
        </div>
      </div>
    );
  };

  const renderSavingsTab = () => {
    // Calculate summary statistics
    let totalSavings = 0;
    let totalInterest = 0;

    Object.values(monthlyIncome).forEach(monthData => {
      totalSavings += (monthData.savings || 0);
      totalInterest += (monthData.interest || 0);
    });

    const total = totalSavings + totalInterest;

    // Sort months chronologically for chart
    const sortedMonths = Object.keys(monthlyIncome).sort();

    // Max value for chart scaling (savings + interest per month)
    const maxTotal = Math.max(
      ...Object.values(monthlyIncome).map((d) => (d.savings || 0) + (d.interest || 0)),
      1
    );

    // Y-axis: round up to nearest 100,000, 5 grid lines
    const roundedMax = Math.ceil(maxTotal / 100000) * 100000;
    const gridInterval = roundedMax / 5;
    const yAxisValues = [
      roundedMax,
      roundedMax - gridInterval,
      roundedMax - 2 * gridInterval,
      roundedMax - 3 * gridInterval,
      roundedMax - 4 * gridInterval,
      0
    ];

    const maxBarHeight = 250;
    const SAVINGS_COLOR = '#4CAF50';   // green
    const INTEREST_COLOR = '#FFC107'; // yellow

    return (
      <div className="tab-content">
        <div className="summary">
          <div className="summary-text">
            <p style={{ fontSize: '1.7rem', fontWeight: 'bold', marginBottom: '10px' }}>{selectedYear}년 저축+이자 요약</p>
            {activeTab === 'savings' && (
              <div style={{ position: 'absolute', top: '20px', right: '20px' }}>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '1rem' }}
                >
                  {years.map(year => (
                    <option key={year} value={year}>{year}년</option>
                  ))}
                </select>
              </div>
            )}
            <p>저축: {formatCurrency(totalSavings)}</p>
            <p>이자: {formatCurrency(totalInterest)}</p>
            <p>합계: {formatCurrency(total)}</p>
          </div>
        </div>

        <div className="chart-container">
          {sortedMonths.length > 0 ? (
            <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
              <div style={{ textAlign: 'center', marginBottom: '10px', fontSize: '18px', fontWeight: 'bold' }}>
                저축+이자
              </div>

              <div style={{ display: 'flex', height: '300px', marginBottom: '10px' }}>
                <div style={{ width: '55px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', alignItems: 'flex-end', paddingRight: '10px', fontSize: '10px', color: '#666', lineHeight: '1', position: 'relative', zIndex: '1', boxSizing: 'border-box', height: 'calc(100% - 20px)' }}>
                  <span>{(yAxisValues[0] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[1] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[2] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[3] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[4] / 10000).toLocaleString()}만원</span>
                  <span>0-</span>
                </div>

                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                  <div
                    style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: '2%', paddingBottom: '20px', borderBottom: '1px solid #ddd', position: 'relative', paddingLeft: '0.5%', paddingRight: '0.5%' }}
                  >
                    <div style={{ position: 'absolute', top: '0px', left: 0, right: 0, bottom: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingTop: '0px', paddingBottom: '0px' }}>
                      {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} style={{ height: '1px', backgroundColor: '#eee', width: '100%', zIndex: '0' }}></div>
                      ))}
                    </div>
                    {sortedMonths.map((month) => {
                      const data = monthlyIncome[month];
                      const savings = data.savings || 0;
                      const interest = data.interest || 0;
                      const monthTotal = savings + interest;
                      const totalHeight = maxTotal > 0 ? (monthTotal / maxTotal) * maxBarHeight : 0;
                      const savingsHeight = maxTotal > 0 ? (savings / maxTotal) * maxBarHeight : 0;
                      const interestHeight = maxTotal > 0 ? (interest / maxTotal) * maxBarHeight : 0;
                      const isHovered = hoveredBar === `savings-${month}`;

                      return (
                        <div key={month} style={{ display: 'flex', alignItems: 'flex-end', minWidth: '30px', flexGrow: 1, justifyContent: 'center' }}>
                          <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div
                              style={{
                                position: 'absolute',
                                top: '-36px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                whiteSpace: 'nowrap',
                                display: isHovered ? 'block' : 'none',
                                zIndex: '1000',
                                pointerEvents: 'none'
                              }}
                            >
                              저축 {formatCurrency(savings)} / 이자 {formatCurrency(interest)}
                            </div>
                            <div
                              style={{
                                width: '24px',
                                height: `${totalHeight}px`,
                                display: 'flex',
                                flexDirection: 'column-reverse',
                                alignItems: 'center',
                                transition: 'height 0.3s ease',
                                cursor: 'pointer'
                              }}
                              onMouseEnter={() => setHoveredBar(`savings-${month}`)}
                              onMouseLeave={() => setHoveredBar(null)}
                            >
                              <div
                                style={{
                                  width: '100%',
                                  height: `${savingsHeight}px`,
                                  backgroundColor: SAVINGS_COLOR,
                                  minHeight: savingsHeight > 0 ? '2px' : 0,
                                  transition: 'height 0.3s ease'
                                }}
                              />
                              <div
                                style={{
                                  width: '100%',
                                  height: `${interestHeight}px`,
                                  backgroundColor: INTEREST_COLOR,
                                  minHeight: interestHeight > 0 ? '2px' : 0,
                                  transition: 'height 0.3s ease'
                                }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <div style={{ display: 'flex', gap: '2%', justifyContent: 'center', paddingTop: '5px', paddingLeft: '0.5%', paddingRight: '0.5%' }}>
                    {sortedMonths.map(month => (
                      <div key={month} style={{ flexGrow: 1, minWidth: '30px', textAlign: 'center', fontSize: '12px', color: '#666' }}>
                        {month.split('-')[1]}월
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', marginTop: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{ width: '16px', height: '16px', backgroundColor: SAVINGS_COLOR, borderRadius: '2px' }}></div>
                  <span style={{ fontSize: '14px' }}>저축</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <div style={{ width: '16px', height: '16px', backgroundColor: INTEREST_COLOR, borderRadius: '2px' }}></div>
                  <span style={{ fontSize: '14px' }}>이자</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="chart-placeholder">
              <p>저축/이자 데이터가 없습니다.</p>
              <p>계좌를 추가하고 거래를 등록해보세요.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderSalaryTab = () => {
    // Group salaries by month, person, and classification (salary vs bonus)
    const monthlySalaries = {};
    salaries.forEach(salary => {
      const month = salary.month;
      const person = salary.person;
      const amount = salary.amount;
      const classification = salary.classification || '월급'; // Default to '월급' if not specified

      if (!monthlySalaries[month]) {
        monthlySalaries[month] = {
          민규: { salary: 0, bonus: 0, total: 0 },
          하영: { salary: 0, bonus: 0, total: 0 },
          total: 0
        };
      }

      if (classification === '보너스') {
        monthlySalaries[month][person].bonus += amount;
      } else {
        monthlySalaries[month][person].salary += amount;
      }
      monthlySalaries[month][person].total += amount;
      monthlySalaries[month].total += amount;
    });

    // Sort months chronologically
    const sortedMonths = Object.keys(monthlySalaries).sort();

    // Calculate summary statistics
    const totalSalary = Object.values(monthlySalaries).reduce((sum, monthData) => sum + monthData.total, 0);
    const minGuiTotal = Object.values(monthlySalaries).reduce((sum, monthData) => sum + monthData.민규.total, 0);
    const haYoungTotal = Object.values(monthlySalaries).reduce((sum, monthData) => sum + monthData.하영.total, 0);

    // Calculate payment counts for each person
    const minGuiPaymentCount = salaries.filter(salary => salary.person === '민규').length;
    const haYoungPaymentCount = salaries.filter(salary => salary.person === '하영').length;

    // Calculate averages
    const averageSalary = salaries.length > 0 ? Math.round(totalSalary / salaries.length) : 0;
    const minGuiAverage = minGuiPaymentCount > 0 ? Math.round(minGuiTotal / minGuiPaymentCount) : 0;
    const haYoungAverage = haYoungPaymentCount > 0 ? Math.round(haYoungTotal / haYoungPaymentCount) : 0;

    // Find the maximum salary value for chart scaling
    const maxSalary = Math.max(...Object.values(monthlySalaries).map(data => Math.max(data.민규.total, data.하영.total)), 1);

    // Calculate y-axis grid values based on the new formula
    // Round up maxSalary to nearest 100,000 and divide by 5
    const roundedMaxSalary = Math.ceil(maxSalary / 100000) * 100000;
    const gridInterval = roundedMaxSalary / 5;
    const yAxisValues = [
      roundedMaxSalary,
      roundedMaxSalary - gridInterval,
      roundedMaxSalary - 2 * gridInterval,
      roundedMaxSalary - 3 * gridInterval,
      roundedMaxSalary - 4 * gridInterval,
      0
    ];

    return (
      <div className="tab-content">
        <div className="summary">
          <div className="summary-text">
            <p style={{ fontSize: '1.7rem', fontWeight: 'bold', marginBottom: '10px' }}>{selectedYear}년 월급 요약</p>
            {activeTab === 'salary' && (
              <div style={{ position: 'absolute', top: '20px', right: '20px' }}>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(e.target.value)}
                  style={{ padding: '8px 12px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '1rem' }}
                >
                  {years.map(year => (
                    <option key={year} value={year}>{year}년</option>
                  ))}
                </select>
              </div>
            )}
            <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '-5px', marginBottom: '5px' }}>** 월급의 기준은 전달 21일/25일에 들어온 금액이다. 예를 들어, 1월의 월급은 12월 21일/25일에 지급되었다.</p>
            <p style={{ fontSize: '0.8rem', color: '#666', marginTop: '-5px', marginBottom: '15px' }}>** PS는 2월, PI는 7월, 8월, 12월에 합쳐 기록한다.</p>
            <p style={{ fontSize: '1.1rem', fontWeight: 'bold', marginBottom: '8px' }}>
              총 월급: {formatCurrency(totalSalary)}
              {minGuiTotal > haYoungTotal ? (
                <> 👑(민규) {formatCurrency(minGuiTotal)} / (하영) {formatCurrency(haYoungTotal)}</>
              ) : haYoungTotal > minGuiTotal ? (
                <> (민규) {formatCurrency(minGuiTotal)} / 👑(하영) {formatCurrency(haYoungTotal)}</>
              ) : (
                <> (민규) {formatCurrency(minGuiTotal)} / (하영) {formatCurrency(haYoungTotal)}</>
              )}
            </p>
            <p style={{ fontSize: '0.95rem' }}>평균: {formatCurrency(averageSalary)} (민규) {formatCurrency(minGuiAverage)} / (하영) {formatCurrency(haYoungAverage)}</p>
            <p style={{ fontSize: '0.95rem' }}>중앙값: {formatCurrency(minGuiMedianSalary)} (민규) / {formatCurrency(haYoungMedianSalary)} (하영)</p>
          </div>
        </div>

        <div className="chart-container">
          {salaries.length > 0 ? (
            <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
              {/* Chart title */}
              <div style={{ textAlign: 'center', marginBottom: '10px', fontSize: '18px', fontWeight: 'bold' }}>
                월급
              </div>

              {/* Chart area */}
              <div style={{ display: 'flex', height: '300px', marginBottom: '10px' }}>
                {/* Y-axis labels */}
                <div style={{ width: '55px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', alignItems: 'flex-end', paddingRight: '10px', fontSize: '10px', color: '#666', lineHeight: '1', position: 'relative', zIndex: '1', boxSizing: 'border-box', height: 'calc(100% - 20px)' }}>
                  <span>{(yAxisValues[0] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[1] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[2] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[3] / 10000).toLocaleString()}만원</span>
                  <span>{(yAxisValues[4] / 10000).toLocaleString()}만원</span>
                  <span>0-</span>
                </div>

                {/* Chart area with grid lines */}
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
                  {/* Bars */}
                  <div
                    style={{ flex: 1, display: 'flex', alignItems: 'flex-end', gap: '2%', paddingBottom: '20px', borderBottom: '1px solid #ddd', position: 'relative', paddingLeft: '0.5%', paddingRight: '0.5%' }}
                    onMouseMove={(e) => {
                      console.log('Mouse moved in chart area - coordinates:', e.clientX, e.clientY);
                    }}
                  >
                    {/* Y-axis grid lines */}
                    <div style={{ position: 'absolute', top: '0px', left: 0, right: 0, bottom: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingTop: '0px', paddingBottom: '0px' }}>
                      {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} style={{ height: '1px', backgroundColor: '#eee', width: '100%', zIndex: '0' }}></div>
                      ))}
                    </div>
                    {sortedMonths.map((month, index) => {
                      const data = monthlySalaries[month];
                      // Use fixed height calculation instead of percentage
                      const maxBarHeight = 250; // Maximum bar height in pixels
                      const minGuiTotalHeight = maxSalary > 0 ? (data.민규.total / maxSalary) * maxBarHeight : 0;
                      const haYoungTotalHeight = maxSalary > 0 ? (data.하영.total / maxSalary) * maxBarHeight : 0;

                      // Calculate individual heights for salary and bonus
                      const minGuiSalaryHeight = maxSalary > 0 ? (data.민규.salary / maxSalary) * maxBarHeight : 0;
                      const minGuiBonusHeight = maxSalary > 0 ? (data.민규.bonus / maxSalary) * maxBarHeight : 0;
                      const haYoungSalaryHeight = maxSalary > 0 ? (data.하영.salary / maxSalary) * maxBarHeight : 0;
                      const haYoungBonusHeight = maxSalary > 0 ? (data.하영.bonus / maxSalary) * maxBarHeight : 0;

                      return (
                        <div key={month} style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', minWidth: '30px', flexGrow: 1, justifyContent: 'center' }}>
                          <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div
                              style={{
                                position: 'absolute',
                                top: '-30px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                whiteSpace: 'nowrap',
                                display: hoveredBar === `${month}-minGui` ? 'block' : 'none',
                                zIndex: '1000',
                                pointerEvents: 'none'
                              }}
                            >
                              {formatCurrency(data.민규.total)} ({formatCurrency(data.민규.bonus)}/{formatCurrency(data.민규.salary)})
                            </div>
                            {/* MinGui stacked bar: salary (opaque) + bonus (transparent) */}
                            <div
                              style={{
                                width: '15px',
                                height: `${minGuiTotalHeight}px`,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                transition: 'height 0.3s ease',
                                cursor: 'pointer'
                              }}
                              onMouseEnter={() => {
                                console.log('Mouse entered minGui bar for month:', month);
                                setHoveredBar(`${month}-minGui`);
                              }}
                              onMouseLeave={() => {
                                console.log('Mouse left minGui bar for month:', month);
                                setHoveredBar(null);
                              }}
                              onMouseMove={(e) => {
                                console.log('Mouse moved over minGui bar for month:', month, '- coordinates:', e.clientX, e.clientY);
                              }}
                              onClick={async (e) => {
                                // Determine which segment was clicked based on position
                                const rect = e.currentTarget.getBoundingClientRect();
                                const clickY = e.clientY - rect.top;
                                const isBonusClicked = clickY < minGuiBonusHeight;

                                // Find the appropriate salary data based on which segment was clicked
                                // We need to find the correct index in the original salaries array
                                let salaryIndex = -1;
                                for (let i = 0; i < salaries.length; i++) {
                                  const s = salaries[i];
                                  if (s.month === month && s.person === '민규') {
                                    if (isBonusClicked && s.classification === '보너스') {
                                      salaryIndex = i;
                                      break;
                                    } else if (!isBonusClicked && (s.classification === undefined || s.classification === '월급')) {
                                      salaryIndex = i;
                                      break;
                                    }
                                  }
                                }

                                if (salaryIndex !== -1) {
                                  // Get the actual salary data from the filtered array
                                  const selectedSalary = salaries[salaryIndex];

                                  // Now we need to find the index of this salary in the full array
                                  // Fetch all salaries to get the full array
                                  try {
                                    const allSalariesResponse = await statsApi.getSalaries();
                                    const allSalaries = allSalariesResponse.data;

                                    // Find the index in the full array that matches our selected salary
                                    let fullArrayIndex = -1;
                                    for (let i = 0; i < allSalaries.length; i++) {
                                      const s = allSalaries[i];
                                      if (s.month === selectedSalary.month &&
                                        s.person === selectedSalary.person &&
                                        s.amount === selectedSalary.amount &&
                                        s.classification === selectedSalary.classification) {
                                        fullArrayIndex = i;
                                        break;
                                      }
                                    }

                                    if (fullArrayIndex !== -1) {
                                      console.log('Clicked on salary data at index:', fullArrayIndex, 'in full array for month:', month, 'person: 민규', 'classification:', isBonusClicked ? '보너스' : '월급');
                                      setEditingSalary({ ...selectedSalary, index: fullArrayIndex });
                                      setShowEditModal(true);
                                    } else {
                                      // If we still can't find the data, show an error
                                      console.error('Could not find salary data in full array for', month, '민규', isBonusClicked ? '보너스' : '월급');
                                    }
                                  } catch (error) {
                                    console.error('Error fetching all salaries:', error);
                                  }
                                } else {
                                  // If we still can't find the data, show an error
                                  console.error('Could not find salary data for', month, '민규', isBonusClicked ? '보너스' : '월급');
                                }
                              }}
                              onContextMenu={async (e) => {
                                // For mobile long-press, we'll use context menu as a workaround
                                e.preventDefault();
                                // Try to find a bonus entry first, then fall back to regular salary
                                let salaryIndex = -1;
                                // Try to find a bonus entry first
                                for (let i = 0; i < salaries.length; i++) {
                                  const s = salaries[i];
                                  if (s.month === month && s.person === '민규' && s.classification === '보너스') {
                                    salaryIndex = i;
                                    break;
                                  }
                                }
                                if (salaryIndex === -1) {
                                  // Fall back to regular salary
                                  for (let i = 0; i < salaries.length; i++) {
                                    const s = salaries[i];
                                    if (s.month === month && s.person === '민규' && (s.classification === undefined || s.classification === '월급')) {
                                      salaryIndex = i;
                                      break;
                                    }
                                  }
                                }
                                if (salaryIndex !== -1) {
                                  // Get the actual salary data from the filtered array
                                  const selectedSalary = salaries[salaryIndex];

                                  // Now we need to find the index of this salary in the full array
                                  // Fetch all salaries to get the full array
                                  try {
                                    const allSalariesResponse = await statsApi.getSalaries();
                                    const allSalaries = allSalariesResponse.data;

                                    // Find the index in the full array that matches our selected salary
                                    let fullArrayIndex = -1;
                                    for (let i = 0; i < allSalaries.length; i++) {
                                      const s = allSalaries[i];
                                      if (s.month === selectedSalary.month &&
                                        s.person === selectedSalary.person &&
                                        s.amount === selectedSalary.amount &&
                                        s.classification === selectedSalary.classification) {
                                        fullArrayIndex = i;
                                        break;
                                      }
                                    }

                                    if (fullArrayIndex !== -1) {
                                      console.log('Clicked on salary data at index:', fullArrayIndex, 'in full array for month:', month, 'person: 민규');
                                      setEditingSalary({ ...selectedSalary, index: fullArrayIndex });
                                      setShowEditModal(true);
                                    } else {
                                      // If we still can't find the data, show an error
                                      console.error('Could not find salary data in full array for', month, '민규');
                                    }
                                  } catch (error) {
                                    console.error('Error fetching all salaries:', error);
                                  }
                                } else {
                                  console.error('Could not find salary data for', month, '민규');
                                }
                              }}
                            >
                              {/* Bonus segment (transparent) */}
                              <div
                                style={{
                                  width: '100%',
                                  height: `${minGuiBonusHeight}px`,
                                  backgroundColor: 'rgba(33, 150, 243, 0.4)', // More transparent blue for bonus
                                  transition: 'height 0.3s ease'
                                }}
                              ></div>
                              {/* Salary segment (opaque) */}
                              <div
                                style={{
                                  width: '100%',
                                  height: `${minGuiSalaryHeight}px`,
                                  backgroundColor: '#2196F3', // Opaque blue for salary
                                  transition: 'height 0.3s ease'
                                }}
                              ></div>
                            </div>
                          </div>
                          <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <div
                              style={{
                                position: 'absolute',
                                top: '-30px',
                                left: '50%',
                                transform: 'translateX(-50%)',
                                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                color: 'white',
                                padding: '4px 8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                whiteSpace: 'nowrap',
                                display: hoveredBar === `${month}-haYoung` ? 'block' : 'none',
                                zIndex: '1000',
                                pointerEvents: 'none'
                              }}
                            >
                              {formatCurrency(data.하영.total)} ({formatCurrency(data.하영.bonus)}/{formatCurrency(data.하영.salary)})
                            </div>
                            {/* HaYoung stacked bar: salary (opaque) + bonus (transparent) */}
                            <div
                              style={{
                                width: '15px',
                                height: `${haYoungTotalHeight}px`,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                transition: 'height 0.3s ease',
                                cursor: 'pointer'
                              }}
                              onMouseEnter={() => {
                                console.log('Mouse entered haYoung bar for month:', month);
                                setHoveredBar(`${month}-haYoung`);
                              }}
                              onMouseLeave={() => {
                                console.log('Mouse left haYoung bar for month:', month);
                                setHoveredBar(null);
                              }}
                              onMouseMove={(e) => {
                                console.log('Mouse moved over haYoung bar for month:', month, '- coordinates:', e.clientX, e.clientY);
                              }}
                              onClick={async (e) => {
                                // Determine which segment was clicked based on position
                                const rect = e.currentTarget.getBoundingClientRect();
                                const clickY = e.clientY - rect.top;
                                const isBonusClicked = clickY < haYoungBonusHeight;

                                // Find the appropriate salary data based on which segment was clicked
                                // We need to find the correct index in the original salaries array
                                let salaryIndex = -1;
                                for (let i = 0; i < salaries.length; i++) {
                                  const s = salaries[i];
                                  if (s.month === month && s.person === '하영') {
                                    if (isBonusClicked && s.classification === '보너스') {
                                      salaryIndex = i;
                                      break;
                                    } else if (!isBonusClicked && (s.classification === undefined || s.classification === '월급')) {
                                      salaryIndex = i;
                                      break;
                                    }
                                  }
                                }

                                if (salaryIndex !== -1) {
                                  // Get the actual salary data from the filtered array
                                  const selectedSalary = salaries[salaryIndex];

                                  // Now we need to find the index of this salary in the full array
                                  // Fetch all salaries to get the full array
                                  try {
                                    const allSalariesResponse = await statsApi.getSalaries();
                                    const allSalaries = allSalariesResponse.data;

                                    // Find the index in the full array that matches our selected salary
                                    let fullArrayIndex = -1;
                                    for (let i = 0; i < allSalaries.length; i++) {
                                      const s = allSalaries[i];
                                      if (s.month === selectedSalary.month &&
                                        s.person === selectedSalary.person &&
                                        s.amount === selectedSalary.amount &&
                                        s.classification === selectedSalary.classification) {
                                        fullArrayIndex = i;
                                        break;
                                      }
                                    }

                                    if (fullArrayIndex !== -1) {
                                      console.log('Clicked on salary data at index:', fullArrayIndex, 'in full array for month:', month, 'person: 하영', 'classification:', isBonusClicked ? '보너스' : '월급');
                                      setEditingSalary({ ...selectedSalary, index: fullArrayIndex });
                                      setShowEditModal(true);
                                    } else {
                                      // If we still can't find the data, show an error
                                      console.error('Could not find salary data in full array for', month, '하영', isBonusClicked ? '보너스' : '월급');
                                    }
                                  } catch (error) {
                                    console.error('Error fetching all salaries:', error);
                                  }
                                } else {
                                  console.error('Could not find salary data for', month, '하영');
                                }
                              }}
                              onContextMenu={async (e) => {
                                // For mobile long-press, we'll use context menu as a workaround
                                e.preventDefault();
                                // Try to find a bonus entry first, then fall back to regular salary
                                let salaryIndex = -1;
                                // Try to find a bonus entry first
                                for (let i = 0; i < salaries.length; i++) {
                                  const s = salaries[i];
                                  if (s.month === month && s.person === '하영' && s.classification === '보너스') {
                                    salaryIndex = i;
                                    break;
                                  }
                                }
                                if (salaryIndex === -1) {
                                  // Fall back to regular salary
                                  for (let i = 0; i < salaries.length; i++) {
                                    const s = salaries[i];
                                    if (s.month === month && s.person === '하영' && (s.classification === undefined || s.classification === '월급')) {
                                      salaryIndex = i;
                                      break;
                                    }
                                  }
                                }
                                if (salaryIndex !== -1) {
                                  // Get the actual salary data from the filtered array
                                  const selectedSalary = salaries[salaryIndex];

                                  // Now we need to find the index of this salary in the full array
                                  // Fetch all salaries to get the full array
                                  try {
                                    const allSalariesResponse = await statsApi.getSalaries();
                                    const allSalaries = allSalariesResponse.data;

                                    // Find the index in the full array that matches our selected salary
                                    let fullArrayIndex = -1;
                                    for (let i = 0; i < allSalaries.length; i++) {
                                      const s = allSalaries[i];
                                      if (s.month === selectedSalary.month &&
                                        s.person === selectedSalary.person &&
                                        s.amount === selectedSalary.amount &&
                                        s.classification === selectedSalary.classification) {
                                        fullArrayIndex = i;
                                        break;
                                      }
                                    }

                                    if (fullArrayIndex !== -1) {
                                      console.log('Clicked on salary data at index:', fullArrayIndex, 'in full array for month:', month, 'person: 하영');
                                      setEditingSalary({ ...selectedSalary, index: fullArrayIndex });
                                      setShowEditModal(true);
                                    } else {
                                      // If we still can't find the data, show an error
                                      console.error('Could not find salary data in full array for', month, '하영');
                                    }
                                  } catch (error) {
                                    console.error('Error fetching all salaries:', error);
                                  }
                                } else {
                                  console.error('Could not find salary data for', month, '하영');
                                }
                              }}
                            >
                              {/* Bonus segment (transparent) */}
                              <div
                                style={{
                                  width: '100%',
                                  height: `${haYoungBonusHeight}px`,
                                  backgroundColor: 'rgba(244, 67, 54, 0.4)', // More transparent red for bonus
                                  transition: 'height 0.3s ease'
                                }}
                              ></div>
                              {/* Salary segment (opaque) */}
                              <div
                                style={{
                                  width: '100%',
                                  height: `${haYoungSalaryHeight}px`,
                                  backgroundColor: '#f44336', // Opaque red for salary
                                  transition: 'height 0.3s ease'
                                }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* X-axis labels */}
                  <div style={{ display: 'flex', gap: '2%', justifyContent: 'center', paddingTop: '5px', paddingLeft: '0.5%', paddingRight: '0.5%' }}>
                    {sortedMonths.map(month => (
                      <div key={month} style={{ flexGrow: 1, minWidth: '30px', textAlign: 'center', fontSize: '12px', color: '#666' }}>
                        {month.split('-')[1]}월
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Legend */}
              <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ width: '15px', height: '15px', backgroundColor: '#2196F3' }}></div>
                  <span style={{ fontSize: '14px' }}>민규</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                  <div style={{ width: '15px', height: '15px', backgroundColor: '#f44336' }}></div>
                  <span style={{ fontSize: '14px' }}>하영</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="chart-placeholder">
              <p>월급 데이터가 없습니다.</p>
              <p>월급 데이터를 추가해보세요.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'portfolio':
        return renderPortfolioTab();
      case 'growth':
        return renderGrowthTab();
      case 'stock':
        return renderStockPortfolioTab();
      case 'savings':
        return renderSavingsTab();
      case 'salary':
        return renderSalaryTab();
      default:
        return renderPortfolioTab();
    }
  };

  // Function to handle salary update
  const handleUpdateSalary = async (updatedSalary) => {
    try {
      await statsApi.updateSalary(updatedSalary.index, updatedSalary.amount, updatedSalary.month, updatedSalary.person, updatedSalary.classification);
      // Refresh the data
      fetchStats();
      // Close the modal
      setShowEditModal(false);
      setEditingSalary(null);
    } catch (error) {
      console.error('Error updating salary:', error);
      alert('Failed to update salary. Please try again.');
    }
  };

  // Function to handle salary deletion
  const handleDeleteSalary = async () => {
    if (!editingSalary) return;

    try {
      await statsApi.deleteSalary(editingSalary.index);
      // Refresh the data
      fetchStats();
      // Close the modal
      setShowEditModal(false);
      setEditingSalary(null);
    } catch (error) {
      console.error('Error deleting salary:', error);
      alert('Failed to delete salary. Please try again.');
    }
  };

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 10 }, (_, i) => (currentYear - 5 + i).toString());

  return (
    <StatsContainer>
      <div className="stats-header">
        <h2>월별 통계</h2>
      </div>

      <div className="tabs">
        <div
          className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setActiveTab('portfolio')}
        >
          포트폴리오
        </div>
        <div
          className={`tab ${activeTab === 'growth' ? 'active' : ''}`}
          onClick={() => setActiveTab('growth')}
        >
          🌱자라나라 자산자산
        </div>
        <div
          className={`tab ${activeTab === 'savings' ? 'active' : ''}`}
          onClick={() => setActiveTab('savings')}
        >
          저축+이자
        </div>
        <div
          className={`tab ${activeTab === 'salary' ? 'active' : ''}`}
          onClick={() => setActiveTab('salary')}
        >
          월급
        </div>
        <div
          className={`tab ${activeTab === 'stock' ? 'active' : ''}`}
          onClick={() => setActiveTab('stock')}
        >
          📉주식 포폴
        </div>
      </div>

      {renderTabContent()}

      {/* Edit Salary Modal */}
      {showEditModal && editingSalary && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            width: '90%',
            maxWidth: '400px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{ marginTop: 0 }}>월급 수정</h3>
            <div style={{ marginBottom: '15px' }}>
              <label>날짜: </label>
              <input
                type="text"
                value={editingSalary.month}
                onChange={(e) => setEditingSalary({ ...editingSalary, month: e.target.value })}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label>이름: </label>
              <select
                value={editingSalary.person}
                onChange={(e) => setEditingSalary({ ...editingSalary, person: e.target.value })}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              >
                <option value="민규">민규</option>
                <option value="하영">하영</option>
              </select>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label>금액: </label>
              <input
                type="number"
                value={editingSalary.amount}
                onChange={(e) => setEditingSalary({ ...editingSalary, amount: parseFloat(e.target.value) || 0 })}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '15px' }}>
              <label>분류: </label>
              <select
                value={editingSalary.classification || '월급'}
                onChange={(e) => setEditingSalary({ ...editingSalary, classification: e.target.value })}
                style={{ width: '100%', padding: '8px', marginTop: '5px' }}
              >
                <option value="월급">월급</option>
                <option value="보너스">보너스</option>
              </select>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button
                onClick={handleDeleteSalary}
                style={{ backgroundColor: '#f44336', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '4px', cursor: 'pointer' }}
              >
                삭제
              </button>
              <div>
                <button
                  onClick={() => setShowEditModal(false)}
                  style={{ backgroundColor: '#ccc', color: 'black', border: 'none', padding: '10px 15px', borderRadius: '4px', cursor: 'pointer', marginRight: '10px' }}
                >
                  취소
                </button>
                <button
                  onClick={() => handleUpdateSalary(editingSalary)}
                  style={{ backgroundColor: '#007bff', color: 'white', border: 'none', padding: '10px 15px', borderRadius: '4px', cursor: 'pointer' }}
                >
                  저장
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </StatsContainer>
  );
}

export default Stats;
