import React, { useState, useCallback, useEffect } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme, Snackbar, Alert, Button, Typography, CircularProgress, Box, FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import CompanyInput from './components/CompanyInput';
import ProductComparison from './components/ProductComparison';
import { initiateProductScraping, getProductComparison, getAllProducts, Product, checkSupabaseProducts } from './services/api';

const theme = createTheme();

const POLLING_INTERVAL = 2000; // 2 seconds
const MAX_POLLING_ATTEMPTS = 30; // 1 minute total polling time
const SCRAPING_WAIT_TIME = 30000; // 30 seconds wait after scraping

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showRetry, setShowRetry] = useState(false);
  const [lastCompanies, setLastCompanies] = useState<string[]>([]);
  const [isScrapingMode, setIsScrapingMode] = useState(false);

  const handleCompanyFilter = (company: string) => {
    setSelectedCompany(company);
  };

  const getFilteredProducts = () => {
    if (selectedCompany) {
      const searchCompany = selectedCompany.toLowerCase();
      return products.filter(product => 
        product.company_name.toLowerCase() === searchCompany
      );
    }
    return products;
  };

  const getUniqueCompanies = () => {
    const companies = new Set<string>();
    products.forEach(product => {
      companies.add(product.company_name);
    });
    return Array.from(companies).sort();
  };

  const checkForScrapedProducts = useCallback(async (companies: string[]) => {
    try {
      const data = await checkSupabaseProducts(companies);
      if (data && data.length > 0) {
        console.log('Found scraped products in Supabase:', data);
        setProducts(data);
        setLoading(false);
        setShowRetry(false);
        setError(null);
        setIsScrapingMode(false);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Error checking for scraped products:', err);
      return false;
    }
  }, []);

  const pollComparisonResults = useCallback(async (companies: string[], attempts = 0) => {
    try {
      console.log(`Polling attempt ${attempts + 1} for companies:`, companies);
      const data = await getProductComparison(companies);
      
      if (data && data.length > 0) {
        console.log('Successfully received products:', data);
        // Wait for 30 seconds before checking Supabase again
        setIsScrapingMode(true);
        setTimeout(async () => {
          console.log('Checking Supabase after wait period...');
          const found = await checkForScrapedProducts(companies);
          if (!found) {
            setError('Products not found after scraping. Please try again.');
            setLoading(false);
            setShowRetry(true);
          }
        }, SCRAPING_WAIT_TIME);
      } else if (attempts < MAX_POLLING_ATTEMPTS) {
        console.log(`No data yet, retrying in ${POLLING_INTERVAL}ms...`);
        setTimeout(() => pollComparisonResults(companies, attempts + 1), POLLING_INTERVAL);
      } else {
        throw new Error('No products found for the specified companies. Please try again or try different companies.');
      }
    } catch (err) {
      console.error('Error in polling:', err);
      setError(err instanceof Error ? err.message : 'Failed to get comparison results');
      setLoading(false);
      setShowRetry(true);
      setProducts([]);
      setIsScrapingMode(false);
    }
  }, [checkForScrapedProducts]);

  const handleCompare = async (companies: string[]) => {
    try {
      setLoading(true);
      setError(null);
      setShowRetry(false);
      setLastCompanies(companies);
      setSelectedCompany('');
      setProducts([]);
      setIsScrapingMode(false);
      
      // First, try to get products from Supabase
      console.log('Checking Supabase for existing products...');
      const found = await checkForScrapedProducts(companies);
      
      if (!found) {
        // No products found, initiate scraping
        console.log('No existing products found, initiating scraping...');
        setIsScrapingMode(true);
        const result = await initiateProductScraping(companies);
        
        if (result.success) {
          console.log('Successfully initiated scraping:', result);
          // Start polling for results
          pollComparisonResults(companies);
        } else {
          throw new Error('Failed to initiate product scraping');
        }
      }
    } catch (err) {
      console.error('Error in handleCompare:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
      setLoading(false);
      setShowRetry(true);
      setProducts([]);
      setIsScrapingMode(false);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container>
        <CompanyInput onCompare={handleCompare} disabled={loading} />
        
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Box sx={{ textAlign: 'center' }}>
              <CircularProgress />
              {isScrapingMode && (
                <Typography sx={{ mt: 2 }}>
                  {products.length > 0 
                    ? "Products found. Please wait 30 seconds while we process the results..."
                    : "Scraping product data... This may take a moment."}
                </Typography>
              )}
            </Box>
          </Box>
        )}
        
        {error && (
          <Alert severity="error" sx={{ mt: 4 }}>
            {error}
          </Alert>
        )}
        
        {products.length > 0 && (
          <>
            <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>
              Company Products
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <FormControl sx={{ minWidth: 200 }}>
                <InputLabel id="company-filter-label">Filter by Company</InputLabel>
                <Select
                  labelId="company-filter-label"
                  value={selectedCompany}
                  onChange={(e) => handleCompanyFilter(e.target.value)}
                  label="Filter by Company"
                >
                  <MenuItem value="">
                    <em>All Searched Companies</em>
                  </MenuItem>
                  {getUniqueCompanies().map((company) => (
                    <MenuItem key={company} value={company}>
                      {company}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>

            <ProductComparison
              products={getFilteredProducts()}
              loading={false}
              error={null}
            />
          </>
        )}
        
        <Snackbar 
          open={!!error} 
          autoHideDuration={6000} 
          onClose={() => setError(null)}
        >
          <Alert 
            severity="error" 
            action={
              showRetry && (
                <Button color="inherit" size="small" onClick={() => handleCompare(lastCompanies)}>
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
