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
    
    # Start with all data
    filtered_df = df.copy()
    
    # Apply search filter
    if search:
        search_cols = ['Model', 'Trim', 'Exterior Color', 'Interior Color', 'Engine']
        search_mask = filtered_df[search_cols].astype(str).apply(
            lambda x: x.str.contains(search, case=False, na=False)
        ).any(axis=1)
        filtered_df = filtered_df[search_mask]
    
    # Apply filters
    if model_filter:
        filtered_df = filtered_df[filtered_df['Model'] == model_filter]
    if year_filter:
        filtered_df = filtered_df[filtered_df['Year'] == int(year_filter)]
    if trim_filter:
        filtered_df = filtered_df[filtered_df['Trim'] == trim_filter]
    if body_style_filter:
        filtered_df = filtered_df[filtered_df['Body Style'] == body_style_filter]
    if min_price:
        filtered_df = filtered_df[filtered_df['MSRP_numeric'] >= min_price]
    if max_price:
        filtered_df = filtered_df[filtered_df['MSRP_numeric'] <= max_price]
    
    # Calculate pagination
    total = len(filtered_df)
    start = (page - 1) * per_page
    end = start + per_page
    
    # Get page data
    page_data = filtered_df.iloc[start:end]
    
    # Convert to records
    vehicles = []
    for _, row in page_data.iterrows():
        # Generate sample vehicle photos (placeholder URLs)
        photos = [
            f"https://via.placeholder.com/400x300/0066cc/ffffff?text={row['Year']}+{row['Model']}",
            f"https://via.placeholder.com/400x300/cc6600/ffffff?text=Interior",
            f"https://via.placeholder.com/400x300/009900/ffffff?text=Side+View"
        ]
        
        vehicle = {
            'vin': row['VIN'],
            'year': int(row['Year']),
            'make': row['Make'],
            'model': row['Model'],
            'trim': row['Trim'],
            'exterior_color': row['Exterior Color'],
            'interior_color': row['Interior Color'],
            'msrp': row['MSRP'],
            'fuel_economy': row['Fuel Economy'],
            'engine': row['Engine'],
            'transmission': row['Transmission'],
            'body_style': row['Body Style'],
            'stock_number': row['Stock Number'],
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