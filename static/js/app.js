class VehicleInventory {
    constructor() {
        this.currentPage = 1;
        this.filters = {};
        this.searchTerm = '';
        this.init();
    }

    async init() {
        await this.loadFilters();
        await this.loadVehicles();
        this.setupEventListeners();
    }

    async loadFilters() {
        try {
            const response = await fetch('/api/filters');
            const filters = await response.json();
            
            this.populateSelect('model-filter', filters.models);
            this.populateSelect('year-filter', filters.years);
            this.populateSelect('trim-filter', filters.trims);
            this.populateSelect('body-style-filter', filters.body_styles);
            
            document.getElementById('min-price').placeholder = `Min ($${Math.round(filters.price_range.min).toLocaleString()})`;
            document.getElementById('max-price').placeholder = `Max ($${Math.round(filters.price_range.max).toLocaleString()})`;
        } catch (error) {
            console.error('Error loading filters:', error);
        }
    }

    populateSelect(elementId, options) {
        const select = document.getElementById(elementId);
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            select.appendChild(optionElement);
        });
    }

    async loadVehicles() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: 12,
                ...this.filters
            });

            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }

            const response = await fetch(`/api/vehicles?${params}`);
            const data = await response.json();
            
            this.renderVehicles(data.vehicles);
            this.renderPagination(data);
            this.updateResultsCount(data.total);
        } catch (error) {
            console.error('Error loading vehicles:', error);
            document.getElementById('vehicles-grid').innerHTML = '<p>Error loading vehicles. Please try again.</p>';
        }
    }

    renderVehicles(vehicles) {
        const grid = document.getElementById('vehicles-grid');
        
        if (vehicles.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #666;">NO VEHICLES FOUND</div>';
            return;
        }

        grid.innerHTML = vehicles.map(vehicle => `
            <div class="vehicle-card">
                <div class="photo-carousel" data-vehicle-id="${vehicle.vin}">
                    ${vehicle.photos.map((photo, index) => `
                        <img src="${photo}" alt="${vehicle.year} ${vehicle.make} ${vehicle.model}" 
                             class="${index === 0 ? 'active' : ''}" data-index="${index}" 
                             onerror="this.src='https://via.placeholder.com/280x180/2a2a2a/666?text=NO+IMAGE'">
                    `).join('')}
                    
                    ${vehicle.photos.length > 1 ? `
                    <div class="carousel-controls">
                        <button class="carousel-btn prev" onclick="this.closest('.photo-carousel').dispatchEvent(new CustomEvent('prevPhoto'))">‹</button>
                        <button class="carousel-btn next" onclick="this.closest('.photo-carousel').dispatchEvent(new CustomEvent('nextPhoto'))">›</button>
                    </div>
                    
                    <div class="photo-indicators">
                        ${vehicle.photos.map((_, index) => `
                            <span class="indicator ${index === 0 ? 'active' : ''}" 
                                  onclick="this.closest('.photo-carousel').dispatchEvent(new CustomEvent('goToPhoto', {detail: ${index}}))"></span>
                        `).join('')}
                    </div>
                    ` : ''}
                </div>
                
                <div class="vehicle-info">
                    <div class="vehicle-title">${vehicle.year} ${vehicle.make} ${vehicle.model} ${vehicle.trim}</div>
                    <div class="vehicle-price">${vehicle.msrp}</div>
                    
                    <div class="vehicle-details">
                        <div class="detail-row">
                            <span class="detail-label">VIN:</span>
                            <span class="detail-value">${vehicle.vin}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">STOCK:</span>
                            <span class="detail-value">${vehicle.stock_number}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">EXTERIOR:</span>
                            <span class="detail-value">${vehicle.exterior_color}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">INTERIOR:</span>
                            <span class="detail-value">${vehicle.interior_color}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">ENGINE:</span>
                            <span class="detail-value">${vehicle.engine}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">MPG:</span>
                            <span class="detail-value">${vehicle.fuel_economy}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">BODY:</span>
                            <span class="detail-value">${vehicle.body_style}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">TRANS:</span>
                            <span class="detail-value">${vehicle.transmission}</span>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Setup photo carousels
        this.setupCarousels();
    }

    setupCarousels() {
        document.querySelectorAll('.photo-carousel').forEach(carousel => {
            let currentIndex = 0;
            const images = carousel.querySelectorAll('img');
            const indicators = carousel.querySelectorAll('.indicator');

            const showPhoto = (index) => {
                images.forEach((img, i) => {
                    img.classList.toggle('active', i === index);
                });
                indicators.forEach((indicator, i) => {
                    indicator.classList.toggle('active', i === index);
                });
                currentIndex = index;
            };

            carousel.addEventListener('nextPhoto', () => {
                const nextIndex = (currentIndex + 1) % images.length;
                showPhoto(nextIndex);
            });

            carousel.addEventListener('prevPhoto', () => {
                const prevIndex = (currentIndex - 1 + images.length) % images.length;
                showPhoto(prevIndex);
            });

            carousel.addEventListener('goToPhoto', (e) => {
                showPhoto(e.detail);
            });
        });
    }

    renderPagination(data) {
        const pagination = document.getElementById('pagination');
        
        if (data.total_pages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `<button class="page-btn" ${data.page === 1 ? 'disabled' : ''} onclick="app.goToPage(${data.page - 1})">‹ Previous</button>`;
        
        // Page numbers
        const startPage = Math.max(1, data.page - 2);
        const endPage = Math.min(data.total_pages, data.page + 2);
        
        if (startPage > 1) {
            paginationHTML += `<button class="page-btn" onclick="app.goToPage(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span class="page-btn" style="border:none; cursor:default;">...</span>`;
            }
        }
        
        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `<button class="page-btn ${i === data.page ? 'active' : ''}" onclick="app.goToPage(${i})">${i}</button>`;
        }
        
        if (endPage < data.total_pages) {
            if (endPage < data.total_pages - 1) {
                paginationHTML += `<span class="page-btn" style="border:none; cursor:default;">...</span>`;
            }
            paginationHTML += `<button class="page-btn" onclick="app.goToPage(${data.total_pages})">${data.total_pages}</button>`;
        }
        
        // Next button
        paginationHTML += `<button class="page-btn" ${data.page === data.total_pages ? 'disabled' : ''} onclick="app.goToPage(${data.page + 1})">Next ›</button>`;
        
        pagination.innerHTML = paginationHTML;
    }

    updateResultsCount(total) {
        const resultsCount = document.getElementById('results-count');
        resultsCount.textContent = `${total} VEHICLES`;
    }

    setupEventListeners() {
        // Search
        document.getElementById('search-btn').addEventListener('click', () => this.performSearch());
        document.getElementById('search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.performSearch();
        });

        // Filters
        document.getElementById('model-filter').addEventListener('change', (e) => this.updateFilter('model', e.target.value));
        document.getElementById('year-filter').addEventListener('change', (e) => this.updateFilter('year', e.target.value));
        document.getElementById('trim-filter').addEventListener('change', (e) => this.updateFilter('trim', e.target.value));
        document.getElementById('body-style-filter').addEventListener('change', (e) => this.updateFilter('body_style', e.target.value));
        document.getElementById('min-price').addEventListener('change', (e) => this.updateFilter('min_price', e.target.value));
        document.getElementById('max-price').addEventListener('change', (e) => this.updateFilter('max_price', e.target.value));

        // Clear filters
        document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());
    }

    performSearch() {
        this.searchTerm = document.getElementById('search').value;
        this.currentPage = 1;
        this.loadVehicles();
    }

    updateFilter(key, value) {
        if (value) {
            this.filters[key] = value;
        } else {
            delete this.filters[key];
        }
        this.currentPage = 1;
        this.loadVehicles();
    }

    clearFilters() {
        this.filters = {};
        this.searchTerm = '';
        this.currentPage = 1;
        
        // Reset form elements
        document.getElementById('search').value = '';
        document.getElementById('model-filter').value = '';
        document.getElementById('year-filter').value = '';
        document.getElementById('trim-filter').value = '';
        document.getElementById('body-style-filter').value = '';
        document.getElementById('min-price').value = '';
        document.getElementById('max-price').value = '';
        
        this.loadVehicles();
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadVehicles();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Initialize the app
const app = new VehicleInventory();