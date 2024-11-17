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
    return response.data;
  } catch (error) {
    throw new Error('Failed to initiate product scraping');
  }
};

export const getProductComparison = async () => {
  try {
    const response = await api.get<Product[]>('/api/compare/');
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch product comparison data');
  }
};

export const getAllProducts = async () => {
  try {
    const response = await api.get<Product[]>('/api/products/');
    return response.data;
  } catch (error) {
    throw new Error('Failed to fetch products');
  }
};
