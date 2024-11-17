from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from supabase import create_client, Client
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from django.core.cache import cache
from rest_framework.throttling import AnonRateThrottle
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY')
)

# Get Make.com webhook URL
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL')

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def create(self, request):
        try:
            data = request.data
            result = supabase.table('products').insert({
                'company_name': data['company_name'],
                'product_name': data['product_name'],
                'price': float(data['price']),
                'rating': float(data['rating']),
                'reviews': data['reviews']
            }).execute()
            
            return Response(result.data[0], status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

def validate_company_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError('Company name must be a non-empty string')
    if not re.match(r'^[a-zA-Z0-9\s\-\.]+$', name):
        raise ValidationError('Company name contains invalid characters')
    return name.strip()

@api_view(['POST'])
def scrape_products(request):
    try:
        primary_company = request.data.get('primary_company')
        competitor_companies = request.data.get('competitor_companies', [])
        
        # Validate company names
        try:
            primary_company = validate_company_name(primary_company)
            competitor_companies = [validate_company_name(comp) for comp in competitor_companies]
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Check rate limit
        cache_key = f'scrape_request_{request.META.get("REMOTE_ADDR")}'
        if cache.get(cache_key):
            return Response(
                {'error': 'Please wait before making another request'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        cache.set(cache_key, True, 60)  # 1 minute cooldown
        
        if not MAKE_WEBHOOK_URL:
            return Response(
                {'error': 'Make.com webhook URL not configured'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Prepare data for Make.com webhook
        webhook_data = {
            'primary_company': primary_company,
            'competitor_companies': competitor_companies,
            'supabase_url': os.getenv('SUPABASE_URL'),
            'supabase_key': os.getenv('SUPABASE_KEY'),
            'callback_url': request.build_absolute_uri('/api/webhook/scrape-callback/')
        }

        # Send request to Make.com webhook with timeout
        try:
            response = requests.post(MAKE_WEBHOOK_URL, json=webhook_data, timeout=10)
            response.raise_for_status()
        except requests.Timeout:
            return Response(
                {'error': 'Make.com webhook timeout'}, 
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.RequestException as e:
            return Response(
                {'error': f'Make.com webhook error: {str(e)}'}, 
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({
            'message': 'Scraping initiated successfully',
            'companies': [primary_company] + competitor_companies
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def scrape_callback(request):
    """Callback endpoint for Make.com to send scraped data"""
    try:
        print("Received webhook callback from Make.com")
        print("Request data:", request.data)
        
        scraped_data = request.data
        
        # Insert scraped data into Supabase
        for product in scraped_data:
            print(f"Processing product: {product['product_name']} from {product['company_name']}")
            result = supabase.table('products').insert({
                'company_name': product['company_name'],
                'product_name': product['product_name'],
                'price': float(product['price']),
                'rating': float(product['rating']),
                'reviews': product['reviews']
            }).execute()
            print(f"Inserted product into Supabase: {result.data}")
        
        return Response({'message': 'Data processed successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error in scrape_callback: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def compare_products(request):
    try:
        primary_company = request.data.get('primary_company')
        competitor_companies = request.data.get('competitor_companies', [])
        
        # Get product comparison data
        comparison = supabase.rpc(
            'get_product_comparison',
            {
                'primary_company': primary_company,
                'competitor_companies': competitor_companies
            }
        ).execute()
        
        # Get company statistics
        stats = supabase.rpc(
            'get_company_statistics',
            {
                'company_names': [primary_company] + competitor_companies
            }
        ).execute()
        
        response_data = {
            'comparison': comparison.data,
            'statistics': stats.data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
