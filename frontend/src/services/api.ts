import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
}

export const initiateProductScraping = async (companies: string[]) => {
  try {
    const response = await api.post('/api/scrape/', { companies });
    if (response.status === 202) {
      return {
        success: true,
        message: response.data.message,
        companies: response.data.companies
      };
    } else {
      throw new Error(response.data.error || 'Failed to initiate product scraping');
    }
  } catch (error: any) {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw new Error('Failed to initiate product scraping. Please try again.');
  }
};

export const getProductComparison = async (companies: string[]) => {
  try {
    const response = await api.post<Product[]>('/api/compare/', { companies });
    if (response.status === 404) {
      // Products not found yet, return empty array to continue polling
      return [];
    }
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      // Products not found yet, return empty array to continue polling
      return [];
    }
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw new Error('Failed to fetch product comparison data');
  }
};

export const getAllProducts = async () => {
  try {
    const response = await api.get<Product[]>('/api/products/');
    return response.data;
  } catch (error: any) {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error);
    }
    throw new Error('Failed to fetch products');
  }
};
