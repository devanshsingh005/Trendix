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
  price: string | number;
  rating: string | number;
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

  const formatPrice = (price: string | number): string => {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toFixed(2);
  };

  const formatRating = (rating: string | number): string => {
    const numRating = typeof rating === 'string' ? parseFloat(rating) : rating;
    return numRating.toFixed(1);
  };

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
                  {formatPrice(product.price)}
                </TableCell>
                <TableCell align="right">
                  {formatRating(product.rating)}
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
