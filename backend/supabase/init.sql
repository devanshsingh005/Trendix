-- Enable the necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create products table
CREATE TABLE products (
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
CREATE INDEX idx_products_company_name ON products(company_name);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for product statistics
CREATE VIEW product_stats AS
SELECT 
    company_name,
    COUNT(*) as product_count,
    AVG(price) as avg_price,
    AVG(rating) as avg_rating
FROM products
GROUP BY company_name;

-- Create function to search products by company
CREATE OR REPLACE FUNCTION search_products_by_companies(company_names TEXT[])
RETURNS SETOF products AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM products
    WHERE company_name = ANY(company_names)
    ORDER BY company_name, rating DESC;
END;
$$ LANGUAGE plpgsql;

-- Create RLS (Row Level Security) policies
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Allow read access to all authenticated users
CREATE POLICY "Allow read access to all authenticated users"
    ON products FOR SELECT
    TO authenticated
    USING (true);

-- Allow insert access to authenticated users
CREATE POLICY "Allow insert access to authenticated users"
    ON products FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Allow update access to authenticated users
CREATE POLICY "Allow update access to authenticated users"
    ON products FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Sample data for testing
INSERT INTO products (company_name, product_name, price, rating, reviews) VALUES
    ('Apple', 'iPhone 13', 999.99, 4.5, 'Great phone with excellent camera'),
    ('Apple', 'MacBook Pro', 1299.99, 4.8, 'Powerful laptop for professionals'),
    ('Samsung', 'Galaxy S21', 899.99, 4.3, 'Good Android flagship phone'),
    ('Samsung', 'Galaxy Book', 1199.99, 4.2, 'Decent Windows laptop'),
    ('Microsoft', 'Surface Laptop', 1099.99, 4.4, 'Sleek design with good performance'),
    ('Microsoft', 'Surface Pro', 999.99, 4.6, 'Versatile 2-in-1 device');

-- Create a function to get product comparison
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

-- Comments for better understanding
COMMENT ON TABLE products IS 'Stores product information for company comparisons';
COMMENT ON COLUMN products.company_name IS 'Name of the company that makes the product';
COMMENT ON COLUMN products.product_name IS 'Name of the product';
COMMENT ON COLUMN products.price IS 'Current price of the product';
COMMENT ON COLUMN products.rating IS 'Average customer rating (0-5)';
COMMENT ON COLUMN products.reviews IS 'Aggregated customer reviews';

-- Create a function to get company statistics
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

-- Create an audit log table
CREATE TABLE product_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID REFERENCES products(id),
    action VARCHAR(10),
    changed_fields JSONB,
    changed_at TIMESTAMPTZ DEFAULT NOW(),
    changed_by UUID
);

-- Create trigger for audit logging
CREATE OR REPLACE FUNCTION log_product_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO product_audit_log (product_id, action, changed_fields, changed_by)
        VALUES (NEW.id, 'INSERT', to_jsonb(NEW), auth.uid());
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO product_audit_log (product_id, action, changed_fields, changed_by)
        VALUES (NEW.id, 'UPDATE', jsonb_strip_nulls(to_jsonb(NEW) - to_jsonb(OLD)), auth.uid());
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO product_audit_log (product_id, action, changed_fields, changed_by)
        VALUES (OLD.id, 'DELETE', to_jsonb(OLD), auth.uid());
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER products_audit
    AFTER INSERT OR UPDATE OR DELETE ON products
    FOR EACH ROW EXECUTE FUNCTION log_product_changes();
