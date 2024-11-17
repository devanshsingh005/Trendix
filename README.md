# Product Comparison Tool

A web application that helps investors evaluate products of a specified company and its competitors.

## Features

- Input primary company and competitor names
- Automated web scraping of product details using Make.com
- Storage of product data in Supabase
- Comparison view of product details including prices, ratings, and reviews

## Tech Stack

- Frontend: React with Material-UI
- Backend: Django with Django REST Framework
- Database: Supabase
- Web Scraping: Make.com

## Project Structure

```
Pullup/
├── backend/           # Django backend
│   ├── api/          # Django app for REST API
│   ├── pullup/       # Django project settings
│   └── requirements.txt
└── frontend/         # React frontend
    ├── src/
    │   ├── components/
    │   └── App.js
    └── package.json
```

## Setup Instructions

### Backend Setup

1. Create and activate a virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
DJANGO_SECRET_KEY=your-secret-key
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the development server:
```bash
python manage.py runserver
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm start
```

## Usage

1. Open http://localhost:3000 in your browser
2. Enter the primary company name
3. Add competitor companies using the "Add Competitor" button
4. Click "Compare Products" to initiate the comparison
5. View the comparison results in a grid layout

## API Endpoints

- `POST /api/scrape/`: Initiate web scraping for company products
- `GET /api/compare/`: Get product comparison data
- `GET /api/products/`: List all products
- `POST /api/products/`: Create a new product
- `GET /api/products/{id}/`: Get product details
- `PUT /api/products/{id}/`: Update product details
- `DELETE /api/products/{id}/`: Delete a product

## Make.com Integration

To set up the Make.com integration:

1. Create a new scenario in Make.com
2. Add an HTTP webhook trigger
3. Configure the scraping steps for your target marketplace
4. Set up the Supabase action to store the scraped data
5. Deploy the scenario

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
