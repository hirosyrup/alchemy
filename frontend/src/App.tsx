import React, { useEffect, useState } from 'react';
import { Container, Typography, Box, CssBaseline, AppBar, Toolbar } from '@mui/material';
import { BalanceChart } from './components/BalanceChart';
import { BetHistory } from './components/BetHistory';
import { getBalanceHistory, getRecentBets } from './api';

function App() {
    const [balanceData, setBalanceData] = useState([]);
    const [bets, setBets] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const history = await getBalanceHistory();
                setBalanceData(history);
                const recentBets = await getRecentBets();
                setBets(recentBets);
            } catch (error) {
                console.error("Failed to fetch data:", error);
            }
        };
        fetchData();
    }, []);

    return (
        <React.Fragment>
            <CssBaseline />
            <AppBar position="static">
                <Toolbar>
                    <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                        Boat Race Trading Dashboard
                    </Typography>
                </Toolbar>
            </AppBar>
            <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                <Box sx={{ mb: 4 }}>
                    <BalanceChart data={balanceData} />
                </Box>
                <Box>
                    <BetHistory bets={bets} />
                </Box>
            </Container>
        </React.Fragment>
    );
}

export default App;
