import axios from 'axios';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Initialize Supabase client
const supabaseUrl = 'https://lbyeddvmqoowhfvseplu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxieWVkZHZtcW9vd2hmdnNlcGx1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzE1NjMyNjEsImV4cCI6MjA0NzEzOTI2MX0.HHWY43rfN_EZMUhE1EcilOuWdwG-4dsei0FhvfR2REE';
const supabase = createClient(supabaseUrl, supabaseKey);

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Product {
  id: string;
  company_name: string;
  product_name: string;
  price: number;
  rating: number;
  reviews: number;
  category?: string;
}

interface ApiResponse<T> {
  status: string;
  data: T;
}

interface ScrapeResponse {
  message: string;
  companies: string[];
  error?: string;
}

const inferProductCategory = (productName: string): string => {
  const lowerName = productName.toLowerCase();
  
  if (lowerName.includes('laptop') || lowerName.includes('notebook')) {
    return 'Laptop';
  } else if (lowerName.includes('phone') || lowerName.includes('mobile') || lowerName.includes('smartphone')) {
    return 'Mobile';
  } else if (lowerName.includes('tablet') || lowerName.includes('ipad')) {
    return 'Tablet';
  } else if (lowerName.includes('watch') || lowerName.includes('smartwatch')) {
    return 'Smartwatch';
  } else if (lowerName.includes('tv') || lowerName.includes('television')) {
    return 'TV';
  } else if (lowerName.includes('headphone') || lowerName.includes('earphone') || lowerName.includes('earbud')) {
    return 'Audio';
  } else {
    return 'Other';
  }
};

const processProductData = (products: Product[] | null | undefined): Product[] => {
  if (!products) return [];
  return products.map(product => ({
    ...product,
    category: inferProductCategory(product.product_name)
  }));
};

export const getProductComparison = async (companies: string[]): Promise<Product[]> => {
  try {
    console.log('Fetching products for companies:', companies);
    
    // Use the checkAndRetryProductAvailability function which handles the webhook and waiting
    return await checkAndRetryProductAvailability(companies);
    
  } catch (error) {
    console.error('Error fetching product comparison:', error);
    throw error;
  }
};

export const getAllProducts = async (): Promise<Product[]> => {
  try {
    const { data: supabaseData, error: supabaseError } = await supabase
      .from('products')
      .select('*')
      .then();

    if (supabaseError) {
      throw supabaseError;
    }

    return processProductData(supabaseData || []);
  } catch (error) {
    console.error('Error fetching all products:', error);
    throw error;
  }
};

export const checkSupabaseProducts = async (companies: string[]): Promise<Product[]> => {
  try {
    const { data: supabaseData, error: supabaseError } = await supabase
      .from('products')
      .select('*')
      .in('company_name', companies)
      .then();

    if (supabaseError) {
      throw supabaseError;
    }

    return processProductData(supabaseData || []);
  } catch (error) {
    console.error('Error checking Supabase products:', error);
    throw error;
  }
};

export const initiateProductScraping = async (companies: string[]): Promise<{
  success: boolean;
  message: string;
  companies: string[];
}> => {
  try {
    const response = await api.post<ScrapeResponse>('/api/scrape/', {
      companies,
    });

    return {
      success: true,
      message: response.data.message,
      companies: response.data.companies,
    };
  } catch (error) {
    console.error('Error initiating scraping:', error);
    throw error;
  }
};

export const checkAndRetryProductAvailability = async (companies: string[]): Promise<Product[]> => {
  try {
    // First check in Supabase
    const { data: supabaseData, error: supabaseError } = await supabase
      .from('products')
      .select('*')
      .in('company_name', companies)
      .then();

    if (supabaseError) {
      throw supabaseError;
    }

    if (supabaseData && supabaseData.length > 0) {
      return processProductData(supabaseData);
    }

    // If no data found, send scrape request
    console.log('No products found, initiating scrape request...');
    await axios.post(`${API_BASE_URL}/api/scrape/`, { companies });

    // Wait for 10 seconds after scrape request
    console.log('Waiting for 10 seconds before checking Supabase...');
    await new Promise(resolve => setTimeout(resolve, 10000)); // Wait for 10 seconds

    // Check Supabase again after waiting
    console.log('Checking Supabase after waiting...');
    const { data: retryData, error: retryError } = await supabase
      .from('products')
      .select('*')
      .in('company_name', companies)
      .then();

    if (retryError) {
      throw retryError;
    }

    // If still no data, return empty array
    if (!retryData || retryData.length === 0) {
      console.log('No products found after waiting');
      return [];
    }

    console.log('Products found after waiting');
    return processProductData(retryData);
  } catch (error) {
    console.error('Error in checking and retrying product availability:', error);
    throw error;
  }
};
