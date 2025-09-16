from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import json

app = Flask(__name__)
CORS(app)

# Load vehicle data
df = pd.read_csv('inventory.csv')

# Clean and prepare data
df['MSRP_numeric'] = df['MSRP'].str.replace('$', '').str.replace(',', '').astype(float)
df['Year'] = df['Year'].astype(int)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/vehicles')
def get_vehicles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    search = request.args.get('search', '')
    
    # Filters
    model_filter = request.args.get('model', '')
    year_filter = request.args.get('year', '')
    trim_filter = request.args.get('trim', '')
    body_style_filter = request.args.get('body_style', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', '')
    
    # Start with all data
    filtered_df = df.copy()
    
    # Apply search filter with robustness
    if search:
        # Normalize search term for robustness (remove hyphens, spaces, make lowercase)
        normalized_search = search.replace('-', '').replace(' ', '').lower()
        
        search_cols = ['Model', 'Trim', 'Exterior Color', 'Interior Color', 'Engine']
        
        try:
            # Original search
            original_mask = filtered_df[search_cols].astype(str).apply(
                lambda x: x.str.contains(search, case=False, na=False, regex=False)
            ).any(axis=1)
            
            # Normalized search (remove hyphens and spaces)
            normalized_mask = filtered_df[search_cols].astype(str).apply(
                lambda x: x.str.replace('-', '', regex=False).str.replace(' ', '', regex=False).str.lower().str.contains(normalized_search, case=False, na=False, regex=False)
            ).any(axis=1)
            
            # Combine both search approaches
            search_mask = original_mask | normalized_mask
            filtered_df = filtered_df[search_mask]
            
        except Exception as e:
            # Fallback to simple search if there's any error
            print(f"Search error: {e}")
    
    # Apply filters
    if model_filter:
        filtered_df = filtered_df[filtered_df['Model'] == model_filter]
    if year_filter:
        filtered_df = filtered_df[filtered_df['Year'] == int(year_filter)]
    if trim_filter:
        filtered_df = filtered_df[filtered_df['Trim'] == trim_filter]
    if body_style_filter:
        filtered_df = filtered_df[filtered_df['Body Style'] == body_style_filter]
    if min_price is not None:
        filtered_df = filtered_df[filtered_df['MSRP_numeric'] >= min_price]
    if max_price is not None:
        filtered_df = filtered_df[filtered_df['MSRP_numeric'] <= max_price]
    
    # Apply sorting
    if sort_by == 'price_low':
        filtered_df = filtered_df.sort_values('MSRP_numeric', ascending=True)
    elif sort_by == 'price_high':
        filtered_df = filtered_df.sort_values('MSRP_numeric', ascending=False)
    else:
        # Default sort by year desc, then model
        filtered_df = filtered_df.sort_values(['Year', 'Model'], ascending=[False, True])
    
    # Calculate pagination
    total = len(filtered_df)
    start = (page - 1) * per_page
    end = start + per_page
    
    # Helper function to handle NaN values
    def safe_value(value):
        if pd.isna(value):
            return ''
        return value
    
    # Get page data
    page_data = filtered_df.iloc[start:end]
    
    # Convert to records
    vehicles = []
    for _, row in page_data.iterrows():
        # Use real photo URLs from scraped data
        photo_urls_str = safe_value(row['Photo URLs'])
        photos = [url.strip() for url in photo_urls_str.split(',') if url.strip()] if photo_urls_str else [
            "https://via.placeholder.com/280x180/2a2a2a/666?text=No+Image"
        ]
        
        vehicle = {
            'vin': safe_value(row['VIN']),
            'year': int(row['Year']),
            'make': safe_value(row['Make']),
            'model': safe_value(row['Model']),
            'trim': safe_value(row['Trim']),
            'exterior_color': safe_value(row['Exterior Color']),
            'interior_color': safe_value(row['Interior Color']),
            'msrp': safe_value(row['MSRP']),
            'fuel_economy': safe_value(row['Fuel Economy']),
            'engine': safe_value(row['Engine']),
            'transmission': safe_value(row['Transmission']),
            'body_style': safe_value(row['Body Style']),
            'stock_number': safe_value(row['Stock Number']),
            'photos': photos
        }
        vehicles.append(vehicle)
    
    return jsonify({
        'vehicles': vehicles,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/filters')
def get_filters():
    """Get available filter options"""
    filters = {
        'models': sorted(df['Model'].unique().tolist()),
        'years': sorted(df['Year'].unique().tolist(), reverse=True),
        'trims': sorted(df['Trim'].unique().tolist()),
        'body_styles': sorted(df['Body Style'].unique().tolist()),
        'price_range': {
            'min': float(df['MSRP_numeric'].min()),
            'max': float(df['MSRP_numeric'].max())
        }
    }
    return jsonify(filters)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)