import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Typography, Chip } from '@mui/material';

interface Bet {
    date: string;
    place_id: number;
    race_number: number;
    combination: string;
    odds: number;
    amount: number;
    return_amount: number;
    status: string;
}

interface Props {
    bets: Bet[];
}

export const BetHistory: React.FC<Props> = ({ bets }) => {
    return (
        <Paper sx={{ p: 2, mt: 2 }}>
            <Typography variant="h6" gutterBottom>
                最近の投票履歴
            </Typography>
            <TableContainer>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>日付</TableCell>
                            <TableCell>場/R</TableCell>
                            <TableCell>買い目</TableCell>
                            <TableCell>オッズ</TableCell>
                            <TableCell>金額</TableCell>
                            <TableCell>払戻</TableCell>
                            <TableCell>結果</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {bets.map((bet, index) => (
                            <TableRow key={index}>
                                <TableCell>{bet.date}</TableCell>
                                <TableCell>{bet.place_id} / {bet.race_number}R</TableCell>
                                <TableCell>{bet.combination}</TableCell>
                                <TableCell>{bet.odds}</TableCell>
                                <TableCell>{bet.amount}</TableCell>
                                <TableCell>{bet.return_amount}</TableCell>
                                <TableCell>
                                    <Chip 
                                        label={bet.status} 
                                        color={bet.status === 'won' ? 'success' : bet.status === 'lost' ? 'error' : 'default'} 
                                        size="small" 
                                    />
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    );
};
