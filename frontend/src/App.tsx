import React, { useState, useCallback } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme, Snackbar, Alert, Button } from '@mui/material';
import CompanyInput from './components/CompanyInput';
import ProductComparison from './components/ProductComparison';
import { initiateProductScraping, getProductComparison, Product } from './services/api';

const theme = createTheme();

const POLLING_INTERVAL = 5000; // 5 seconds

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRetry, setShowRetry] = useState(false);
  const [lastCompanies, setLastCompanies] = useState<string[]>([]);

  const pollComparisonResults = useCallback(async (companies: string[], attempts = 0) => {
    try {
      const data = await getProductComparison();
      if (data.length > 0) {
        setProducts(data);
        setLoading(false);
        setShowRetry(false);
      } else if (attempts < 12) { // Poll for 1 minute max
        setTimeout(() => pollComparisonResults(companies, attempts + 1), POLLING_INTERVAL);
      } else {
        throw new Error('Timeout waiting for comparison results');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get comparison results');
      setLoading(false);
      setShowRetry(true);
    }
  }, []);

  const handleCompare = async (companies: string[]) => {
    try {
      setLoading(true);
      setError(null);
      setShowRetry(false);
      setLastCompanies(companies);
      
      // Initiate scraping
      await initiateProductScraping(companies);
      
      // Start polling for results
      pollComparisonResults(companies);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
      setShowRetry(true);
    }
  };

  const handleRetry = () => {
    if (lastCompanies.length > 0) {
      handleCompare(lastCompanies);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container>
        <CompanyInput onCompare={handleCompare} disabled={loading} />
        <ProductComparison
          products={products}
          loading={loading}
          error={error}
        />
        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={() => setError(null)}
        >
          <Alert 
            severity="error" 
            action={
              showRetry && (
                <Button color="inherit" size="small" onClick={handleRetry}>
                  Retry
                </Button>
              )
            }
          >
            {error}
          </Alert>
        </Snackbar>
      </Container>
    </ThemeProvider>
  );
}

export default App;
