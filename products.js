(function() { // Entire script wrapped in an IIFE for scope isolation
    document.addEventListener('DOMContentLoaded', () => {
        // Ensure these IDs match your HTML.
        // If these are from the 'Manage Entities' section, they should ideally be 'mainProductSelect', etc.
        const productSelect = document.getElementById('productSelect');
        const addProductBtn = document.getElementById('addProductBtn');
        const editProductBtn = document.getElementById('editProductBtn');
        const deleteProductBtn = document.getElementById('deleteProductBtn');
        const viewProductBtn = document.getElementById('viewProductBtn');

        // Initial button states
        function toggleProductButtons() {
            const productId = productSelect.value;
            if (editProductBtn) editProductBtn.disabled = !productId;
            if (deleteProductBtn) deleteProductBtn.disabled = !productId;
        }

        function loadProducts() {
            // Using /api/products as per your script. Ensure this Flask route exists and returns JSON.
            fetch('/api/products')
                .then(res => {
                    if (!res.ok) {
                        return res.json().then(err => { throw new Error(err.message || 'Error fetching products'); });
                    }
                    return res.json();
                })
                .then(data => {
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
                    toggleProductButtons(); // Update buttons after populating
                })
                .catch(error => {
                    console.error('Error loading products:', error);
                    productSelect.innerHTML = `<option value="">-- Error loading products --</option>`;
                    productSelect.disabled = true;
                    if (viewProductBtn) viewProductBtn.disabled = true;
                    if (addProductBtn) addProductBtn.disabled = true; // Disable if products cannot be loaded
                    if (editProductBtn) editProductBtn.disabled = true;
                    if (deleteProductBtn) deleteProductBtn.disabled = true;
                    alert(`Failed to load products: ${error.message}`);
                });
        }

        // Event Listeners
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
                        method: 'DELETE', // IMPORTANT: Changed to DELETE method
                    });

                    if (response.status === 204) { // 204 No Content for successful deletion
                        alert('Product deleted successfully!');
                        loadProducts(); // Reload products to update the dropdown
                    } else if (response.status === 404) {
                        const errorData = await response.json();
                        alert(`Failed to delete product: ${errorData.message || 'Product not found.'}`);
                    } else if (response.status === 409) {
                        const errorData = await response.json();
                        alert(`Failed to delete product due to conflict: ${errorData.message || 'Unknown conflict.'}`);
                    } else {
                        const errorData = await response.json(); // Catch other potential JSON errors
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

        // Initial load on DOMContentLoaded
        loadProducts(); // Load products and set initial button states
    });
})(); // End of IIFE

