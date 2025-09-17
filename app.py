from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Load vehicle data
df_new = pd.read_csv('inventoryNew.csv')
df_used = pd.read_csv('inventoryUsed.csv')

# Clean and prepare data for new inventory
df_new['MSRP_numeric'] = df_new['MSRP'].str.replace('$', '').str.replace(',', '').astype(float)
df_new['Year'] = df_new['Year'].astype(int)

# Clean and prepare data for used inventory (use Retail Price as price)
df_used['MSRP_numeric'] = df_used['Retail Price'].astype(str).str.replace('$', '').str.replace(',', '').astype(float)
df_used['Year'] = df_used['Year'].astype(int)
# Add empty MSRP column for used vehicles to maintain consistency
df_used['MSRP'] = df_used['Retail Price']  # Use retail price as display price

@app.route('/')
def index():
    # Add cache control headers to prevent browser caching during development
    response = app.make_response(render_template('index.html'))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/vehicles')
def get_vehicles():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    search = request.args.get('search', '')
    inventory_type = request.args.get('inventory_type', 'new')  # default to new
    
    # Filters
    model_filter = request.args.get('model', '')
    year_filter = request.args.get('year', '')
    trim_filter = request.args.get('trim', '')
    body_style_filter = request.args.get('body_style', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', '')
    
    # Select appropriate dataframe based on inventory type
    df = df_new if inventory_type == 'new' else df_used
    
    # Start with selected inventory data
    filtered_df = df.copy()
    
    # Apply multi-parameter search filter with robustness and exclusion support
    if search:
        search_terms = search.strip().split()  # Split by whitespace to get individual terms
        search_cols = ['Model', 'Trim', 'Exterior Color', 'Interior Color', 'Engine', 'VIN', 'Stock Number']
        
        # Separate include and exclude terms
        include_terms = [term for term in search_terms if not term.startswith('-')]
        exclude_terms = [term[1:] for term in search_terms if term.startswith('-') and len(term) > 1]
        
        try:
            # Process include terms (all must match)
            if include_terms:
                include_masks = []
                
                for term in include_terms:
                    # Normalize term for robustness (remove hyphens, spaces, make lowercase)
                    normalized_term = term.replace('-', '').replace(' ', '').lower()
                    
                    # Original search for this term
                    original_mask = filtered_df[search_cols].astype(str).apply(
                        lambda x: x.str.contains(term, case=False, na=False, regex=False)
                    ).any(axis=1)
                    
                    # Normalized search for this term (remove hyphens and spaces)
                    normalized_mask = filtered_df[search_cols].astype(str).apply(
                        lambda x: x.str.replace('-', '', regex=False).str.replace(' ', '', regex=False).str.lower().str.contains(normalized_term, case=False, na=False, regex=False)
                    ).any(axis=1)
                    
                    # Combine both approaches for this term
                    term_mask = original_mask | normalized_mask
                    include_masks.append(term_mask)
                
                # All include terms must match (AND logic)
                if include_masks:
                    combined_include_mask = include_masks[0]
                    for mask in include_masks[1:]:
                        combined_include_mask = combined_include_mask & mask
                    filtered_df = filtered_df[combined_include_mask]
            
            # Process exclude terms (none should match)
            if exclude_terms:
                exclude_masks = []
                
                for term in exclude_terms:
                    # Normalize term for robustness (remove hyphens, spaces, make lowercase)
                    normalized_term = term.replace('-', '').replace(' ', '').lower()
                    
                    # Original search for this term
                    original_mask = filtered_df[search_cols].astype(str).apply(
                        lambda x: x.str.contains(term, case=False, na=False, regex=False)
                    ).any(axis=1)
                    
                    # Normalized search for this term (remove hyphens and spaces)
                    normalized_mask = filtered_df[search_cols].astype(str).apply(
                        lambda x: x.str.replace('-', '', regex=False).str.replace(' ', '', regex=False).str.lower().str.contains(normalized_term, case=False, na=False, regex=False)
                    ).any(axis=1)
                    
                    # Combine both approaches for this term
                    term_mask = original_mask | normalized_mask
                    exclude_masks.append(term_mask)
                
                # Exclude vehicles that match any exclude term
                if exclude_masks:
                    combined_exclude_mask = exclude_masks[0]
                    for mask in exclude_masks[1:]:
                        combined_exclude_mask = combined_exclude_mask | mask
                    filtered_df = filtered_df[~combined_exclude_mask]
            
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
        
        # Base vehicle data
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
            'photos': photos,
            'inventory_type': inventory_type
        }
        
        # Add CarFax URL for used vehicles
        if inventory_type == 'used' and 'Carfax URL' in row:
            vehicle['carfax_url'] = safe_value(row['Carfax URL'])
            
        # Add vehicle link URL
        link_column = 'Vehicle Link' if inventory_type == 'new' else 'Full Link'
        if link_column in row:
            vehicle['vehicle_link'] = safe_value(row[link_column])
            
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
    inventory_type = request.args.get('inventory_type', 'new')
    
    # Select appropriate dataframe
    df = df_new if inventory_type == 'new' else df_used
    
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

@app.route('/api/inventory-status')
def get_inventory_status():
    """Get inventory last update timestamps"""
    try:
        new_modified = os.path.getmtime('inventoryNew.csv')
        used_modified = os.path.getmtime('inventoryUsed.csv')
        
        return jsonify({
            'new_updated': datetime.fromtimestamp(new_modified).strftime('%Y-%m-%d %I:%M %p'),
            'used_updated': datetime.fromtimestamp(used_modified).strftime('%Y-%m-%d %I:%M %p'),
            'new_count': len(df_new),
            'used_count': len(df_used)
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)