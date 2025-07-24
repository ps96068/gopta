// dashboard/static/js/dashboard.js

// Dashboard Utilities
const Dashboard = {
    // API Base URL
    apiBase: '/dashboard/api',

    // Show loading spinner
    showLoading() {
        const spinner = document.createElement('div');
        spinner.className = 'spinner-wrapper';
        spinner.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        document.body.appendChild(spinner);
    },

    // Hide loading spinner
    hideLoading() {
        const spinner = document.querySelector('.spinner-wrapper');
        if (spinner) spinner.remove();
    },

    // Show toast notification
    showToast(message, type = 'success') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toast = new bootstrap.Toast(toastContainer.lastElementChild);
        toast.show();
    },

    // Format date
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('ro-RO', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Format currency
    formatCurrency(amount, currency = 'MDL') {
        return new Intl.NumberFormat('ro-MD', {
            style: 'currency',
            currency: currency
        }).format(amount);
    },

    // Confirm dialog
    async confirm(message, title = 'Confirmare') {
        return new Promise(resolve => {
            const modal = document.createElement('div');
            modal.innerHTML = `
                <div class="modal fade" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">${title}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>${message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anulează</button>
                                <button type="button" class="btn btn-primary" id="confirmBtn">Confirmă</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);
            const modalBS = new bootstrap.Modal(modal.firstElementChild);

            modal.querySelector('#confirmBtn').addEventListener('click', () => {
                modalBS.hide();
                resolve(true);
            });

            modal.firstElementChild.addEventListener('hidden.bs.modal', () => {
                modal.remove();
                resolve(false);
            });

            modalBS.show();
        });
    },

    // AJAX request wrapper
    async fetch(url, options = {}) {
        const defaultOptions = {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const response = await fetch(url, { ...defaultOptions, ...options });

        if (response.status === 401) {
            window.location.href = '/dashboard/auth/login';
            return;
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Eroare necunoscută' }));
            throw new Error(error.detail || 'Eroare server');
        }

        return response;
    },

    // Delete item
    async deleteItem(url, itemName = 'element') {
        const confirmed = await this.confirm(`Sigur doriți să ștergeți acest ${itemName}?`, 'Confirmare ștergere');

        if (!confirmed) return false;

        this.showLoading();

        try {
            await this.fetch(url, { method: 'DELETE' });
            this.showToast(`${itemName} șters cu succes`, 'success');
            return true;
        } catch (error) {
            this.showToast(error.message, 'danger');
            return false;
        } finally {
            this.hideLoading();
        }
    },

    // Handle form submission
    async submitForm(form, options = {}) {
        const formData = new FormData(form);

        this.showLoading();

        try {
            const response = await this.fetch(form.action, {
                method: form.method || 'POST',
                body: formData
            });

            const result = await response.json();

            if (options.onSuccess) {
                options.onSuccess(result);
            } else {
                this.showToast('Salvat cu succes', 'success');
                if (options.redirect) {
                    setTimeout(() => {
                        window.location.href = options.redirect;
                    }, 1000);
                }
            }

            return result;
        } catch (error) {
            this.showToast(error.message, 'danger');
            if (options.onError) options.onError(error);
            throw error;
        } finally {
            this.hideLoading();
        }
    }
};

// File Upload Handler
class FileUploadHandler {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            maxSize: 2 * 1024 * 1024, // 2MB
            allowedTypes: ['image/jpeg', 'image/jpg', 'image/png'],
            multiple: false,
            preview: true,
            ...options
        };

        this.init();
    }

    init() {
        this.element.addEventListener('dragover', this.handleDragOver.bind(this));
        this.element.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.element.addEventListener('drop', this.handleDrop.bind(this));
        this.element.addEventListener('click', this.handleClick.bind(this));

        // Hidden file input
        this.fileInput = document.createElement('input');
        this.fileInput.type = 'file';
        this.fileInput.multiple = this.options.multiple;
        this.fileInput.accept = this.options.allowedTypes.join(',');
        this.fileInput.style.display = 'none';
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        document.body.appendChild(this.fileInput);
    }

    handleDragOver(e) {
        e.preventDefault();
        this.element.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.preventDefault();
        this.element.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        this.element.classList.remove('dragover');
        this.handleFiles(e.dataTransfer.files);
    }

    handleClick() {
        this.fileInput.click();
    }

    handleFileSelect(e) {
        this.handleFiles(e.target.files);
    }

    handleFiles(files) {
        for (const file of files) {
            if (!this.validateFile(file)) continue;

            if (this.options.preview) {
                this.showPreview(file);
            }

            if (this.options.onSelect) {
                this.options.onSelect(file);
            }
        }
    }

    validateFile(file) {
        if (!this.options.allowedTypes.includes(file.type)) {
            Dashboard.showToast(`Tip fișier nepermis: ${file.type}`, 'danger');
            return false;
        }

        if (file.size > this.options.maxSize) {
            Dashboard.showToast(`Fișier prea mare: ${(file.size / 1024 / 1024).toFixed(2)}MB`, 'danger');
            return false;
        }

        return true;
    }

    showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.createElement('div');
            preview.className = 'image-preview m-2';
            preview.innerHTML = `
                <img src="${e.target.result}" alt="${file.name}" class="img-thumbnail">
                <button type="button" class="remove-image">
                    <i class="bi bi-x"></i>
                </button>
            `;

            preview.querySelector('.remove-image').addEventListener('click', () => {
                preview.remove();
                if (this.options.onRemove) this.options.onRemove(file);
            });

            const previewContainer = this.element.parentElement.querySelector('.preview-container') ||
                                   (() => {
                                       const container = document.createElement('div');
                                       container.className = 'preview-container d-flex flex-wrap mt-3';
                                       this.element.parentElement.appendChild(container);
                                       return container;
                                   })();

            previewContainer.appendChild(preview);
        };
        reader.readAsDataURL(file);
    }
}

// Data Table Handler
class DataTableHandler {
    constructor(tableId, options = {}) {
        this.table = document.getElementById(tableId);
        this.options = {
            sortable: true,
            searchable: true,
            paginate: true,
            perPage: 20,
            ...options
        };

        this.init();
    }

    init() {
        if (this.options.searchable) {
            this.initSearch();
        }

        if (this.options.sortable) {
            this.initSort();
        }

        if (this.options.paginate) {
            this.initPagination();
        }
    }

    initSearch() {
        const searchInput = document.createElement('input');
        searchInput.type = 'search';
        searchInput.className = 'form-control mb-3';
        searchInput.placeholder = 'Caută...';

        searchInput.addEventListener('input', (e) => {
            this.search(e.target.value);
        });

        this.table.parentElement.insertBefore(searchInput, this.table);
    }

    initSort() {
        const headers = this.table.querySelectorAll('th[data-sortable]');

        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sort(header.dataset.field);
            });
        });
    }

    search(query) {
        const rows = this.table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query.toLowerCase()) ? '' : 'none';
        });
    }

    sort(field) {
        // Implementation depends on data source
        console.log('Sorting by:', field);
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => new bootstrap.Tooltip(tooltip));

    // Initialize file uploads
    const uploadAreas = document.querySelectorAll('.upload-area');
    uploadAreas.forEach(area => new FileUploadHandler(area));

    // Initialize data tables
    const dataTables = document.querySelectorAll('[data-table]');
    dataTables.forEach(table => new DataTableHandler(table.id));
});

// Export for use in other scripts
window.Dashboard = Dashboard;