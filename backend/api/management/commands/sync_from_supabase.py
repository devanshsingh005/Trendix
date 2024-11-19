from django.core.management.base import BaseCommand
from api.models import Product
from django.conf import settings
from supabase import create_client, Client

class Command(BaseCommand):
    help = 'Sync products from Supabase to local database'

    def handle(self, *args, **options):
        # Initialize Supabase client
        supabase: Client = create_client(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )

        # Get all products from Supabase
        result = supabase.table('products').select('*').execute()
        products = result.data

        self.stdout.write(f"Found {len(products)} products in Supabase")

        # Import each product
        for product in products:
            try:
                # Check if product exists
                existing = Product.objects.filter(
                    company_name=product['company_name'],
                    product_name=product['product_name']
                ).first()

                if existing:
                    # Update existing product
                    existing.price = float(product['price'])
                    existing.rating = float(product['rating'])
                    existing.reviews = int(str(product['reviews']).replace(',', ''))
                    existing.save()
                    self.stdout.write(f"Updated: {product['company_name']} - {product['product_name']}")
                else:
                    # Create new product
                    Product.objects.create(
                        company_name=product['company_name'],
                        product_name=product['product_name'],
                        price=float(product['price']),
                        rating=float(product['rating']),
                        reviews=int(str(product['reviews']).replace(',', ''))
                    )
                    self.stdout.write(f"Created: {product['company_name']} - {product['product_name']}")

            except Exception as e:
                self.stderr.write(f"Error with product {product}: {str(e)}")

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {len(products)} products from Supabase"))
