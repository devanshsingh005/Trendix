import React, { useMemo } from 'react';
import {
  Paper,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Box,
  Alert,
  Rating,
  Chip,
  Stack,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

interface Product {
  id: string;
  company_name: string;
  product_name: string;
  price: string | number;
  rating: string | number;
  reviews: number;
  category?: string;
}

interface ProductComparisonProps {
  products: Product[];
  loading: boolean;
  error: string | null;
}

interface GroupedProducts {
  [company: string]: {
    [category: string]: Product[];
  };
}

const ProductComparison: React.FC<ProductComparisonProps> = ({
  products,
  loading,
  error,
}) => {
  const groupedProducts = useMemo(() => {
    if (!products || !products.length) return {};
    return products.reduce((acc: GroupedProducts, product) => {
      const company = product.company_name;
      const category = product.category || 'Other';

      if (!acc[company]) {
        acc[company] = {};
      }
      if (!acc[company][category]) {
        acc[company][category] = [];
      }
      acc[company][category].push(product);
      return acc;
    }, {});
  }, [products]);

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

  if (!products || !products.length) {
    return (
      <Paper elevation={3} sx={{ mt: 4, p: 3 }}>
        <Typography variant="body1" color="text.secondary" align="center">
          No products available.
        </Typography>
      </Paper>
    );
  }

  const formatPrice = (price: string | number): string => {
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    return numPrice.toFixed(2);
  };

  const formatRating = (rating: string | number): string => {
    const numRating = typeof rating === 'string' ? parseFloat(rating) : rating;
    return numRating.toFixed(1);
  };

  const getBestPrice = (productList: Product[]) => {
    return Math.min(...productList.map(p => typeof p.price === 'string' ? parseFloat(p.price) : p.price));
  };

  const getBestRating = (productList: Product[]) => {
    return Math.max(...productList.map(p => typeof p.rating === 'string' ? parseFloat(p.rating) : p.rating));
  };

  return (
    <Paper elevation={3} sx={{ mt: 4, p: 3 }}>
      <Typography variant="h5" gutterBottom align="center" sx={{ mb: 4 }}>
        Product Comparison by Brand and Category
      </Typography>

      {Object.entries(groupedProducts).map(([company, categories]) => (
        <Box key={company} sx={{ mb: 8 }}>
          <Typography 
            variant="h5" 
            sx={{ 
              mb: 3, 
              pb: 1, 
              borderBottom: '3px solid',
              borderColor: 'primary.main',
              color: 'primary.main',
              fontWeight: 'bold'
            }}
          >
            {company}
          </Typography>

          {Object.entries(categories).map(([category, categoryProducts]) => {
            const bestPrice = getBestPrice(categoryProducts);
            const bestRating = getBestRating(categoryProducts);

            return (
              <Box key={`${company}-${category}`} sx={{ mb: 4, ml: 2 }}>
                <Typography 
                  variant="h6" 
                  sx={{ 
                    mb: 2,
                    color: 'text.secondary',
                    display: 'flex',
                    alignItems: 'center',
                    '&::before': {
                      content: '""',
                      width: '24px',
                      height: '2px',
                      backgroundColor: 'primary.main',
                      marginRight: '8px'
                    }
                  }}
                >
                  {category}
                </Typography>

                <TableContainer 
                  component={Paper} 
                  elevation={2}
                  sx={{ 
                    mb: 3,
                    borderRadius: '8px',
                    overflow: 'hidden'
                  }}
                >
                  <Table>
                    <TableHead>
                      <TableRow sx={{ 
                        backgroundColor: 'primary.light',
                        '& .MuiTableCell-head': {
                          color: 'primary.main',
                          fontWeight: 'bold'
                        }
                      }}>
                        <TableCell>Product Name</TableCell>
                        <TableCell align="right">Price</TableCell>
                        <TableCell align="center">Rating</TableCell>
                        <TableCell align="right">Reviews</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {categoryProducts.map((product) => {
                        const price = typeof product.price === 'string' ? parseFloat(product.price) : product.price;
                        const rating = typeof product.rating === 'string' ? parseFloat(product.rating) : product.rating;
                        const isBestPrice = price === bestPrice;
                        const isBestRating = rating === bestRating;

                        return (
                          <TableRow 
                            key={product.id}
                            sx={{ 
                              '&:nth-of-type(odd)': { backgroundColor: 'action.hover' },
                              transition: 'background-color 0.2s',
                              '&:hover': { 
                                backgroundColor: 'action.selected',
                                '& .MuiTableCell-root': {
                                  color: 'primary.main'
                                }
                              }
                            }}
                          >
                            <TableCell>
                              <Typography variant="body1">
                                {product.product_name}
                              </Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Stack direction="row" spacing={1} justifyContent="flex-end" alignItems="center">
                                <Typography 
                                  variant="body1" 
                                  color={isBestPrice ? 'success.main' : 'text.primary'}
                                  sx={{ fontWeight: isBestPrice ? 'bold' : 'regular' }}
                                >
                                  ${formatPrice(product.price)}
                                </Typography>
                                {isBestPrice && (
                                  <Chip 
                                    size="small" 
                                    color="success" 
                                    label="Best Price"
                                    icon={<TrendingDownIcon />}
                                  />
                                )}
                              </Stack>
                            </TableCell>
                            <TableCell align="center">
                              <Stack direction="row" spacing={1} justifyContent="center" alignItems="center">
                                <Rating 
                                  value={parseFloat(formatRating(rating))} 
                                  precision={0.1} 
                                  size="small"
                                  readOnly 
                                />
                                <Typography variant="body2">
                                  ({formatRating(rating)})
                                </Typography>
                                {isBestRating && (
                                  <Chip 
                                    size="small" 
                                    color="primary" 
                                    label="Top Rated"
                                    icon={<TrendingUpIcon />}
                                  />
                                )}
                              </Stack>
                            </TableCell>
                            <TableCell align="right">
                              {product.reviews.toLocaleString()}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            );
          })}
        </Box>
      ))}
    </Paper>
  );
};

export default ProductComparison;
