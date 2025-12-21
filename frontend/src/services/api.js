import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add authentication tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.request);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Account API functions
export const accountApi = {
  // Get all accounts
  getAllAccounts: () => {
    console.log('API call: GET /accounts');
    return api.get('/accounts');
  },
  
  // Get account by ID
  getAccount: (id) => api.get(`/accounts/${id}`),
  
  // Create new account
  createAccount: (account) => api.post('/accounts', account),
  
  // Update account
  updateAccount: (id, account) => api.put(`/accounts/${id}`, account),
  
  // Delete account
  deleteAccount: (id) => api.delete(`/accounts/${id}`),
  
  // Toggle account status
  toggleAccountStatus: (id) => api.post(`/accounts/${id}/toggle-status`),
  
  // Get account transactions
  getTransactions: (id, ascending = false) => 
    api.get(`/accounts/${id}/transactions`, { params: { ascending } }),
  
  // Add transaction to account
  addTransaction: (id, transaction) => 
    api.post(`/accounts/${id}/transactions`, transaction),

  // Update transaction
  updateTransaction: (accountId, transactionId, transaction) =>
    api.put(`/accounts/${accountId}/transactions/${transactionId}`, transaction),
  
  // Get account valuations
  getValuations: (id) => api.get(`/accounts/${id}/valuations`),
  
  // Add valuation to account
  addValuation: (id, valuation) => 
    api.post(`/accounts/${id}/valuations`, valuation),
  
  // Delete valuation from account
  deleteValuation: (id, valuationId) => 
    api.delete(`/accounts/${id}/valuations/${valuationId}`),
};

// Stats API functions
export const statsApi = {
  // Get total assets
  getTotalAssets: () => api.get('/stats/total-assets'),
  
  // Get total cash
  getTotalCash: () => api.get('/stats/total-cash'),
  
  // Get monthly income breakdown
  getMonthlyIncomeBreakdown: (year) => 
    api.get('/stats/monthly-income-breakdown', { params: { year } }),
  
  // Get salaries
  getSalaries: (year) => api.get('/stats/salaries', { params: { year } }),

  // Get median salary
  getSalaryMedian: (year, person) => api.get('/stats/salaries/median', { params: { year, person } }),

  // Get monthly salary totals
  getMonthlySalaryTotals: (year, person) => api.get('/stats/salaries/monthly-totals', { params: { year, person } }),
  
  // Add salary
  addSalary: (amount, month, person) => 
    api.post('/stats/salaries', null, { params: { amount, month, person } }),
  
  // Update salary
  updateSalary: (index, amount, month, person, classification) => 
    api.put(`/stats/salaries/${index}`, null, { params: { amount, month, person, classification } }),
  
  // Delete salary
  deleteSalary: (index) => 
    api.delete(`/stats/salaries/${index}`),
  
  // Get asset allocation
  getAssetAllocation: () => api.get('/stats/asset-allocation'),
};

// Utility function to format currency
export const formatCurrency = (amount) => {
  if (amount === undefined || amount === null) return '₩0';
  return `₩${amount.toLocaleString()}`;
};

// Utility function to get text color based on background
export const getTextColor = (color) => {
  if (!color) return '#333';
  // Convert to lowercase for comparison
  const normalizedColor = color.toLowerCase();
  // Only return white text if background is pure black
  if (normalizedColor === '#000000' || normalizedColor === '#000') {
    return '#ffffff';
  }
  // For all other colors, return black text
  return '#000000';
};
