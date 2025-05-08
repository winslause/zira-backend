console.log('script1.js loaded successfully');

        // Initialize Charts
let salesChart, usersChart;

function initializeCharts(salesData, usersData) {
    console.log('Initializing charts with salesData:', salesData, 'usersData:', usersData);
    const salesCtx = document.getElementById('sales-chart').getContext('2d');
    const usersCtx = document.getElementById('users-chart').getContext('2d');

    // Destroy existing charts if they exist
    if (salesChart) salesChart.destroy();
    if (usersChart) usersChart.destroy();

    salesChart = new Chart(salesCtx, {
        type: 'line',
        data: {
            labels: salesData.map(d => d.month),
            datasets: [{
                label: 'Sales (KSh)',
                data: salesData.map(d => d.total),
                borderColor: '#d97706',
                fill: false
            }]
        },
        options: { responsive: true }
    });

    usersChart = new Chart(usersCtx, {
        type: 'bar',
        data: {
            labels: usersData.map(d => d.month),
            datasets: [{
                label: 'New Users',
                data: usersData.map(d => d.count),
                backgroundColor: '#d97706'
            }]
        },
        options: { responsive: true }
    });
}
console.log('script1.js loaded successfully');
// Fetch Dashboard Stats
async function fetchDashboardStats() {
    console.log('Fetching dashboard stats...');
    try {
        const response = await fetch('/api/dashboard_stats', { credentials: 'include' });
        console.log('Dashboard stats response:', response.status, response.headers.get('content-type'), response.url);
        if (response.redirected && response.url.includes('/login')) {
            showToast('Session expired. Please log in.', 'error');
            window.location.href = '/login';
            return;
        }
        if (!response.ok) {
            console.error('Dashboard stats fetch failed:', response.status, response.statusText);
            throw new Error('Failed to fetch dashboard stats');
        }
        const data = await response.json();
        console.log('Dashboard stats data:', data);
        document.getElementById('total-sales').textContent = `KSh ${data.total_sales.toFixed(2)}`;
        document.getElementById('new-users').textContent = data.new_users;
        document.getElementById('pending-orders').textContent = data.pending_orders;
        document.getElementById('top-product').textContent = data.top_product || 'N/A';
        initializeCharts(data.sales_data || [], data.users_data || []);
    } catch (error) {
        console.error('Error in fetchDashboardStats:', error);
        showToast(`Dashboard stats failed to load: ${error.message}`, 'error');
        // Fallback data to prevent frozen UI
        document.getElementById('total-sales').textContent = 'KSh 0.00';
        document.getElementById('new-users').textContent = '0';
        document.getElementById('pending-orders').textContent = '0';
        document.getElementById('top-product').textContent = 'N/A';
        initializeCharts([], []);
    }
}

// Navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        console.log('Navigating to section:', link.dataset.section);
        const section = link.dataset.section;
        document.querySelectorAll('.section').forEach(s => s.classList.add('hidden'));
        document.getElementById(section).classList.remove('hidden');
        document.getElementById('section-title').textContent = section.charAt(0).toUpperCase() + section.slice(1);
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('bg-yellow-600'));
        link.classList.add('bg-yellow-600');
        if (window.innerWidth < 768) {
            document.querySelector('.sidebar').classList.add('sidebar-hidden');
        }
    });
});
console.log('script1.js loaded successfully');
// Sidebar Toggle
document.getElementById('toggle-sidebar').addEventListener('click', () => {
    console.log('Toggling sidebar');
    document.querySelector('.sidebar').classList.toggle('sidebar-hidden');
});

// Modal Functions
function openModal(modalId) {
    console.log('Opening modal:', modalId);
    const modal = document.getElementById(modalId);
    modal.classList.remove('hidden');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    if (modalId === 'product-modal') {
        populateProductCategories();
    } else if (modalId === 'discount-modal') {
        populateDiscountProducts();
    }
}

function closeModal(modalId) {
    console.log('Closing modal:', modalId);
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
    resetForm(modalId);
}

function resetForm(modalId) {
    console.log('Resetting form for modal:', modalId);
    const form = document.getElementById(modalId.replace('modal', 'form'));
    if (form) {
        form.reset();
        form.querySelector('input[type="hidden"]')?.value = '';
        const preview = document.getElementById(`${modalId.replace('modal', 'image')}-preview`);
        if (preview) {
            preview.classList.add('hidden');
            preview.src = '';
        }
        document.getElementById(modalId + '-title').textContent = `Add ${modalId.split('-')[0].charAt(0).toUpperCase() + modalId.split('-')[0].slice(1)}`;
    }
}

// Close Modal on Outside Click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', e => {
        if (e.target === modal) {
            console.log('Closing modal via outside click:', modal.id);
            closeModal(modal.id);
        }
    });
});

// Toast Notifications
function showToast(message, type = 'success') {
    console.log(`Showing toast: ${message} (${type})`);
    Toastify({
        text: message,
        duration: 3000,
        style: {
            background: type === 'success' ? '#d97706' : type === 'info' ? '#3b82f6' : '#dc2626'
        }
    }).showToast();
}

// Confirmation Dialog
function showConfirm(message, callback) {
    console.log('Showing confirm dialog:', message);
    const confirmModal = document.createElement('div');
    confirmModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    confirmModal.innerHTML = `
        <div class="bg-white p-6 rounded-lg shadow-lg max-w-sm w-full">
            <p class="mb-4">${message}</p>
            <div class="flex justify-end space-x-2">
                <button id="confirm-cancel" class="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400">Cancel</button>
                <button id="confirm-ok" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">Confirm</button>
            </div>
        </div>
    `;
    document.body.appendChild(confirmModal);

    document.getElementById('confirm-ok').addEventListener('click', () => {
        console.log('Confirm dialog: Confirmed');
        document.body.removeChild(confirmModal);
        callback(true);
    });
    document.getElementById('confirm-cancel').addEventListener('click', () => {
        console.log('Confirm dialog: Canceled');
        document.body.removeChild(confirmModal);
        callback(false);
    });
}

// Image Validation and Preview
function validateAndPreviewImage(input, previewId) {
    console.log('Validating image for preview:', previewId);
    const file = input.files[0];
    const preview = document.getElementById(previewId);
    if (file) {
        if (!['image/jpeg', 'image/png'].includes(file.type)) {
            showToast('Only JPG and PNG images are allowed', 'error');
            input.value = '';
            preview.classList.add('hidden');
            return false;
        }
        if (file.size > 3 * 1024 * 1024) {
            showToast('Image size must be less than 3MB', 'error');
            input.value = '';
            preview.classList.add('hidden');
            return false;
        }
        const reader = new FileReader();
        reader.onload = e => {
            preview.src = e.target.result;
            preview.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
        return true;
    }
    preview.classList.add('hidden');
    return false;
}

document.getElementById('product-image')?.addEventListener('change', e => {
    console.log('Product image changed');
    validateAndPreviewImage(e.target, 'product-image-preview');
});

document.getElementById('admin-story-image')?.addEventListener('change', e => {
    console.log('Story image changed');
    validateAndPreviewImage(e.target, 'admin-story-image-preview');
});

// Fetch Data
async function fetchData(endpoint) {
    console.log(`Fetching /api/${endpoint}`);
    try {
        const response = await fetch(`/api/${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        console.log(`Response for /api/${endpoint}:`, response.status, response.headers.get('content-type'), response.url);
        if (response.redirected && response.url.includes('/login')) {
            showToast('Session expired. Please log in.', 'error');
            window.location.href = '/login';
            return null;
        }
        const contentType = response.headers.get('content-type');
        if (!response.ok) {
            if (response.status === 401) {
                showToast('Unauthorized. Please log in.', 'error');
                window.location.href = '/login';
                return null;
            }
            if (response.status === 500) {
                showToast('Server error. Please try again later.', 'error');
                return [];
            }
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                console.error(`Error data for /api/${endpoint}:`, errorData);
                throw new Error(errorData.error || `Failed to fetch ${endpoint}`);
            } else {
                const text = await response.text();
                console.error(`Non-JSON response for /api/${endpoint}:`, text.slice(0, 100));
                throw new Error(`Unexpected response from ${endpoint}`);
            }
        }
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error(`Non-JSON response for /api/${endpoint}:`, text.slice(0, 100));
            throw new Error(`Unexpected response from ${endpoint}`);
        }
        const data = await response.json();
        console.log(`Data for /api/${endpoint}:`, data);
        return data;
    } catch (error) {
        console.error(`Error fetching /api/${endpoint}:`, error);
        showToast(`Failed to load ${endpoint}: ${error.message}`, 'error');
        return [];
    }
}

// Global Error Handler
window.onerror = function(message, source, lineno, colno, error) {
    console.error(`Global error: ${message} at ${source}:${lineno}:${colno}`, error);
    showToast('An unexpected error occurred. Please try again.', 'error');
};

// Populate Tables
async function populateUsers(data) {
    console.log('Populating users table');
    try {
        const users = data || await fetchData('users');
        const tbody = document.getElementById('users-table');
        tbody.innerHTML = users.length ? users.map(user => `
            <tr>
                <td>${user.id}</td>
                <td>${user.name}</td>
                <td>${user.email}</td>
                <td>${user.phone_number || 'N/A'}</td>
                <td>${user.role}</td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editUser(${user.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteUser(${user.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="6">No users found</td></tr>';
    } catch (error) {
        console.error('Error in populateUsers:', error);
        showToast(error.message, 'error');
    }
}

async function populateProducts(data) {
    console.log('Populating products table');
    try {
        const products = data || await fetchData('discounted_artefacts');
        const tbody = document.getElementById('products-table');
        tbody.innerHTML = products.length ? products.map(product => `
            <tr>
                <td>${product.id}</td>
                <td>${product.name}</td>
                <td>${product.category}</td>
                <td>KSh ${product.price.toFixed(2)}</td>
                <td>${product.discount ? product.discount + '%' : 'None'}</td>
                <td>${product.image ? `<img src="/static/uploads/${product.image}" alt="${product.name}" class="image-preview" onerror="this.src='/static/placeholder.jpg'">` : 'No Image'}</td>
                <td>${product.description || 'N/A'}</td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editProduct(${product.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteProduct(${product.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="8">No products found</td></tr>';
    } catch (error) {
        console.error('Error in populateProducts:', error);
        showToast(error.message, 'error');
    }
}

async function populateOrders(data) {
    console.log('Populating orders table');
    try {
        const orders = data || await fetchData('orders');
        const tbody = document.getElementById('orders-table');
        tbody.innerHTML = orders.length ? orders.map(order => `
            <tr>
                <td>${order.id}</td>
                <td>${order.customer}</td>
                <td>${order.customer_number || 'N/A'}</td>
                <td>${order.location || 'N/A'}</td>
                <td>KSh ${order.total.toFixed(2)}</td>
                <td>
                    <select onchange="updateOrderStatus('${order.id}', this.value)">
                        <option value="Pending" ${order.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Shipped" ${order.status === 'Shipped' ? 'selected' : ''}>Shipped</option>
                        <option value="Delivered" ${order.status === 'Delivered' ? 'selected' : ''}>Delivered</option>
                        <option value="Canceled" ${order.status === 'Canceled' ? 'selected' : ''}>Canceled</option>
                    </select>
                </td>
                <td>${order.payment_method}</td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="viewOrder('${order.id}')"><i class="fas fa-eye"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteOrder('${order.id}')"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="8">No orders found</td></tr>';
    } catch (error) {
        console.error('Error in populateOrders:', error);
        showToast(error.message, 'error');
    }
}

async function updateOrderStatus(orderId, status) {
    console.log(`Updating order ${orderId} status to ${status}`);
    try {
        const response = await fetch(`/api/orders/${orderId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
            credentials: 'include'
        });
        console.log('Update order status response:', response.status, response.url);
        if (response.redirected && response.url.includes('/login')) {
            showToast('Session expired. Please log in.', 'error');
            window.location.href = '/login';
            return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Update failed');
        showToast('Order status updated');
        await populateOrders();
        await fetchDashboardStats();
    } catch (error) {
        console.error('Error in updateOrderStatus:', error);
        showToast(error.message, 'error');
    }
}

async function deleteOrder(orderId) {
    console.log(`Deleting order ${orderId}`);
    showConfirm('Are you sure you want to delete this order?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/orders/${orderId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include'
            });
            console.log('Delete order response:', response.status, response.url);
            if (response.redirected && response.url.includes('/login')) {
                showToast('Session expired. Please log in.', 'error');
                window.location.href = '/login';
                return;
            }
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Order deleted successfully');
            await populateOrders();
            await fetchDashboardStats();
        } catch (error) {
            console.error('Error in deleteOrder:', error);
            showToast(error.message, 'error');
        }
    });
}

async function populateCategories(data) {
    console.log('Populating categories table');
    try {
        const categories = data || await fetchData('categories');
        const tbody = document.getElementById('categories-table');
        tbody.innerHTML = categories.length ? categories.map(category => `
            <tr>
                <td>${category.id}</td>
                <td>${category.name}</td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editCategory(${category.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteCategory(${category.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="3">No categories found</td></tr>';
    } catch (error) {
        console.error('Error in populateCategories:', error);
        showToast(error.message, 'error');
    }
}

async function populateDiscounts(data) {
    console.log('Populating discounts table');
    try {
        const discounts = data || await fetchData('discounts');
        const tbody = document.getElementById('discounts-table');
        tbody.innerHTML = discounts.length ? discounts.map(discount => `
            <tr>
                <td>${discount.id}</td>
                <td>${discount.productName}</td>
                <td>${discount.percent}%</td>
                <td>${discount.startDate}</td>
                <td>${discount.endDate}</td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editDiscount(${discount.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteDiscount(${discount.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="6">No discounts found</td></tr>';
    } catch (error) {
        console.error('Error in populateDiscounts:', error);
        showToast(error.message, 'error');
    }
}

async function populateArtisans(data) {
    console.log('Populating artisans table');
    try {
        const artisans = data || await fetchData('artisans');
        const tbody = document.getElementById('artisans-table');
        tbody.innerHTML = artisans.length ? artisans.map(artisan => `
            <tr>
                <td>${artisan.id}</td>
                <td>${artisan.name}</td>
                <td>${artisan.email}</td>
                <td>${artisan.phone_number || 'N/A'}</td>
                <td>
                    <select onchange="updateArtisanStatus(${artisan.id}, this.value)">
                        <option value="Approved" ${artisan.status === 'Approved' ? 'selected' : ''}>Approved</option>
                        <option value="Pending" ${artisan.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Suspended" ${artisan.status === 'Suspended' ? 'selected' : ''}>Suspended</option>
                    </select>
                </td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editArtisan(${artisan.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteArtisan(${artisan.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="6">No artisans found</td></tr>';
    } catch (error) {
        console.error('Error in populateArtisans:', error);
        showToast(error.message, 'error');
    }
}

async function populateStories(data) {
    console.log('Populating stories table');
    try {
        const stories = data || await fetchData('stories');
        const tbody = document.getElementById('stories-table');
        tbody.innerHTML = stories.length ? stories.map(story => `
            <tr>
                <td>${story.id}</td>
                <td>${story.title}</td>
                <td><img src="/static/uploads/${story.image}" alt="${story.title}" class="image-preview" onerror="this.src='/static/placeholder.jpg'"></td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="editStory(${story.id})"><i class="fas fa-edit"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteStory(${story.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="4">No stories found</td></tr>';
    } catch (error) {
        console.error('Error in populateStories:', error);
        showToast(error.message, 'error');
    }
}

async function populateReviews(data) {
    console.log('Populating reviews table');
    try {
        const reviews = data || await fetchData('reviews');
        const tbody = document.getElementById('reviews-table');
        tbody.innerHTML = reviews.length ? reviews.map(review => `
            <tr>
                <td>${review.id}</td>
                <td>${review.product}</td>
                <td>${review.customer}</td>
                <td>${review.rating} ★</td>
                <td>
                    <select onchange="updateReviewStatus(${review.id}, this.value)">
                        <option value="Approved" ${review.status === 'Approved' ? 'selected' : ''}>Approved</option>
                        <option value="Pending" ${review.status === 'Pending' ? 'selected' : ''}>Pending</option>
                        <option value="Rejected" ${review.status === 'Rejected' ? 'selected' : ''}>Rejected</option>
                    </select>
                </td>
                <td>
                    <button class="action-btn text-blue-600 hover:text-blue-800" onclick="viewReview(${review.id})"><i class="fas fa-eye"></i></button>
                    <button class="action-btn text-red-600 hover:text-red-800" onclick="deleteReview(${review.id})"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('') : '<tr><td colspan="6">No reviews found</td></tr>';
    } catch (error) {
        console.error('Error in populateReviews:', error);
        showToast(error.message, 'error');
    }
}

// Form Handlers
document.getElementById('user-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting user form');
    const id = document.getElementById('user-id').value;
    const user = {
        username: document.getElementById('user-username').value.trim(),
        name: document.getElementById('user-name').value.trim(),
        email: document.getElementById('user-email').value.trim(),
        phone_number: document.getElementById('user-phone').value.trim(),
        role: document.getElementById('user-role').value
    };
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/users/${id}` : '/api/users';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(user),
            credentials: 'include'
        });
        console.log('User form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'User updated successfully' : 'User added successfully');
        await populateUsers();
        closeModal('user-modal');
    } catch (error) {
        console.error('Error in user form submission:', error);
        showToast(error.message, 'error');
    }
});

document.getElementById('product-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting product form');
    const id = document.getElementById('product-id').value;
    const form = document.getElementById('product-form');
    const formData = new FormData(form);
    const imageInput = document.getElementById('product-image');
    if (!id && !imageInput.files[0]) {
        showToast('Image is required for new products', 'error');
        return;
    }
    if (imageInput.files[0] && !validateAndPreviewImage(imageInput, 'product-image-preview')) {
        return;
    }
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/discounted_artefacts/${id}` : '/api/discounted_artefacts';
        const response = await fetch(url, {
            method,
            body: formData,
            credentials: 'include'
        });
        console.log('Product form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'Product updated successfully' : 'Product added successfully');
        await populateProducts();
        closeModal('product-modal');
    } catch (error) {
        console.error('Error in product form submission:', error);
        showToast(error.message, 'error');
    }
});

document.getElementById('category-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting category form');
    const id = document.getElementById('category-id').value;
    const category = {
        name: document.getElementById('category-name').value.trim()
    };
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/categories/${id}` : '/api/categories';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(category),
            credentials: 'include'
        });
        console.log('Category form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'Category updated successfully' : 'Category added successfully');
        await populateCategories();
        closeModal('category-modal');
    } catch (error) {
        console.error('Error in category form submission:', error);
        showToast(error.message, 'error');
    }
});

document.getElementById('discount-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting discount form');
    const id = document.getElementById('discount-id').value;
    const productId = parseInt(document.getElementById('discount-product').value);
    const percent = parseInt(document.getElementById('discount-percent').value);
    const startDate = document.getElementById('discount-start').value;
    const endDate = document.getElementById('discount-end').value;

    // Client-side validation
    if (!productId) {
        showToast('Please select a product', 'error');
        return;
    }
    if (!percent || percent < 0 || percent > 100) {
        showToast('Discount percent must be between 0 and 100', 'error');
        return;
    }
    if (!startDate || !endDate) {
        showToast('Please provide start and end dates', 'error');
        return;
    }
    if (new Date(startDate) > new Date(endDate)) {
        showToast('End date must be after start date', 'error');
        return;
    }

    const discount = { productId, percent, startDate, endDate };
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/discounts/${id}` : '/api/discounts';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(discount),
            credentials: 'include'
        });
        console.log('Discount form response:', response.status, response.url);
        if (response.redirected && response.url.includes('/login')) {
            showToast('Session expired. Please log in.', 'error');
            window.location.href = '/login';
            return;
        }
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'Discount updated successfully' : 'Discount added successfully');
        await populateDiscounts();
        await populateProducts();
        closeModal('discount-modal');
    } catch (error) {
        console.error('Error in discount form submission:', error);
        showToast(error.message, 'error');
    }
});
console.log('script1.js loaded successfully');
document.getElementById('artisan-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting artisan form');
    const id = document.getElementById('artisan-id').value;
    const artisan = {
        name: document.getElementById('artisan-name').value.trim(),
        email: document.getElementById('artisan-email').value.trim(),
        phone_number: document.getElementById('artisan-phone').value.trim(),
        status: document.getElementById('artisan-status').value
    };
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/artisans/${id}` : '/api/artisans';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(artisan),
            credentials: 'include'
        });
        console.log('Artisan form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'Artisan updated successfully' : 'Artisan added successfully');
        await populateArtisans();
        closeModal('artisan-modal');
    } catch (error) {
        console.error('Error in artisan form submission:', error);
        showToast(error.message, 'error');
    }
});

document.getElementById('admin-story-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting story form');
    const id = document.getElementById('admin-story-id').value;
    const formData = new FormData();
    formData.append('title', document.getElementById('admin-story-title').value.trim());
    formData.append('content', document.getElementById('admin-story-content').value.trim());
    const imageInput = document.getElementById('admin-story-image');
    if (!id && !imageInput.files[0]) {
        showToast('Image is required for new stories', 'error');
        return;
    }
    if (imageInput.files[0] && !validateAndPreviewImage(imageInput, 'admin-story-image-preview')) {
        return;
    }
    if (imageInput.files[0]) formData.append('image', imageInput.files[0]);
    try {
        const method = id ? 'PUT' : 'POST';
        const url = id ? `/api/stories/${id}` : '/api/stories';
        const response = await fetch(url, { method, body: formData, credentials: 'include' });
        console.log('Story form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Operation failed');
        showToast(id ? 'Story updated successfully' : 'Story added successfully');
        await populateStories();
        closeModal('admin-story-modal');
    } catch (error) {
        console.error('Error in story form submission:', error);
        showToast(error.message, 'error');
    }
});

document.getElementById('password-form')?.addEventListener('submit', async e => {
    e.preventDefault();
    console.log('Submitting password form');
    const currentPassword = document.getElementById('current-password').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    if (newPassword !== confirmPassword) {
        showToast('New password and confirm password do not match', 'error');
        return;
    }
    try {
        const response = await fetch('/api/change_admin_password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
            credentials: 'include'
        });
        console.log('Password form response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Password change failed');
        showToast('Password updated successfully');
        document.getElementById('password-form').reset();
    } catch (error) {
        console.error('Error in password form submission:', error);
        showToast(error.message, 'error');
    }
});

// Edit/Delete Functions
async function editUser(id) {
    console.log(`Editing user ${id}`);
    try {
        const response = await fetch(`/api/users/${id}`, { credentials: 'include' });
        console.log('Edit user response:', response.status, response.url);
        const user = await response.json();
        if (!response.ok) throw new Error(user.error || 'Failed to fetch user');
        document.getElementById('user-id').value = user.id;
        document.getElementById('user-username').value = user.username;
        document.getElementById('user-name').value = user.name;
        document.getElementById('user-email').value = user.email;
        document.getElementById('user-phone').value = user.phone_number || '';
        document.getElementById('user-role').value = user.role;
        document.getElementById('user-modal-title').textContent = 'Edit User';
        openModal('user-modal');
    } catch (error) {
        console.error('Error in editUser:', error);
        showToast(error.message, 'error');
    }
}

async function deleteUser(id) {
    console.log(`Deleting user ${id}`);
    showConfirm('Are you sure you want to delete this user?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/users/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete user response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('User deleted successfully');
            await populateUsers();
        } catch (error) {
            console.error('Error in deleteUser:', error);
            showToast(error.message, 'error');
        }
    });
}

async function editProduct(id) {
    console.log(`Editing product ${id}`);
    try {
        const response = await fetch(`/api/discounted_artefacts/${id}`, { credentials: 'include' });
        console.log('Edit product response:', response.status, response.url);
        const product = await response.json();
        if (!response.ok) throw new Error(product.error || 'Failed to fetch product');
        document.getElementById('product-id').value = product.id;
        document.getElementById('product-name').value = product.name;
        document.getElementById('product-category').value = product.category;
        document.getElementById('product-price').value = product.price;
        document.getElementById('product-description').value = product.description || '';
        const preview = document.getElementById('product-image-preview');
        if (product.image) {
            preview.src = `/static/uploads/${product.image}`;
            preview.classList.remove('hidden');
        }
        document.getElementById('product-modal-title').textContent = 'Edit Product';
        openModal('product-modal');
    } catch (error) {
        console.error('Error in editProduct:', error);
        showToast(error.message, 'error');
    }
}

async function deleteProduct(id) {
    console.log(`Deleting product ${id}`);
    showConfirm('Are you sure you want to delete this product? This action cannot be undone.', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/discounted_artefacts/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete product response:', response.status, response.url);
            if (response.redirected && response.url.includes('/login')) {
                showToast('Session expired. Please log in.', 'error');
                window.location.href = '/login';
                return;
            }
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Product deleted successfully');
            await populateProducts();
            await populateDiscounts();
        } catch (error) {
            console.error('Error in deleteProduct:', error);
            showToast(error.message, 'error');
        }
    });
}

async function editCategory(id) {
    console.log(`Editing category ${id}`);
    try {
        const response = await fetch(`/api/categories/${id}`, { credentials: 'include' });
        console.log('Edit category response:', response.status, response.url);
        const category = await response.json();
        if (!response.ok) throw new Error(category.error || 'Failed to fetch category');
        document.getElementById('category-id').value = category.id;
        document.getElementById('category-name').value = category.name;
        document.getElementById('category-modal-title').textContent = 'Edit Category';
        openModal('category-modal');
    } catch (error) {
        console.error('Error in editCategory:', error);
        showToast(error.message, 'error');
    }
}

async function deleteCategory(id) {
    console.log(`Deleting category ${id}`);
    showConfirm('Are you sure you want to delete this category?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/categories/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete category response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Category deleted successfully');
            await populateCategories();
        } catch (error) {
            console.error('Error in deleteCategory:', error);
            showToast(error.message, 'error');
        }
    });
}

async function editDiscount(id) {
    console.log(`Editing discount ${id}`);
    try {
        const response = await fetch(`/api/discounts/${id}`, { credentials: 'include' });
        console.log('Edit discount response:', response.status, response.url);
        const discount = await response.json();
        if (!response.ok) throw new Error(discount.error || 'Failed to fetch discount');
        document.getElementById('discount-id').value = discount.id;
        document.getElementById('discount-product').value = discount.productId;
        document.getElementById('discount-percent').value = discount.percent;
        document.getElementById('discount-start').value = discount.startDate;
        document.getElementById('discount-end').value = discount.endDate;
        document.getElementById('discount-modal-title').textContent = 'Edit Discount';
        openModal('discount-modal');
    } catch (error) {
        console.error('Error in editDiscount:', error);
        showToast(error.message, 'error');
    }
}

async function deleteDiscount(id) {
    console.log(`Deleting discount ${id}`);
    showConfirm('Are you sure you want to delete this discount?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/discounts/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete discount response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Discount deleted successfully');
            await populateDiscounts();
            await populateProducts();
        } catch (error) {
            console.error('Error in deleteDiscount:', error);
            showToast(error.message, 'error');
        }
    });
}

async function editArtisan(id) {
    console.log(`Editing artisan ${id}`);
    try {
        const response = await fetch(`/api/artisans/${id}`, { credentials: 'include' });
        console.log('Edit artisan response:', response.status, response.url);
        const artisan = await response.json();
        if (!response.ok) throw new Error(artisan.error || 'Failed to fetch artisan');
        document.getElementById('artisan-id').value = artisan.id;
        document.getElementById('artisan-name').value = artisan.name;
        document.getElementById('artisan-email').value = artisan.email;
        document.getElementById('artisan-phone').value = artisan.phone_number || '';
        document.getElementById('artisan-status').value = artisan.status;
        document.getElementById('artisan-modal-title').textContent = 'Edit Artisan Seller';
        openModal('artisan-modal');
    } catch (error) {
        console.error('Error in editArtisan:', error);
        showToast(error.message, 'error');
    }
}

async function deleteArtisan(id) {
    console.log(`Deleting artisan ${id}`);
    showConfirm('Are you sure you want to delete this artisan?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/artisans/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete artisan response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Artisan deleted successfully');
            await populateArtisans();
        } catch (error) {
            console.error('Error in deleteArtisan:', error);
            showToast(error.message, 'error');
        }
    });
}

async function editStory(id) {
    console.log(`Editing story ${id}`);
    try {
        const response = await fetch(`/api/stories/${id}`, { credentials: 'include' });
        console.log('Edit story response:', response.status, response.url);
        const story = await response.json();
        if (!response.ok) throw new Error(story.error || 'Failed to fetch story');
        document.getElementById('admin-story-id').value = story.id;
        document.getElementById('admin-story-title').value = story.title;
        document.getElementById('admin-story-content').value = story.content;
        const preview = document.getElementById('admin-story-image-preview');
        if (story.image) {
            preview.src = `/static/uploads/${story.image}`;
            preview.classList.remove('hidden');
        }
        document.getElementById('admin-story-modal-title').textContent = 'Edit Story';
        openModal('admin-story-modal');
    } catch (error) {
        console.error('Error in editStory:', error);
        showToast(error.message, 'error');
    }
}

async function deleteStory(id) {
    console.log(`Deleting story ${id}`);
    showConfirm('Are you sure you want to delete this story?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/stories/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete story response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Story deleted successfully');
            await populateStories();
        } catch (error) {
            console.error('Error in deleteStory:', error);
            showToast(error.message, 'error');
        }
    });
}

async function viewOrder(orderId) {
    console.log(`Viewing order ${orderId}`);
    try {
        const response = await fetch(`/api/orders/${orderId}`, { credentials: 'include' });
        console.log('View order response:', response.status, response.url);
        const order = await response.json();
        if (!response.ok) throw new Error(order.error || 'Failed to fetch order');
        const orderDetails = `
            Order Details:
            ID: ${order.id}
            Customer: ${order.customer}
            Customer Number: ${order.customer_number || 'N/A'}
            Location: ${order.location || 'N/A'}
            Total: KSh ${order.total.toFixed(2)}
            Status: ${order.status}
            Payment Method: ${order.payment_method}
        `;
        showToast(orderDetails, 'info');
    } catch (error) {
        console.error('Error in viewOrder:', error);
        showToast(error.message, 'error');
    }
}

async function updateArtisanStatus(id, status) {
    console.log(`Updating artisan ${id} status to ${status}`);
    try {
        const response = await fetch(`/api/artisans/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
            credentials: 'include'
        });
        console.log('Update artisan status response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Update failed');
        showToast('Artisan status updated');
        await populateArtisans();
    } catch (error) {
        console.error('Error in updateArtisanStatus:', error);
        showToast(error.message, 'error');
    }
}

async function viewReview(id) {
    console.log(`Viewing review ${id}`);
    try {
        const response = await fetch(`/api/reviews/${id}`, { credentials: 'include' });
        console.log('View review response:', response.status, response.url);
        const review = await response.json();
        if (!response.ok) throw new Error(review.error || 'Failed to fetch review');
        const reviewDetails = `
            Review Details:
            ID: ${review.id}
            Product: ${review.product}
            Customer: ${review.customer}
            Rating: ${review.rating} ★
            Comment: ${review.comment || 'N/A'}
            Status: ${review.status}
        `;
        showToast(reviewDetails, 'info');
    } catch (error) {
        console.error('Error in viewReview:', error);
        showToast(error.message, 'error');
    }
}

async function updateReviewStatus(id, status) {
    console.log(`Updating review ${id} status to ${status}`);
    try {
        const response = await fetch(`/api/reviews/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status }),
            credentials: 'include'
        });
        console.log('Update review status response:', response.status, response.url);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Update failed');
        showToast('Review status updated');
        await populateReviews();
    } catch (error) {
        console.error('Error in updateReviewStatus:', error);
        showToast(error.message, 'error');
    }
}

async function deleteReview(id) {
    console.log(`Deleting review ${id}`);
    showConfirm('Are you sure you want to delete this review?', async (confirmed) => {
        if (!confirmed) return;
        try {
            const response = await fetch(`/api/reviews/${id}`, { method: 'DELETE', credentials: 'include' });
            console.log('Delete review response:', response.status, response.url);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Delete failed');
            showToast('Review deleted successfully');
            await populateReviews();
        } catch (error) {
            console.error('Error in deleteReview:', error);
            showToast(error.message, 'error');
        }
    });
}

// Global Search
document.getElementById('global-search')?.addEventListener('input', async e => {
    console.log('Global search triggered:', e.target.value);
    const query = e.target.value.toLowerCase();
    const currentSection = document.querySelector('.section:not(.hidden)')?.id;
    if (!currentSection) return;

    const endpointMap = {
        users: 'users',
        products: 'discounted_artefacts',
        orders: 'orders',
        categories: 'categories',
        discounts: 'discounts',
        artisans: 'artisans',
        stories: 'stories',
        reviews: 'reviews'
    };

    const tableFnMap = {
        users: populateUsers,
        products: populateProducts,
        orders: populateOrders,
        categories: populateCategories,
        discounts: populateDiscounts,
        artisans: populateArtisans,
        stories: populateStories,
        reviews: populateReviews
    };

    if (endpointMap[currentSection] && tableFnMap[currentSection]) {
        try {
            const data = await fetchData(endpointMap[currentSection]);
            const filtered = data.filter(item => Object.values(item).some(val => val && val.toString().toLowerCase().includes(query)));
            tableFnMap[currentSection](filtered);
        } catch (error) {
            console.error('Error in global search:', error);
            showToast(error.message, 'error');
        }
    }
});

// Search Filters
function setupSearch(id, endpoint, tableFn) {
    document.getElementById(id)?.addEventListener('input', async e => {
        console.log(`Search triggered for ${id}:`, e.target.value);
        const query = e.target.value.toLowerCase();
        try {
            const data = await fetchData(endpoint);
            const filtered = data.filter(item => Object.values(item).some(val => val && val.toString().toLowerCase().includes(query)));
            tableFn(filtered);
        } catch (error) {
            console.error(`Error in search for ${id}:`, error);
            showToast(error.message, 'error');
        }
    });
}

setupSearch('users-search', 'users', populateUsers);
setupSearch('products-search', 'discounted_artefacts', populateProducts);
setupSearch('orders-search', 'orders', populateOrders);
setupSearch('categories-search', 'categories', populateCategories);
setupSearch('discounts-search', 'discounts', populateDiscounts);
setupSearch('artisans-search', 'artisans', populateArtisans);
setupSearch('stories-search', 'stories', populateStories);
setupSearch('reviews-search', 'reviews', populateReviews);

// Populate Dropdowns
async function populateProductCategories() {
    console.log('Populating product categories');
    try {
        const categories = await fetchData('categories');
        const select = document.getElementById('product-category');
        select.innerHTML = categories.length ? categories.map(c => `<option value="${c.name}">${c.name}</option>`).join('') : '<option value="">No categories available</option>';
    } catch (error) {
        console.error('Error in populateProductCategories:', error);
        showToast(error.message, 'error');
    }
}

async function populateDiscountProducts() {
    console.log('Populating discount products');
    try {
        const products = await fetchData('discounted_artefacts');
        const select = document.getElementById('discount-product');
        select.innerHTML = products.length ? products.map(p => `<option value="${p.id}">${p.name}</option>`).join('') : '<option value="">No products available</option>';
    } catch (error) {
        console.error('Error in populateDiscountProducts:', error);
        showToast(error.message, 'error');
    }
}

// Logout
async function logout() {
    console.log('Logging out');
    try {
        const response = await fetch('/logout', { credentials: 'include' });
        console.log('Logout response:', response.status, response.url);
        const data = await response.json();
        showToast(data.message || 'Logged out successfully');
        setTimeout(() => window.location.href = '/login', 1000);
    } catch (error) {
        console.error('Error in logout:', error);
        showToast(error.message, 'error');
    }
}

// Polling for Orders
function pollOrders() {
    console.log('Starting order polling');
    setInterval(async () => {
        const ordersSection = document.getElementById('orders');
        if (ordersSection && !ordersSection.classList.contains('hidden')) {
            console.log('Polling orders');
            await populateOrders();
            await fetchDashboardStats();
        }
    }, 15000);
}

// Check Session
async function checkSession() {
    console.log('Checking session');
    try {
        const response = await fetch('/api/check_session', { credentials: 'include' });
        console.log('Session check response:', response.status, response.url);
        if (response.redirected || response.status === 401) {
            showToast('Session invalid. Please log in.', 'error');
            window.location.href = '/login';
            return false;
        }
        return true;
    } catch (error) {
        console.error('Error in checkSession:', error);
        showToast('Failed to verify session: ' + error.message, 'error');
        return false;
    }
}

// Initialize
async function initialize() {
    console.log('Initializing dashboard');
    try {
        const isAuthenticated = await checkSession();
        if (!isAuthenticated) return;

        // Run fetches individually to prevent Promise.all halting on single failure
        await fetchDashboardStats();
        await populateUsers();
        await populateProducts();
        await populateOrders();
        await populateCategories();
        await populateDiscounts();
        await populateArtisans();
        await populateStories();
        await populateReviews();
        pollOrders();
    } catch (error) {
        console.error('Error in initialize:', error);
        showToast('Initialization failed: ' + error.message, 'error');
    }
}

// Call initialization on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM content loaded, starting initialization');
    initialize();
});
   