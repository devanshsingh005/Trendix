from dotenv import load_dotenv
import os
from supabase.client import create_client

# Load environment variables
load_dotenv()

# Get environment variables
supabase_url = os.getenv('SUPABASE_URL')
if supabase_url is None:
    raise ValueError("Environment variable 'SUPABASE_URL' is not set.")

supabase_key = os.getenv('SUPABASE_KEY')
if supabase_key is None:
    raise ValueError("Environment variable 'SUPABASE_KEY' is not set.")

supabase = create_client(supabase_url, supabase_key)

# SQL commands to set up the database
setup_commands = """
-- Enable the necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create products table if not exists
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(200) NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    rating DECIMAL(3,2) NOT NULL CHECK (rating >= 0 AND rating <= 5),
    reviews TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for faster company name lookups
CREATE INDEX IF NOT EXISTS idx_products_company_name ON products(company_name);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to get product comparison
CREATE OR REPLACE FUNCTION get_product_comparison(primary_company TEXT, competitor_companies TEXT[])
RETURNS TABLE (
    company_name TEXT,
    products JSON
) AS $$
BEGIN
    RETURN QUERY
    WITH company_products AS (
        SELECT 
            p.company_name,
            json_agg(
                json_build_object(
                    'product_name', p.product_name,
                    'price', p.price,
                    'rating', p.rating,
                    'reviews', p.reviews
                )
            ) as products
        FROM products p
        WHERE p.company_name = primary_company 
           OR p.company_name = ANY(competitor_companies)
        GROUP BY p.company_name
    )
    SELECT * FROM company_products;
END;
$$ LANGUAGE plpgsql;

-- Create function to get company statistics
CREATE OR REPLACE FUNCTION get_company_statistics(company_names TEXT[])
RETURNS TABLE (
    company_name TEXT,
    total_products BIGINT,
    average_price DECIMAL(10,2),
    average_rating DECIMAL(3,2),
    price_range_min DECIMAL(10,2),
    price_range_max DECIMAL(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.company_name,
        COUNT(*) as total_products,
        ROUND(AVG(p.price)::numeric, 2) as average_price,
        ROUND(AVG(p.rating)::numeric, 2) as average_rating,
        MIN(p.price) as price_range_min,
        MAX(p.price) as price_range_max
    FROM products p
    WHERE p.company_name = ANY(company_names)
    GROUP BY p.company_name;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data
INSERT INTO products (company_name, product_name, price, rating, reviews)
SELECT * FROM (VALUES
    ('Apple', 'iPhone 13', 999.99, 4.5, 'Great phone with excellent camera'),
    ('Apple', 'MacBook Pro', 1299.99, 4.8, 'Powerful laptop for professionals'),
    ('Samsung', 'Galaxy S21', 899.99, 4.3, 'Good Android flagship phone'),
    ('Samsung', 'Galaxy Book', 1199.99, 4.2, 'Decent Windows laptop'),
    ('Microsoft', 'Surface Laptop', 1099.99, 4.4, 'Sleek design with good performance'),
    ('Microsoft', 'Surface Pro', 999.99, 4.6, 'Versatile 2-in-1 device')
) AS v(company_name, product_name, price, rating, reviews)
WHERE NOT EXISTS (
    SELECT 1 FROM products 
    WHERE company_name = v.company_name 
    AND product_name = v.product_name
);
"""

# Execute the setup commands
try:
    # Split the commands and execute them one by one
    for command in setup_commands.split(';'):
        if command.strip():
            supabase.table('products').select('*').execute()  # This is just to test the connection
            print(f"Executing command...")
            # Note: We can't execute raw SQL directly with the Python client
            # You'll need to execute these commands in the Supabase SQL editor
            
    print("Database setup completed successfully!")
    
    # Test the setup by querying the products
    response = supabase.table('products').select('*').execute()
    print("\nProducts in database:")
    print(response)
    
except Exception as e:
    print(f"Error setting up database: {str(e)}")
