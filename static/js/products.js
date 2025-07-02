(function() { 
    document.addEventListener('DOMContentLoaded', () => {
        const productSelect = document.getElementById('productSelect');
        const addProductBtn = document.getElementById('addProductBtn');
        const editProductBtn = document.getElementById('editProductBtn');
        const deleteProductBtn = document.getElementById('deleteProductBtn');
        const viewProductBtn = document.getElementById('viewProductBtn');

        function toggleProductButtons() {
            const productId = productSelect.value;
            if (editProductBtn) editProductBtn.disabled = !productId;
            if (deleteProductBtn) deleteProductBtn.disabled = !productId;
        }

        function loadProducts() {
            fetch('/api/products')
                .then(res => {
                    if (!res.ok) {
                        return res.json().then(err => { throw new Error(err.message || 'Error fetching products'); });
                    }
                    return res.json();
                })
                .then(response => {
                    const data = response.data || []; 
                    productSelect.innerHTML = `<option value="">-- Select Product --</option>`;
                    if (data.length === 0) {
                        productSelect.innerHTML = `<option value="">-- No products found --</option>`;
                        productSelect.disabled = true;
                        if (viewProductBtn) viewProductBtn.disabled = true;
                    } else {
                        data.forEach(product => {
                            const option = document.createElement('option');
                            option.value = product.product_id;
                            option.textContent = product.name || product.code || 'Unnamed Product';
                            productSelect.appendChild(option);
                        });
                        productSelect.disabled = false;
                        if (viewProductBtn) viewProductBtn.disabled = false;
                    }
                    toggleProductButtons(); 
                })
                .catch(error => {
                    console.error('Error loading products:', error);
                    productSelect.innerHTML = `<option value="">-- Error loading products --</option>`;
                    productSelect.disabled = true;
                    if (viewProductBtn) viewProductBtn.disabled = true;
                    if (addProductBtn) addProductBtn.disabled = true; 
                    if (editProductBtn) editProductBtn.disabled = true;
                    if (deleteProductBtn) deleteProductBtn.disabled = true;
                    alert(`Failed to load products: ${error.message}`);
                });
        }

        productSelect?.addEventListener('change', toggleProductButtons);

        addProductBtn?.addEventListener('click', () => {
            window.location.href = `/products/create`;
        });

        editProductBtn?.addEventListener('click', () => {
            const productId = productSelect.value;
            if (!productId) {
                alert("Please select a product to edit.");
                return;
            }
            window.location.href = `/products/${productId}/edit`;
        });

        deleteProductBtn?.addEventListener('click', async () => {
            const productId = productSelect.value;
            if (!productId) {
                alert("Please select a product to delete.");
                return;
            }
            if (confirm("Are you sure you want to delete this product?")) {
                try {
                    const response = await fetch(`/products/${productId}/delete`, {
                        method: 'DELETE', 
                    });

                    if (response.status === 204) { 
                        alert('Product deleted successfully!');
                        loadProducts(); 
                    } else if (response.status === 404) {
                        const errorData = await response.json();
                        alert(`Failed to delete product: ${errorData.message || 'Product not found.'}`);
                    } else if (response.status === 409) {
                        const errorData = await response.json();
                        alert(`Failed to delete product due to conflict: ${errorData.message || 'Unknown conflict.'}`);
                    } else {
                        const errorData = await response.json(); 
                        alert(`Failed to delete product: ${errorData.message || `Server error (Status: ${response.status})`}`);
                        console.error('Delete failed:', errorData);
                    }
                } catch (error) {
                    console.error('Network error during product delete:', error);
                    alert('A network error occurred while deleting the product.');
                }
            }
        });

        viewProductBtn?.addEventListener('click', () => {
            window.location.href = `/products/view`;
        });

        loadProducts(); 
    });
})(); 

