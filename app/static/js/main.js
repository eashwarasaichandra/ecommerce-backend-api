const API_URL = '/api';

// Utility: Toast notifications
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    if(!toast) return;
    toast.textContent = message;
    toast.className = `toast ${isError ? 'error' : ''}`;
    setTimeout(() => {
        toast.className = 'toast hidden';
    }, 3000);
}

// Auth State
function getToken() {
    return localStorage.getItem('token');
}

function updateNavState() {
    const token = getToken();
    if(token) {
        document.getElementById('nav-login')?.classList.add('hidden');
        document.getElementById('nav-logout')?.classList.remove('hidden');
        
        try {
            const user = JSON.parse(localStorage.getItem('user'));
            if(user && user.role === 'admin') {
                document.getElementById('nav-admin')?.classList.remove('hidden');
            } else {
                document.getElementById('nav-admin')?.classList.add('hidden');
            }
        } catch(e) {}
        
        fetchCartCount();
    } else {
        document.getElementById('nav-login')?.classList.remove('hidden');
        document.getElementById('nav-logout')?.classList.add('hidden');
        document.getElementById('nav-admin')?.classList.add('hidden');
        document.getElementById('cart-badge').classList.add('hidden');
    }
}

document.getElementById('nav-logout')?.addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
});

// Generic Fetch Wrapper
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = getToken();
    if(token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    const options = { method, headers };
    if(body) options.body = JSON.stringify(body);
    
    try {
        // Add cache-busting timestamp for GET requests
        let url = `${API_URL}${endpoint}`;
        if (method === 'GET') {
            url += (url.includes('?') ? '&' : '?') + `t=${new Date().getTime()}`;
        }
        
        const response = await fetch(url, options);
        const data = await response.json();
        if(!response.ok) {
            throw new Error(data.message || 'Something went wrong');
        }
        return data;
    } catch (err) {
        showToast(err.message, true);
        throw err;
    }
}

// Handlers
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const data = await apiCall('/auth/login', 'POST', { email, password });
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        showToast('Login successful!');
        setTimeout(() => window.location.href = '/', 1000);
    } catch(err) {}
}

async function handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        await apiCall('/auth/register', 'POST', { name, email, password });
        showToast('Registration successful! Please login.');
        setTimeout(() => window.location.href = '/login', 1500);
    } catch(err) {}
}

// Fetch Data
let currentPage = 1;
let currentSearch = '';
let currentCategory = '';

function setCategory(cat) {
    currentCategory = cat;
    currentPage = 1;
    fetchProducts();
    
    // Update active pill styling
    const pills = document.querySelectorAll('#category-pills .btn');
    pills.forEach(p => {
        if((cat === '' && p.innerText === 'All') || p.innerText === cat) {
            p.className = 'btn btn-primary';
        } else {
            p.className = 'btn btn-ghost';
        }
    });
}

function handleSearch() {
    const input = document.getElementById('search-input');
    if(input) {
        currentSearch = input.value;
        currentPage = 1;
        fetchProducts();
    }
}

async function fetchProducts(page = currentPage) {
    try {
        currentPage = page;
        let queryParams = `?page=${page}&limit=6`;
        if (currentSearch) queryParams += `&search=${encodeURIComponent(currentSearch)}`;
        if (currentCategory) queryParams += `&category=${encodeURIComponent(currentCategory)}`;
        
        const data = await apiCall(`/products/${queryParams}`);
        const grid = document.getElementById('products-grid');
        if(!grid) return;
        
        let products = data.products || data; // handle both new pagination and old array responses
        
        if (products.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem;">No products found.</div>';
            document.getElementById('pagination-controls').innerHTML = '';
            return;
        }
        
        grid.innerHTML = products.map(p => `
            <div class="product-card">
                <div class="product-image" onclick="viewProductDetails(${p.id})" style="cursor:pointer;">
                    ${p.image_url ? `<img src="${p.image_url}" alt="${p.name}">` : `<span style="font-size:3rem">🛍️</span>`}
                </div>
                <div class="product-info">
                    <div style="color:var(--accent); font-size:0.8rem; font-weight:bold; text-transform:uppercase;">${(p.category === 'Uncategorized' || !p.category) ? 'Other' : p.category}</div>
                    <h3 class="product-title" onclick="viewProductDetails(${p.id})" style="cursor:pointer;">${p.name}</h3>
                    <p class="product-desc">${p.description || 'No description available.'}</p>
                    <div class="product-price">$${p.price.toFixed(2)}</div>
                    <button class="btn btn-primary btn-block" onclick="addToCart(${p.id})">Add to Cart</button>
                    ${p.stock < 5 ? `<p class="mt-2 text-danger" style="color:var(--danger);font-size:0.8rem">Only ${p.stock} left in stock!</p>` : ''}
                </div>
            </div>
        `).join('');
        
        // Update pagination
        const pagination = document.getElementById('pagination-controls');
        if(pagination && data.pages) {
            let html = '';
            if (data.current_page > 1) {
                html += `<button class="btn btn-ghost" onclick="fetchProducts(${data.current_page - 1})">Previous</button>`;
            }
            html += `<span style="padding: 0.5rem;">Page ${data.current_page} of ${data.pages}</span>`;
            if (data.current_page < data.pages) {
                html += `<button class="btn btn-ghost" onclick="fetchProducts(${data.current_page + 1})">Next</button>`;
            }
            pagination.innerHTML = html;
        }
    } catch(err) {}
}

async function addToCart(productId) {
    if(!getToken()) {
        showToast('Please login to add items to cart', true);
        setTimeout(() => window.location.href = '/login', 1500);
        return;
    }
    
    try {
        await apiCall('/cart/add', 'POST', { product_id: productId, quantity: 1 });
        showToast('Item added to cart');
        fetchCartCount();
    } catch(err) {}
}

async function fetchCartCount() {
    try {
        const data = await apiCall('/cart/');
        const badge = document.getElementById('cart-badge');
        if(badge) {
            const count = data.items.reduce((acc, item) => acc + item.quantity, 0);
            badge.textContent = count;
            if(count > 0) badge.classList.remove('hidden');
            else badge.classList.add('hidden');
        }
    } catch(err) {}
}

async function fetchCart() {
    if(!getToken()) {
        window.location.href = '/login';
        return;
    }
    
    try {
        const data = await apiCall('/cart/');
        const cartItems = document.getElementById('cart-items');
        
        document.getElementById('cart-subtotal').textContent = `$${data.cart_total.toFixed(2)}`;
        document.getElementById('cart-total').textContent = `$${data.cart_total.toFixed(2)}`;
        
        if(!cartItems) return;
        
        if(data.items.length === 0) {
            cartItems.innerHTML = '<div class="glass-panel" style="padding:2rem;text-align:center;">Your cart is empty.</div>';
            document.getElementById('checkout-btn').disabled = true;
            return;
        }
        
        cartItems.innerHTML = data.items.map(item => `
            <div class="cart-item">
                <div class="cart-item-details">
                    <h4>${item.product_name}</h4>
                    <p>Qty: ${item.quantity}</p>
                </div>
                <div style="display:flex; gap:1rem; align-items:center;">
                    <div class="cart-item-price">$${item.item_total.toFixed(2)}</div>
                    <button class="btn btn-danger" onclick="removeFromCart(${item.id})">Remove</button>
                </div>
            </div>
        `).join('');
        document.getElementById('checkout-btn').disabled = false;
        
    } catch(err) {}
}

async function removeFromCart(itemId) {
    try {
        await apiCall(`/cart/remove/${itemId}`, 'DELETE');
        showToast('Item removed');
        fetchCart();
        fetchCartCount();
    } catch(err) {}
}

async function handleCheckout() {
    const btn = document.getElementById('checkout-btn');
    if(btn) {
        btn.disabled = true;
        btn.textContent = 'Processing Payment...';
    }
    
    try {
        await apiCall('/orders/', 'POST');
        showToast('Payment successful! Order placed.');
        setTimeout(() => window.location.href = '/orders', 1500);
    } catch(err) {
        if(btn) {
            btn.disabled = false;
            btn.textContent = 'Proceed to Checkout';
        }
    }
}

async function fetchOrders() {
    if(!getToken()) {
        window.location.href = '/login';
        return;
    }
    
    try {
        const orders = await apiCall('/orders/');
        const ordersList = document.getElementById('orders-list');
        if(!ordersList) return;
        
        if(orders.length === 0) {
            ordersList.innerHTML = '<div class="glass-panel" style="padding:2rem;text-align:center;">You have no orders yet.</div>';
            return;
        }
        
        ordersList.innerHTML = orders.map(order => `
            <div class="order-card">
                <div>
                    <h4>Order #${order.id}</h4>
                    <p>Date: ${new Date(order.created_at).toLocaleDateString()}</p>
                    <div class="order-items-preview">
                        ${order.items.map(i => `${i.quantity}x ${i.product_name}`).join(', ')}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:var(--accent);font-weight:700;font-size:1.25rem;margin-bottom:0.5rem;">$${order.total_price.toFixed(2)}</div>
                    <span style="background:var(--surface);padding:0.25rem 0.75rem;border-radius:12px;font-size:0.875rem;border:1px solid var(--border); margin-right: 0.5rem; color: ${order.payment_status === 'failed' ? 'var(--danger)' : 'var(--accent)'}">${order.payment_status?.toUpperCase() || 'PAID'}</span>
                    <span style="background:var(--surface);padding:0.25rem 0.75rem;border-radius:12px;font-size:0.875rem;border:1px solid var(--border);">${order.status.toUpperCase()}</span>
                </div>
            </div>
        `).join('');
    } catch(err) {}
}

async function viewProductDetails(id) {
    try {
        const p = await apiCall(`/products/${id}`);
        const modal = document.getElementById('product-modal');
        const content = document.getElementById('modal-content');
        if(!modal || !content) return;
        
        let avgRating = 0;
        if(p.reviews && p.reviews.length > 0) {
            avgRating = p.reviews.reduce((a, b) => a + b.rating, 0) / p.reviews.length;
        }
        
        let starsHTML = '';
        for(let i=1; i<=5; i++) {
            starsHTML += `<span style="color: ${i <= Math.round(avgRating) ? 'gold' : '#475569'}; font-size: 1.25rem;">★</span>`;
        }
        
        content.innerHTML = `
            <div style="display:flex; gap:2rem; flex-wrap:wrap; margin-bottom: 2rem;">
                <div style="flex:1; min-width:250px; background:var(--surface); border-radius:16px; overflow:hidden;">
                    ${p.image_url ? `<img src="${p.image_url}" style="width:100%; height:auto;">` : ''}
                </div>
                <div style="flex:2; min-width:300px;">
                    <div style="color:var(--accent); font-weight:bold; text-transform:uppercase;">${(p.category === 'Uncategorized' || !p.category) ? 'Other' : p.category}</div>
                    <h2 style="font-size:2rem; margin-bottom:0.5rem;">${p.name}</h2>
                    <div>${starsHTML} <span style="font-size:0.875rem; color: #94a3b8;">(${p.reviews?.length || 0} reviews)</span></div>
                    <p style="margin: 1rem 0; color:#cbd5e1; line-height:1.6;">${p.description}</p>
                    <div style="font-size:1.5rem; font-weight:800; color:var(--text); margin-bottom:1.5rem;">$${p.price.toFixed(2)}</div>
                    <button class="btn btn-primary" onclick="addToCart(${p.id})">Add to Cart</button>
                    ${p.stock < 5 ? `<p class="mt-2 text-danger" style="color:var(--danger);font-size:0.8rem">Only ${p.stock} left in stock!</p>` : ''}
                </div>
            </div>
            
            <div style="border-top: 1px solid var(--border); padding-top: 2rem;">
                <h3>Customer Reviews</h3>
                <div style="margin: 1.5rem 0; max-height: 300px; overflow-y:auto;">
                    ${(p.reviews || []).map(r => `
                        <div style="background:var(--surface); border:1px solid var(--border); padding:1rem; border-radius:12px; margin-bottom:1rem;">
                            <div style="display:flex; justify-content:space-between;">
                                <strong>${r.user}</strong>
                                <span style="color:gold;">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</span>
                            </div>
                            <p style="margin-top:0.5rem; color:#cbd5e1;">${r.comment}</p>
                            <div style="font-size:0.75rem; color:#64748b; margin-top:0.5rem;">${new Date(r.date).toLocaleDateString()}</div>
                        </div>
                    `).join('')}
                    ${p.reviews?.length === 0 ? '<p>No reviews yet. Be the first!</p>' : ''}
                </div>
                
                ${getToken() ? `
                    <div style="background:rgba(255,255,255,0.02); padding:1.5rem; border-radius:12px;">
                        <h4>Write a Review</h4>
                        <form id="review-form" onsubmit="submitReview(event, ${p.id})">
                            <div class="form-group" style="margin: 1rem 0;">
                                <label>Rating (1-5)</label>
                                <input type="number" id="review-rating" min="1" max="5" required style="width:100px;">
                            </div>
                            <div class="form-group" style="margin-bottom: 1rem;">
                                <label>Comment</label>
                                <textarea id="review-comment" required style="width:100%; padding:0.75rem; border-radius:8px; border:1px solid var(--border); background:var(--bg-color); color:white; min-height:80px;"></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary">Submit Review</button>
                        </form>
                    </div>
                ` : '<p style="color:var(--accent);"><em>Please log in to leave a review.</em></p>'}
            </div>
        `;
        
        modal.style.display = 'flex';
    } catch(err) {}
}

async function submitReview(e, productId) {
    e.preventDefault();
    const rating = document.getElementById('review-rating').value;
    const comment = document.getElementById('review-comment').value;
    
    try {
        await apiCall(`/products/${productId}/reviews`, 'POST', { rating, comment });
        showToast('Review submitted!');
        viewProductDetails(productId); // Refresh
    } catch(err) {}
}

// Init Navigation State
document.addEventListener('DOMContentLoaded', updateNavState);
