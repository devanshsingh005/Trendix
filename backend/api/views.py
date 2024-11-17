from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from supabase import create_client
import os
from datetime import datetime
import requests

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
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

@api_view(['POST'])
def scrape_products(request):
    try:
        primary_company = request.data.get('primary_company')
        competitor_companies = request.data.get('competitor_companies', [])
        
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

        # Send request to Make.com webhook
        response = requests.post(MAKE_WEBHOOK_URL, json=webhook_data)
        
        if response.status_code != 200:
            return Response(
                {'error': 'Failed to trigger Make.com webhook'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
