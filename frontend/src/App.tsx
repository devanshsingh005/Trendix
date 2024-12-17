import React, { useState, useCallback, useEffect } from 'react';
import {
  Container,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Snackbar,
  Alert,
  Button,
  Typography,
  CircularProgress,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import CompanyInput from './components/CompanyInput';
import ProductComparison from './components/ProductComparison';
import {
  initiateProductScraping,
  getProductComparison,
  getAllProducts,
  Product,
  checkSupabaseProducts,
} from './services/api';

const theme = createTheme();

const POLLING_INTERVAL = 2000; // 2 seconds
const MAX_POLLING_ATTEMPTS = 7; // 1 minute total polling time
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
      return products.filter(
        (product) => product.company_name.toLowerCase() === searchCompany
      );
    }
    return products;
  };

  const getUniqueCompanies = () => {
    const companies = new Set<string>();
    products.forEach((product) => {
      // Add lowercase company names to avoid duplicates
      companies.add(product.company_name.toLowerCase());
    });
    // Return proper casing sorted companies
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

  const pollComparisonResults = useCallback(
    async (companies: string[], attempts = 0) => {
      try {
        console.log(`Polling attempt ${attempts + 1} for companies:`, companies);
        const data = await getProductComparison(companies);

        if (data && data.length > 0) {
          console.log('Successfully received products:', data);
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
          setTimeout(
            () => pollComparisonResults(companies, attempts + 1),
            POLLING_INTERVAL
          );
        } else {
          throw new Error(
            'No products found for the specified companies. Please try again or try different companies.'
          );
        }
      } catch (err) {
        console.error('Error in polling:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to get comparison results'
        );
        setLoading(false);
        setShowRetry(true);
        setProducts([]);
        setIsScrapingMode(false);
      }
    },
    [checkForScrapedProducts]
  );

  const handleCompare = async (companies: string[]) => {
    try {
      setLoading(true);
      setError(null);
      setShowRetry(false);
      setLastCompanies(companies);
      setSelectedCompany('');
      setProducts([]);
      setIsScrapingMode(false);

      console.log('Checking Supabase for existing products...');

      // Step 1: Check for products in Supabase
      const availableData = await checkSupabaseProducts(companies);
      const availableCompanies = availableData.map(product =>
        product.company_name.toLowerCase()
      );
      const unavailableCompanies = companies.filter(
        company => !availableCompanies.includes(company.toLowerCase())
      );

      console.log('Available companies:', availableCompanies);
      console.log('Unavailable companies:', unavailableCompanies);

      // Step 2: Display products for available companies immediately
      if (availableData.length > 0) {
        setProducts(availableData);
      }

      // Step 3: Initiate scraping only for unavailable companies
      if (unavailableCompanies.length > 0) {
        console.log('Initiating scraping for unavailable companies:', unavailableCompanies);
        setIsScrapingMode(true);

        const result = await initiateProductScraping(unavailableCompanies);

        if (result.success) {
          console.log('Scraping initiated successfully. Starting polling...');
          await new Promise(resolve => setTimeout(resolve, 60000));
          pollComparisonResults(unavailableCompanies);
        } else {
          throw new Error('Failed to initiate product scraping');
        }
      } else {
        console.log('All requested companies have data available in Supabase.');
        setLoading(false);
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
                    ? 'Products found. Please wait 30 seconds while we process the results...'
                    : 'Scraping product data... This may take a moment.'}
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
                <Button
                  color="inherit"
                  size="small"
                  onClick={() => handleCompare(lastCompanies)}
                >
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
