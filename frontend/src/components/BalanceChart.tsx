import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Paper, Typography, Box } from '@mui/material';

interface BalanceData {
    date: string;
    balance: number;
}

interface Props {
    data: BalanceData[];
}

export const BalanceChart: React.FC<Props> = ({ data }) => {
    return (
        <Paper sx={{ p: 2, height: 400 }}>
            <Typography variant="h6" gutterBottom>
                収支推移
            </Typography>
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="balance" stroke="#8884d8" />
                </LineChart>
            </ResponsiveContainer>
        </Paper>
    );
};
