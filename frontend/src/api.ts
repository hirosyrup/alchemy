import axios from 'axios';

const API_URL = 'http://localhost:8000/api/dashboard';

export const getBalanceHistory = async () => {
    const response = await axios.get(`${API_URL}/balance`);
    return response.data.history;
};

export const getRecentBets = async () => {
    const response = await axios.get(`${API_URL}/bets`);
    return response.data.bets;
};
