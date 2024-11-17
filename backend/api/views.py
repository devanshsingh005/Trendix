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
from django.conf import settings
import logging

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=settings.SUPABASE_URL,
    supabase_key=settings.SUPABASE_KEY
)

# Get Make.com webhook URL
MAKE_WEBHOOK_URL = os.getenv('MAKE_WEBHOOK_URL', 'https://hook.eu1.make.com/yourwebhookurl')

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
@throttle_classes([AnonRateThrottle])
def scrape_products(request):
    try:
        # Validate input
        company_names = request.data.get('company_names', [])
        if not company_names:
            return Response({'error': 'No company names provided'}, status=400)

        # Make webhook call to Make.com
        try:
            response = requests.post(
                MAKE_WEBHOOK_URL,
                json={'company_names': company_names},
                timeout=10
            )
            response.raise_for_status()
            return Response({'message': 'Scraping initiated'}, status=202)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error calling Make.com webhook: {str(e)}")
            return Response(
                {'error': 'Failed to initiate scraping. Please try again later.'},
                status=503
            )

    except Exception as e:
        logging.exception("Error in scrape_products view")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def scrape_callback(request):
    try:
        # Log the incoming data
        logging.info("Received webhook callback from Make.com")
        logging.debug(f"Callback data: {request.data}")

        # Process the scraped data
        products_data = request.data.get('products', [])
        if not products_data:
            return Response({'error': 'No product data received'}, status=400)

        # Save products to database
        for product in products_data:
            try:
                Product.objects.create(**product)
            except Exception as e:
                logging.error(f"Error saving product: {str(e)}")
                continue

        return Response({'message': f'Processed {len(products_data)} products'})

    except Exception as e:
        logging.exception("Error in scrape_callback view")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def compare_products(request):
    try:
        # Get products from database
        company_names = request.data.get('company_names', [])
        if not company_names:
            return Response({'error': 'No company names provided'}, status=400)

        products = []
        for company in company_names:
            product = Product.objects.filter(company_name=company).order_by('-created_at').first()
            if product:
                products.append({
                    'company_name': product.company_name,
                    'product_name': product.product_name,
                    'price': str(product.price),
                    'rating': str(product.rating),
                    'reviews': product.reviews
                })

        if not products:
            return Response({'error': 'No products found for the specified companies'}, status=404)

        return Response(products)

    except Exception as e:
        logging.exception("Error in compare_products view")
        return Response({'error': str(e)}, status=500)
