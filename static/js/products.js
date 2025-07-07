document.addEventListener('DOMContentLoaded', () => {
    const productSelect = document.getElementById('productSelect');
    const addBtn = document.getElementById('addProductBtn');
    const editBtn = document.getElementById('editProductBtn');
    const delBtn = document.getElementById('deleteProductBtn');
    const viewBtn = document.getElementById('viewProductBtn'); 
    const toggleActionButtons = () => {
        const hasSelection = !!productSelect.value;
        if (editBtn) editBtn.disabled = !hasSelection;
        if (delBtn) delBtn.disabled = !hasSelection;
    };

    async function loadProducts() {
        try {
            const res = await fetch('/api/products');
            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.message || `Server error (${res.status})`);
            }

            const products = await res.json();

            productSelect.innerHTML = '<option value="">— Select Product —</option>';

            products.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.product_id;
                opt.textContent = p.name || p.code || `Product ${p.product_id}`; 
                productSelect.appendChild(opt);
            });

            productSelect.disabled = products.length === 0;

            if (viewBtn) {
                 viewBtn.disabled = products.length === 0;
            }


            toggleActionButtons();

        } catch (err) {
            console.error('Product load failed:', err);
            productSelect.innerHTML = '<option value="">— Error loading —</option>';
            productSelect.disabled = true; 

            if (viewBtn) viewBtn.disabled = true;
            if (addBtn) addBtn.disabled = true; 
            if (editBtn) editBtn.disabled = true;
            if (delBtn) delBtn.disabled = true;

            alert(`Cannot load products: ${err.message}`);
        }
    }

    if (productSelect) {
        productSelect.addEventListener('change', toggleActionButtons);
    } else {
        console.warn("Element with ID 'productSelect' not found. Product selection functionality may be limited.");
    }


    if (addBtn) {
        addBtn.addEventListener('click', () => {
            window.location.href = '/products/create';
        });
    } else {
        console.warn("Element with ID 'addProductBtn' not found. Add product functionality may be limited.");
    }


    if (editBtn) {
        editBtn.addEventListener('click', () => {
            const productId = productSelect.value;
            if (!productId) {
                alert('Please select a product to edit.');
                return;
            }
            window.location.href = `/products/${productId}/edit`;
        });
    } else {
        console.warn("Element with ID 'editProductBtn' not found. Edit product functionality may be limited.");
    }


    if (delBtn) {
        delBtn.addEventListener('click', async () => {
            const productId = productSelect.value;
            if (!productId) {
                alert('Please select a product to delete.');
                return;
            }

            if (confirm(`Are you sure you want to delete product ID ${productId}? This action cannot be undone.`)) {
                try {
                    const response = await fetch(`/api/products/${productId}/delete`, {
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
                        alert(`Failed to delete product due to conflict: ${errorData.message || 'Product is in use elsewhere.'}`);
                    } else {
                        const errorData = await response.json().catch(() => ({})); 
                        alert(`Failed to delete product: ${errorData.message || `Server error (Status: ${response.status})`}`);
                        console.error('Delete failed:', errorData);
                    }
                } catch (error) {
                    console.error('Network error during product delete:', error);
                    alert('A network error occurred while deleting the product. Please check your connection.');
                }
            }
        });
    } else {
        console.warn("Element with ID 'deleteProductBtn' not found. Delete product functionality may be limited.");
    }


    if (viewBtn) {
        viewBtn.addEventListener('click', () => {
            
            window.location.href = '/products/view';
        });
    } else {
        console.warn("Element with ID 'viewProductBtn' not found. View products functionality may be limited.");
    }


    
    loadProducts();
});
