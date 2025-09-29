class VehicleInventory {
    constructor() {
        this.currentPage = 1;
        this.filters = {};
        this.searchTerm = '';
        this.inventoryType = 'new'; // Default to new vehicles
        this.viewMode = 'card'; // Default to card view
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.currentVehicles = [];
        this.tableClipboardSetup = false;
        this.init();
    }

    async init() {
        await this.loadFilters();
        await this.loadVehicles();
        this.setupEventListeners();
        this.loadInventoryStatus();
    }

    async loadFilters() {
        try {
            const response = await fetch(`/api/filters?inventory_type=${this.inventoryType}`);
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
                per_page: this.viewMode === 'list' ? 100 : 12,
                inventory_type: this.inventoryType,
                ...this.filters
            });

            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }

            const response = await fetch(`/api/vehicles?${params}`);
            const data = await response.json();
            
            this.currentVehicles = data.vehicles;
            
            if (this.viewMode === 'card') {
                this.renderVehicles(data.vehicles);
            } else {
                this.renderTable(data.vehicles);
            }
            
            this.renderPagination(data);
            this.updateResultsCount(data.total);
        } catch (error) {
            console.error('Error loading vehicles:', error);
            const errorMsg = '<p>Error loading vehicles. Please try again.</p>';
            if (this.viewMode === 'card') {
                document.getElementById('vehicles-grid').innerHTML = errorMsg;
            } else {
                document.getElementById('table-body').innerHTML = `<tr><td colspan="100" style="text-align: center; padding: 40px;">${errorMsg}</td></tr>`;
            }
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
                        <img ${index === 0 ? `src="${photo}"` : `data-src="${photo}"`} alt="${vehicle.year} ${vehicle.make} ${vehicle.model}" 
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
                    <div class="vehicle-title">
                    ${vehicle.vehicle_link ? `<a href="${vehicle.vehicle_link}" target="_blank" rel="noopener noreferrer">${vehicle.year} ${vehicle.make} ${vehicle.model} ${vehicle.trim}</a>` : `${vehicle.year} ${vehicle.make} ${vehicle.model} ${vehicle.trim}`}
                </div>
                    <div class="price-row">
                        <div class="vehicle-price">${vehicle.msrp}</div>
                        ${vehicle.inventory_type === 'used' && vehicle.carfax_url ? `
                        <a href="${vehicle.carfax_url}" target="_blank" rel="noopener noreferrer" class="carfax-btn-inline">CARFAX</a>
                        ` : ''}
                        ${vehicle.inventory_type === 'new' ? `
                        <a href="https://fordvisions.dealerconnection.com/vinv/GetInvoice.aspx?v=${vehicle.vin}" target="_blank" rel="noopener noreferrer" class="invoice-btn">INVOICE</a>
                        <a href="https://www.windowsticker.forddirect.com/windowsticker.pdf?vin=${vehicle.vin}" target="_blank" rel="noopener noreferrer" class="window-sticker-btn">STICKER</a>
                        ` : ''}
                    </div>
                    
                    <div class="vehicle-details">
                        <div class="detail-row">
                            <span class="detail-label">VIN:</span>
                            <span class="detail-value clickable-value" data-copy="${vehicle.vin}" title="Click to copy">${vehicle.vin}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">STOCK:</span>
                            <span class="detail-value clickable-value" data-copy="${vehicle.stock_number}" title="Click to copy">${vehicle.stock_number}</span>
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
        
        // Setup clipboard copy functionality - add event delegation to handle dynamically created elements
        this.setupClipboardCopyDelegation();
    }

    async loadInventoryStatus() {
        try {
            const response = await fetch('/api/inventory-status');
            const status = await response.json();
            const statusEl = document.getElementById('inventory-status');
            
            if (this.inventoryType === 'new') {
                statusEl.textContent = `New: ${status.new_count} vehicles • Updated: ${status.new_updated}`;
            } else {
                statusEl.textContent = `Used: ${status.used_count} vehicles • Updated: ${status.used_updated}`;
            }
        } catch (error) {
            console.error('Error loading inventory status:', error);
        }
    }

    setupCarousels() {
        document.querySelectorAll('.photo-carousel').forEach(carousel => {
            let currentIndex = 0;
            const images = carousel.querySelectorAll('img');
            const indicators = carousel.querySelectorAll('.indicator');

            const showPhoto = (index) => {
                // Lazy load the image if it hasn't been loaded yet
                const targetImg = images[index];
                if (targetImg && targetImg.hasAttribute('data-src')) {
                    targetImg.src = targetImg.getAttribute('data-src');
                    targetImg.removeAttribute('data-src');
                }
                
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
        document.getElementById('sort-select').addEventListener('change', (e) => this.updateFilter('sort', e.target.value));

        // Clear filters
        document.getElementById('clear-filters').addEventListener('click', () => this.clearFilters());

        // Inventory type toggle
        document.getElementById('toggle-new').addEventListener('click', () => this.switchInventoryType('new'));
        document.getElementById('toggle-used').addEventListener('click', () => this.switchInventoryType('used'));
        
        // View mode toggle
        document.getElementById('toggle-card').addEventListener('click', () => this.switchViewMode('card'));
        document.getElementById('toggle-list').addEventListener('click', () => this.switchViewMode('list'));
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

    switchInventoryType(type) {
        if (this.inventoryType === type) return;
        
        this.inventoryType = type;
        this.currentPage = 1;
        
        // Update toggle button states
        document.getElementById('toggle-new').classList.toggle('active', type === 'new');
        document.getElementById('toggle-used').classList.toggle('active', type === 'used');
        
        // Clear all filters and search when switching
        this.clearFilters();
        
        // Clear filter dropdown options before reloading
        this.clearFilterOptions();
        
        // Reload filters and vehicles for new inventory type
        this.loadFilters();
        this.loadVehicles();
        this.loadInventoryStatus();
    }

    clearFilterOptions() {
        // Clear all dropdown options except the first "All X" option
        const selects = ['model-filter', 'year-filter', 'trim-filter', 'body-style-filter'];
        selects.forEach(selectId => {
            const select = document.getElementById(selectId);
            // Keep only the first option (the "All X" option)
            while (select.children.length > 1) {
                select.removeChild(select.lastChild);
            }
        });
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
        document.getElementById('sort-select').value = '';
        
        this.loadVehicles();
    }

    setupClipboardCopyDelegation() {
        // Use event delegation on the vehicles grid container to handle dynamically created elements
        const vehiclesGrid = document.getElementById('vehicles-grid');
        
        vehiclesGrid.addEventListener('click', async (e) => {
            // Check if the clicked element has the clickable-value class
            if (e.target.classList.contains('clickable-value')) {
                const textToCopy = e.target.getAttribute('data-copy');
                const originalText = e.target.textContent;
                
                if (!textToCopy) return;
                
                try {
                    // Try modern clipboard API first (requires HTTPS)
                    if (navigator.clipboard && window.isSecureContext) {
                        await navigator.clipboard.writeText(textToCopy);
                    } else {
                        // Fallback for HTTP/older browsers using deprecated execCommand
                        const textArea = document.createElement('textarea');
                        textArea.value = textToCopy;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        const successful = document.execCommand('copy');
                        document.body.removeChild(textArea);
                        
                        if (!successful) {
                            throw new Error('execCommand copy failed');
                        }
                    }
                    
                    // Show "COPIED" feedback
                    e.target.textContent = 'COPIED';
                    e.target.style.color = '#00cc66';
                    e.target.style.fontWeight = '600';
                    
                    // Reset after 1.5 seconds
                    setTimeout(() => {
                        e.target.textContent = originalText;
                        e.target.style.color = '';
                        e.target.style.fontWeight = '';
                    }, 1500);
                    
                } catch (err) {
                    // Show error feedback
                    e.target.textContent = 'COPY FAILED';
                    e.target.style.color = '#ff6666';
                    setTimeout(() => {
                        e.target.textContent = originalText;
                        e.target.style.color = '';
                    }, 1500);
                }
            }
        });
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadVehicles();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    switchViewMode(mode) {
        if (this.viewMode === mode) return;
        
        this.viewMode = mode;
        this.currentPage = 1;
        
        // Update toggle button states
        document.getElementById('toggle-card').classList.toggle('active', mode === 'card');
        document.getElementById('toggle-list').classList.toggle('active', mode === 'list');
        
        // Show/hide appropriate container
        document.getElementById('vehicles-grid').style.display = mode === 'card' ? 'grid' : 'none';
        document.getElementById('vehicles-table-container').style.display = mode === 'list' ? 'block' : 'none';
        
        // Reload vehicles
        this.loadVehicles();
    }

    renderTable(vehicles) {
        const tableContainer = document.getElementById('vehicles-table-container');
        const tableHeader = document.getElementById('table-header');
        const tableBody = document.getElementById('table-body');
        
        if (vehicles.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="100" style="text-align: center; padding: 40px; color: #666;">NO VEHICLES FOUND</td></tr>';
            return;
        }

        // Define columns to display
        const columns = [
            { key: 'year', label: 'YEAR', sortable: true },
            { key: 'make', label: 'MAKE', sortable: true },
            { key: 'model', label: 'MODEL', sortable: true },
            { key: 'trim', label: 'TRIM', sortable: true },
            { key: 'msrp', label: 'PRICE', sortable: true },
            { key: 'vin', label: 'VIN', sortable: true },
            { key: 'stock_number', label: 'STOCK', sortable: true },
            { key: 'exterior_color', label: 'EXTERIOR', sortable: true },
            { key: 'interior_color', label: 'INTERIOR', sortable: true },
            { key: 'engine', label: 'ENGINE', sortable: true },
            { key: 'transmission', label: 'TRANSMISSION', sortable: true },
            { key: 'body_style', label: 'BODY', sortable: true },
            { key: 'fuel_economy', label: 'MPG', sortable: true }
        ];

        // Render header
        tableHeader.innerHTML = columns.map(col => {
            if (col.sortable) {
                const isSorted = this.sortColumn === col.key;
                const direction = isSorted ? this.sortDirection : '';
                const arrow = direction === 'asc' ? ' ▲' : direction === 'desc' ? ' ▼' : '';
                return `<th class="sortable" onclick="app.sortTable('${col.key}')">${col.label}${arrow}</th>`;
            }
            return `<th>${col.label}</th>`;
        }).join('');

        // Render rows
        tableBody.innerHTML = vehicles.map(vehicle => {
            return `<tr>
                <td>${vehicle.year || ''}</td>
                <td>${vehicle.make || ''}</td>
                <td>${vehicle.model || ''}</td>
                <td>${vehicle.trim || ''}</td>
                <td class="price-cell">${vehicle.msrp || ''}</td>
                <td class="clickable-cell" data-copy="${vehicle.vin || ''}" title="Click to copy">${vehicle.vin || ''}</td>
                <td class="clickable-cell" data-copy="${vehicle.stock_number || ''}" title="Click to copy">${vehicle.stock_number || ''}</td>
                <td>${vehicle.exterior_color || ''}</td>
                <td>${vehicle.interior_color || ''}</td>
                <td>${vehicle.engine || ''}</td>
                <td>${vehicle.transmission || ''}</td>
                <td>${vehicle.body_style || ''}</td>
                <td>${vehicle.fuel_economy || ''}</td>
            </tr>`;
        }).join('');

        // Setup clipboard copy for table cells (only once)
        if (!this.tableClipboardSetup) {
            this.setupTableClipboard();
            this.tableClipboardSetup = true;
        }
    }

    sortTable(column) {
        // Toggle sort direction if clicking same column
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }

        // Sort the current vehicles array
        this.currentVehicles.sort((a, b) => {
            let aVal = a[column] || '';
            let bVal = b[column] || '';

            // Handle price sorting (remove $ and commas)
            if (column === 'msrp') {
                aVal = parseFloat(aVal.toString().replace(/[$,]/g, '')) || 0;
                bVal = parseFloat(bVal.toString().replace(/[$,]/g, '')) || 0;
            }
            // Handle year sorting
            else if (column === 'year') {
                aVal = parseInt(aVal) || 0;
                bVal = parseInt(bVal) || 0;
            }
            // String comparison
            else {
                aVal = aVal.toString().toLowerCase();
                bVal = bVal.toString().toLowerCase();
            }

            if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
            if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        // Re-render the table
        this.renderTable(this.currentVehicles);
    }

    setupTableClipboard() {
        const tableBody = document.getElementById('table-body');
        
        tableBody.addEventListener('click', async (e) => {
            if (e.target.classList.contains('clickable-cell')) {
                const textToCopy = e.target.getAttribute('data-copy');
                const originalText = e.target.textContent;
                
                if (!textToCopy) return;
                
                try {
                    if (navigator.clipboard && window.isSecureContext) {
                        await navigator.clipboard.writeText(textToCopy);
                    } else {
                        const textArea = document.createElement('textarea');
                        textArea.value = textToCopy;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textArea);
                    }
                    
                    e.target.textContent = 'COPIED';
                    e.target.style.color = '#00cc66';
                    
                    setTimeout(() => {
                        e.target.textContent = originalText;
                        e.target.style.color = '';
                    }, 1500);
                    
                } catch (err) {
                    e.target.textContent = 'COPY FAILED';
                    e.target.style.color = '#ff6666';
                    setTimeout(() => {
                        e.target.textContent = originalText;
                        e.target.style.color = '';
                    }, 1500);
                }
            }
        });
    }
}

// Initialize the app
const app = new VehicleInventory();