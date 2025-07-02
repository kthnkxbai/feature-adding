document.addEventListener('DOMContentLoaded', () => {
    const tenantSelect = document.getElementById('tenantSelect');
    const addBtn = document.getElementById('addTenantBtn');
    const editBtn = document.getElementById('editTenantBtn');
    const deleteBtn = document.getElementById('deleteTenantBtn');
    const viewBtn = document.getElementById('viewTenantBtn');

    if (!tenantSelect) return;

    const toggleButtons = () => {
        const tenantId = tenantSelect.value;
        if (editBtn) editBtn.disabled = !tenantId;
        if (deleteBtn) deleteBtn.disabled = !tenantId;
    };

    tenantSelect.addEventListener('change', toggleButtons);
    toggleButtons();

    if (addBtn) {
        addBtn.addEventListener('click', () => {
            window.location.href = "/tenants";
        });
    }

    if (viewBtn) {
        viewBtn.addEventListener('click', () => {
            window.location.href = "/view";
        });
    }

    if (editBtn) {
        editBtn.addEventListener('click', () => {
            const tenantId = tenantSelect.value;
            if (!tenantId) return alert("Please select a tenant to edit.");
            const option = tenantSelect.selectedOptions[0];
            const organizationCode = option.getAttribute('data-org-code');
            const subDomain = option.getAttribute('data-sub-domain');
            window.location.href = `/tenants/${tenantId}/${organizationCode}/${subDomain}`;
        });
    }

    if (deleteBtn) {
        deleteBtn.addEventListener('click', () => {
            const tenantId = tenantSelect.value;
            if (!tenantId) return alert("Please select a tenant to delete.");
            const option = tenantSelect.selectedOptions[0];
            const organizationCode = option.getAttribute('data-org-code');
            const subDomain = option.getAttribute('data-sub-domain');
            
            if (confirm("Are you sure you want to delete this tenant? This action cannot be undone.")) {
                
                const deleteUrl = `/api/tenants/${tenantId}/${organizationCode}/${subDomain}`;

                fetch(deleteUrl, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        
                    }
                })
                .then(response => {
                    if (response.ok) {
                        alert('Tenant deleted successfully!');
                        window.location.href = "/"; 
                    } else {
                        
                        response.text().then(errorText => {
                            console.error('Delete failed:', errorText);
                            alert('Failed to delete tenant: ' + errorText);
                        });
                    }
                })
                .catch(error => {
                   
                    console.error('Network error during delete:', error);
                    alert('A network error occurred while deleting the tenant.');
                });
            }
        });
    }
});
