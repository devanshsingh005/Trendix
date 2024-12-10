from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from supabase import create_client, Client
import os
import logging
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re
from django.conf import settings

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY
)

# Get Make.com webhook URL
MAKE_WEBHOOK_URL = 'https://hook.eu2.make.com/0udpdkarnhtlsx1fgyeu9hxych3mj91c'

# Test mode flag - set to False to use real Make.com webhook
TEST_MODE = False

def insert_sample_data():
    """Insert sample product data into Supabase."""
    try:
        sample_data = [
            {'company_name': 'Samsung', 'product_name': 'Galaxy S21', 'price': 899.99, 'rating': 4.3, 'reviews': 1500},
            {'company_name': 'Samsung', 'product_name': 'Galaxy Tab S7', 'price': 649.99, 'rating': 4.5, 'reviews': 800},
            {'company_name': 'Apple', 'product_name': 'iPhone 13', 'price': 999.99, 'rating': 4.6, 'reviews': 2000},
            {'company_name': 'Apple', 'product_name': 'iPad Pro', 'price': 799.99, 'rating': 4.7, 'reviews': 1200},
            {'company_name': 'Google', 'product_name': 'Pixel 6', 'price': 699.99, 'rating': 4.4, 'reviews': 900}
        ]
        
        # Insert the sample data
        response = supabase.table('products').insert(sample_data).execute()
        logging.info(f"Sample data inserted successfully: {response.data}")
        return True
    except Exception as e:
        logging.error(f"Error inserting sample data: {str(e)}")
        return False

def verify_webhook_url():
    try:
        # Test the webhook URL with a simple ping
        response = requests.post(
            MAKE_WEBHOOK_URL,
            json={'test': True, 'timestamp': datetime.now().isoformat()},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        logging.info(f"Webhook verification response: {response.status_code}")
        return response.status_code in (200, 201, 202)
    except Exception as e:
        logging.error(f"Webhook verification failed: {str(e)}")
        return False

# Verify webhook URL on startup
if not TEST_MODE:
    webhook_available = verify_webhook_url()
    if not webhook_available:
        logging.error("Make.com webhook is not responding. Falling back to test mode.")
        TEST_MODE = True

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request):
        try:
            data = request.data
            logger.info(f"ProductViewSet.create received data: {json.dumps(data, indent=2)}")

            # Save to Supabase
            supabase_result = supabase.table('products').insert({
                'company_name': data['company_name'],
                'product_name': data['product_name'],
                'price': float(data['price']),
                'rating': float(data['rating']),
                'reviews': data['reviews']
            }).execute()
            logger.info(f"Saved to Supabase: {json.dumps(supabase_result.data[0], indent=2)}")

            # Save to local database
            product = Product.objects.create(
                company_name=data['company_name'],
                product_name=data['product_name'],
                price=float(data['price']),
                rating=float(data['rating']),
                reviews=int(str(data['reviews']).replace(',', ''))
            )
            logger.info(f"Saved to local database: {product.id}")

            return Response(supabase_result.data[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error in ProductViewSet.create: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def validate_company_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Company name must be a non-empty string')
    if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', name):
        raise ValidationError('Company name contains invalid characters')
    # Normalize company name to title case
    return name.strip().title()

def get_callback_url(request):
    """Get the appropriate callback URL based on the environment"""
    if 'localhost' in request.get_host():
        # Local development
        return f"{request.build_absolute_uri('/').rstrip('/')}/api/webhook/scrape-callback/"
    else:
        # Production
        return "https://ayushthegreat.pythonanywhere.com/api/webhook/scrape-callback/"

@api_view(['GET', 'POST'])
@throttle_classes([AnonRateThrottle])
def scrape_products(request):
    try:
        # Get companies from either POST data or GET parameters
        if request.method == 'POST':
            companies = request.data.get('companies', [])
        else:
            companies_param = request.GET.get('companies', '')
            companies = [c.strip() for c in companies_param.split(',')] if companies_param else []
            
        logging.info(f"Received scraping request for companies: {companies}")
        
        if not companies:
            return Response({'error': 'No companies provided'}, status=400)

        # Validate company names
        validated_companies = []
        for company in companies:
            try:
                validated_name = validate_company_name(company)
                validated_companies.append(validated_name)
                logging.info(f"Validated company name: {validated_name}")
            except ValidationError as e:
                logging.error(f"Invalid company name '{company}': {str(e)}")
                return Response({'error': f'Invalid company name "{company}": {str(e)}'}, status=400)

        # Clear old products for these companies
        Product.objects.filter(company_name__in=validated_companies).delete()
        logging.info(f"Cleared old products for companies: {validated_companies}")

        if TEST_MODE:
            # Test mode: Create sample data
            logging.info("TEST MODE: Creating sample data")
            for company in validated_companies:
                sample_data = {
                    'company_name': company,
                    'product_name': f"Sample Product from {company}",
                    'price': 99.99,
                    'rating': 4.5,
                    'reviews': 100
                }
                Product.objects.create(**sample_data)
                logging.info(f"Created sample product for {company}")

            return Response({
                'message': 'Sample data created successfully',
                'companies': validated_companies,
                'mode': 'test'
            }, status=202)
        else:
            # Production mode: Call Make.com webhook for each company
            callback_url = get_callback_url(request)
            successful_requests = []
            failed_requests = []

            for company in validated_companies:
                try:
                    webhook_data = {
                        'companyName': company  # Match exact structure expected by Make.com
                    }
                    
                    logging.info(f"Sending request to Make.com webhook for company: {company}")
                    logging.info(f"Webhook URL: {MAKE_WEBHOOK_URL}")
                    logging.info(f"Callback URL: {callback_url}")
                    logging.info(f"Request data: {json.dumps(webhook_data, indent=2)}")
                    
                    response = requests.post(
                        MAKE_WEBHOOK_URL,
                        json=webhook_data,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'Pullup/1.0'
                        },
                        timeout=180  # Increased timeout to 3 minutes
                    )
                    
                    logging.info(f"Make.com response status for {company}: {response.status_code}")
                    try:
                        response_json = response.json()
                        logging.info(f"Make.com response body for {company}: {json.dumps(response_json, indent=2)}")
                    except json.JSONDecodeError:
                        logging.info(f"Make.com response body for {company} (raw): {response.text}")
                    
                    if response.status_code in (200, 201, 202):
                        successful_requests.append(company)
                    else:
                        failed_requests.append({
                            'company': company,
                            'status': response.status_code,
                            'error': response.text
                        })
                        logging.error(f"Make.com webhook failed for {company}: {response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    failed_requests.append({
                        'company': company,
                        'error': str(e)
                    })
                    logging.error(f"Error calling Make.com webhook for {company}: {str(e)}")

            # Return response based on results
            if successful_requests:
                status_code = 202 if not failed_requests else 207  # 207 Multi-Status if partial success
                return Response({
                    'message': 'Scraping initiated',
                    'successful_companies': successful_requests,
                    'failed_companies': failed_requests,
                    'callback_url': callback_url,
                    'mode': 'production'
                }, status=status_code)
            else:
                return Response({
                    'error': 'Failed to initiate scraping for all companies',
                    'failed_companies': failed_requests
                }, status=503)
                    
    except Exception as e:
        logging.exception("Error in scrape_products view")
        return Response({
            'error': str(e)
        }, status=500)

# Set up file logging
try:
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'webhook.log')
    
    # Test if we can write to the file
    with open(log_file, 'a') as f:
        f.write(f"\n=== Log started at {datetime.now()} ===\n")
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    logger = logging.getLogger('webhook')
    logger.setLevel(logging.INFO)
    # Remove any existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(file_handler)
    logger.info("Logging system initialized successfully")
except Exception as e:
    print(f"Error setting up logging: {str(e)}")
    # Fallback to console logging
    logger = logging.getLogger('webhook')
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    logger.error(f"Failed to set up file logging, falling back to console: {str(e)}")

@api_view(['POST'])
def scrape_callback(request):
    try:
        # Log the incoming data
        logger.info("==================== WEBHOOK CALLBACK START ====================")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Raw request data: {request.body.decode()}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Handle both direct array and wrapped object format
            if isinstance(request.data, list):
                products_data = request.data
                logger.info("Received data as direct array")
            else:
                products_data = request.data.get('products', [])
                logger.info("Received data as wrapped object")
                
            logger.info(f"Extracted products data: {json.dumps(products_data, indent=2)}")
            logger.info(f"Number of products received: {len(products_data)}")
        except Exception as e:
            logger.error(f"Error parsing request data: {str(e)}")
            logger.error(f"Request data type: {type(request.data)}")
            logger.error(f"Request data content: {request.data}")
            return Response({'error': 'Invalid data format'}, status=400)
        
        if not products_data:
            logger.error("No product data received in webhook callback")
            return Response({'error': 'No product data received'}, status=400)

        # Log current database state
        existing_count = Product.objects.count()
        logger.info(f"Current products in database: {existing_count}")

        # Validate and save products to database
        saved_products = []
        for product_data in products_data:
            try:
                # Log each product being processed
                logger.info(f"\nProcessing product: {json.dumps(product_data, indent=2)}")
                
                # Validate required fields
                required_fields = ['company_name', 'product_name', 'price', 'rating', 'reviews']
                missing_fields = [field for field in required_fields if field not in product_data]
                if missing_fields:
                    logger.error(f"Missing required fields for product: {missing_fields}")
                    continue

                # Clean and convert numeric fields
                try:
                    # Handle price (might be already numeric from Make.com)
                    if isinstance(product_data['price'], (int, float)):
                        price = float(product_data['price'])
                    else:
                        price_str = str(product_data['price']).replace('$', '').replace(',', '').strip()
                        price = float(price_str)
                    product_data['price'] = price
                    logger.info(f"Converted price: {price}")

                    # Handle rating (might be already numeric from Make.com)
                    if isinstance(product_data['rating'], (int, float)):
                        rating = float(product_data['rating'])
                    else:
                        rating_str = str(product_data['rating']).strip()
                        rating = float(rating_str)
                    product_data['rating'] = rating
                    logger.info(f"Converted rating: {rating}")

                    # Handle reviews (might be string or number)
                    if isinstance(product_data['reviews'], int):
                        reviews = product_data['reviews']
                    else:
                        reviews_str = str(product_data['reviews']).replace(',', '').strip()
                        reviews = int(reviews_str)
                    product_data['reviews'] = reviews
                    logger.info(f"Converted reviews: {reviews}")

                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting numeric fields: {str(e)}")
                    logger.error(f"Product data: {product_data}")
                    continue

                # Save to database
                logger.info(f"Attempting to save product to database: {product_data}")
                
                try:
                    # Check if product already exists in local database
                    existing_product = Product.objects.filter(
                        company_name=product_data['company_name'],
                        product_name=product_data['product_name']
                    ).first()
                    
                    if existing_product:
                        # Update existing product in local database
                        for key, value in product_data.items():
                            setattr(existing_product, key, value)
                        existing_product.save()
                        saved_products.append(existing_product)
                        logger.info(f"Updated existing product in local database: {existing_product.product_name}")
                    else:
                        # Create new product in local database
                        new_product = Product.objects.create(**product_data)
                        saved_products.append(new_product)
                        logger.info(f"Created new product in local database: {new_product.product_name}")

                    # Save to Supabase
                    supabase_data = {
                        'company_name': product_data['company_name'],
                        'product_name': product_data['product_name'],
                        'price': float(product_data['price']),
                        'rating': float(product_data['rating']),
                        'reviews': str(product_data['reviews'])
                    }
                    
                    # Check if product exists in Supabase
                    supabase_result = supabase.table('products').select('*').eq(
                        'company_name', product_data['company_name']
                    ).eq('product_name', product_data['product_name']).execute()
                    
                    if supabase_result.data:
                        # Update existing product in Supabase
                        supabase_id = supabase_result.data[0]['id']
                        supabase.table('products').update(supabase_data).eq('id', supabase_id).execute()
                        logger.info(f"Updated existing product in Supabase: {product_data['product_name']}")
                    else:
                        # Create new product in Supabase
                        supabase.table('products').insert(supabase_data).execute()
                        logger.info(f"Created new product in Supabase: {product_data['product_name']}")

                except Exception as e:
                    logger.error(f"Error saving product: {str(e)}")
                    logger.error(f"Product data: {product_data}")
                    continue

            except Exception as e:
                logger.error(f"Error saving product: {str(e)}")
                logger.error(f"Product data that caused error: {product_data}")
                continue

        # Log final database state
        new_count = Product.objects.count()
        logger.info(f"\nFinal products in database: {new_count}")
        logger.info(f"Change in product count: {new_count - existing_count}")

        if not saved_products:
            logger.warning("No products were saved to database")
            return Response({
                'message': 'No products were saved',
                'error': 'Failed to save any products'
            }, status=400)

        # Return success response with saved products
        response_data = {
            'message': f'Successfully processed {len(saved_products)} products',
            'processed_count': len(saved_products),
            'products': [
                {
                    'company_name': p.company_name,
                    'product_name': p.product_name,
                    'price': str(p.price),
                    'rating': str(p.rating),
                    'reviews': p.reviews
                } for p in saved_products
            ]
        }
        logger.info(f"Returning success response: {json.dumps(response_data, indent=2)}")
        logger.info("==================== WEBHOOK CALLBACK END ====================\n")
        return Response(response_data)

    except Exception as e:
        logger.exception("Error in scrape_callback view")
        return Response({'error': str(e)}, status=500)

@api_view(['GET', 'POST'])
def compare_products(request):
    try:
        # Get companies from either POST data or GET parameters
        if request.method == 'POST':
            companies = request.data.get('companies', [])
        else:
            companies_param = request.GET.get('companies', '')
            companies = [c.strip() for c in companies_param.split(',')] if companies_param else []
        
        logging.info(f"Comparing products for companies: {companies}")
        
        if not companies:
            return Response({
                'status': 'error',
                'message': 'No company names provided. Use ?companies=company1,company2 for GET or {"companies": ["company1", "company2"]} for POST'
            }, status=400)

        # Query Supabase directly for better performance
        query = supabase.table('products').select('*').in_('company_name', companies)
        response = query.execute()
        
        if not response.data:
            # Initiate scraper if no products found
            logging.info("No products found for companies, initiating scraping...")
            try:
                # Call the scrape_products view function directly
                scrape_response = scrape_products(request._request)
                if scrape_response.status_code in [200, 201, 202]:
                    return Response({
                        'status': 'accepted',
                        'message': 'Scraping initiated. Please check back later for results.',
                        'companies': companies
                    }, status=202)
                else:
                    return scrape_response
            except Exception as scrape_error:
                logging.exception("Error initiating scraping")
                return Response({
                    'status': 'error',
                    'message': f'Failed to initiate scraping: {str(scrape_error)}'
                }, status=500)
        
        # Group products by company
        company_products = {}
        for product in response.data:
            company = product['company_name']
            if company not in company_products:
                company_products[company] = []
            company_products[company].append({
                'company_name': product['company_name'],
                'product_name': product['product_name'],
                'price': str(product['price']),
                'rating': str(product['rating']),
                'reviews': product['reviews']
            })
        
        # Get the best product for each company
        comparison_results = []
        for company, products in company_products.items():
            if products:
                best_product = sorted(products, key=lambda x: (float(x['rating']), int(x['reviews'])), reverse=True)[0]
                comparison_results.append(best_product)
        
        return Response({
            'status': 'success',
            'data': comparison_results
        })

    except Exception as e:
        logging.exception("Error in compare_products view")
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@throttle_classes([AnonRateThrottle])
def fetch_products(request):
    try:
        logging.info("Attempting to fetch products from Supabase...")
        logging.info(f"Supabase URL: {settings.SUPABASE_URL}")
        logging.info(f"Supabase key configured: {'Yes' if settings.SUPABASE_KEY else 'No'}")
        
        # Fetch products from Supabase
        response = supabase.table('products').select("*").execute()
        
        # Log the complete response for debugging
        logging.info("Supabase raw response:")
        logging.info(f"Response data: {response.data}")
        logging.info(f"Response status: {getattr(response, 'status_code', 'N/A')}")
        
        products = response.data if response.data else []
        logging.info(f"Number of products fetched: {len(products)}")
        
        # Convert decimal values to strings for JSON serialization
        formatted_products = []
        for product in products:
            logging.info(f"Processing product: {product}")
            formatted_product = {
                'id': str(product.get('id', '')),
                'company_name': str(product.get('company_name', '')),
                'product_name': str(product.get('product_name', '')),
                'price': float(product.get('price', 0)),
                'rating': float(product.get('rating', 0)),
                'reviews': int(product.get('reviews', 0))
            }
            logging.info(f"Formatted product: {formatted_product}")
            formatted_products.append(formatted_product)
        
        logging.info(f"Total formatted products: {len(formatted_products)}")
        return Response({
            'status': 'success',
            'data': formatted_products
        }, status=status.HTTP_200_OK)
            
    except Exception as e:
        logging.error(f"Error fetching products from Supabase: {str(e)}")
        logging.error(f"Exception type: {type(e)}")
        logging.error(f"Exception details:", exc_info=True)
        return Response({
            'status': 'error',
            'message': 'Failed to fetch products',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
