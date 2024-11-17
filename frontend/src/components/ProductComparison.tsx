import React from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  Box,
  Alert,
} from '@mui/material';

interface Product {
  id: string;
  company_name: string;
  product_name: string;
  price: number;
  rating: number;
  reviews: number;
}

interface ProductComparisonProps {
  products: Product[];
  loading: boolean;
  error: string | null;
}

const ProductComparison: React.FC<ProductComparisonProps> = ({
  products,
  loading,
  error,
}) => {
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 4 }}>
        {error}
      </Alert>
    );
  }

  if (!products.length) {
    return null;
  }

  return (
    <Paper elevation={3} sx={{ mt: 4, p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Product Comparison
      </Typography>
      
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Company</TableCell>
              <TableCell>Product</TableCell>
              <TableCell align="right">Price ($)</TableCell>
              <TableCell align="right">Rating</TableCell>
              <TableCell align="right">Reviews</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {products.map((product) => (
              <TableRow key={product.id}>
                <TableCell>{product.company_name}</TableCell>
                <TableCell>{product.product_name}</TableCell>
                <TableCell align="right">
                  {product.price.toFixed(2)}
                </TableCell>
                <TableCell align="right">
                  {product.rating.toFixed(1)}
                </TableCell>
                <TableCell align="right">{product.reviews}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default ProductComparison;
