(function() {
    document.addEventListener('DOMContentLoaded', () => {

        const tenantSelect = document.getElementById('tenantSelect');
        const branchSelect = document.getElementById('branchSelect');
        const addBranchBtn = document.getElementById('addBranchBtn');
        const editBranchBtn = document.getElementById('editBranchBtn');
        const deleteBranchBtn = document.getElementById('deleteBranchBtn');
        const viewBranchBtn = document.getElementById('viewBranchBtn');

        if (branchSelect) branchSelect.disabled = true;
        if (addBranchBtn) addBranchBtn.disabled = true;
        if (editBranchBtn) editBranchBtn.disabled = true;
        if (deleteBranchBtn) deleteBranchBtn.disabled = true;
        if (viewBranchBtn) viewBranchBtn.disabled = true;

        const toggleBranchButtons = () => {
            const tenantId = tenantSelect.value;
            const branchId = branchSelect.value;
            const isSpecificBranchSelected = branchId && branchId !== "-1";

            if (addBranchBtn) addBranchBtn.disabled = !tenantId;
            if (editBranchBtn) editBranchBtn.disabled = !isSpecificBranchSelected;
            if (deleteBranchBtn) deleteBranchBtn.disabled = !isSpecificBranchSelected;
            if (viewBranchBtn) viewBranchBtn.disabled = !tenantId;
        };

        tenantSelect?.addEventListener('change', () => {
            const tenantId = tenantSelect.value;

            branchSelect.innerHTML = `<option value="">-- Select Branch --</option>`;
            branchSelect.disabled = true;
            editBranchBtn.disabled = true;
            deleteBranchBtn.disabled = true;
            if (!tenantId) {
                toggleBranchButtons();
                return;
            }

            fetch(`/api/tenants/${tenantId}/branches`)
                .then(res => {
                    if (!res.ok) {
                        return res.json().then(err => { throw new Error(err.message || 'Error fetching branches'); });
                    }
                    return res.json();
                })
                .then(data => {
                    if (data.length === 0) {
                        const noBranchesOption = document.createElement('option');
                        noBranchesOption.value = "-1";
                        noBranchesOption.textContent = "No branches for this tenant";
                        branchSelect.appendChild(noBranchesOption);
                        branchSelect.disabled = true;
                    } else {
                        branchSelect.disabled = false;
                        data.forEach(branch => {
                            const option = document.createElement('option');
                            option.value = branch.branch_id;
                            option.textContent = branch.name;
                            branchSelect.appendChild(option);
                        });
                    }
                    toggleBranchButtons();
                })
                .catch(error => {
                    console.error('Error loading branches:', error);
                    branchSelect.innerHTML = `<option value="">-- Error loading branches --</option>`;
                    branchSelect.disabled = true;
                    addBranchBtn.disabled = true;
                    editBranchBtn.disabled = true;
                    deleteBranchBtn.disabled = true;
                    viewBranchBtn.disabled = true;
                    alert(`Failed to load branches: ${error.message}`);
                });
        });

        branchSelect?.addEventListener('change', toggleBranchButtons);

        addBranchBtn?.addEventListener('click', () => {
            const tenantId = tenantSelect.value;
            if (!tenantId) return alert("Please select a tenant first.");
            window.location.href = `/branches/create/${tenantId}`;
        });

        editBranchBtn?.addEventListener('click', () => {
            const branchId = branchSelect.value;
            if (!branchId || branchId === "-1") {
                alert("Please select a branch to edit.");
                return;
            }
            window.location.href = `/branches/${branchId}/edit`;
        });

        deleteBranchBtn?.addEventListener('click', async () => {
            const branchId = branchSelect.value;
            if (!branchId || branchId === "-1") {
                alert("Please select a branch to delete.");
                return;
            }
            if (confirm("Are you sure you want to delete this branch?")) {
                try {
                    const response = await fetch(`/branches/${branchId}/delete`, {
                        method: 'DELETE',
                    });

                    if (response.status === 204) {
                        alert('Branch deleted successfully!');
                        if (tenantSelect.value) {
                             tenantSelect.dispatchEvent(new Event('change'));
                        } else {
                            branchSelect.innerHTML = `<option value="">-- Select Branch --</option>`;
                            branchSelect.disabled = true;
                            toggleBranchButtons();
                        }
                    } else if (response.status === 404) {
                        const errorData = await response.json();
                        alert(`Failed to delete branch: ${errorData.message || 'Branch not found.'}`);
                    } else if (response.status === 409) {
                        const errorData = await response.json();
                        alert(`Failed to delete branch due to conflict: ${errorData.message || 'Unknown conflict.'}`);
                    } else {
                        const errorData = await response.json();
                        alert(`Failed to delete branch: ${errorData.message || `Server error (Status: ${response.status})`}`);
                        console.error('Delete failed:', errorData);
                    }
                } catch (error) {
                    console.error('Network error during branch delete:', error);
                    alert('A network error occurred while deleting the branch.');
                }
            }
        });

        viewBranchBtn?.addEventListener('click', () => {
            const tenantId = tenantSelect.value;
            if (!tenantId) return alert("Please select a tenant first.");
            window.location.href = `/branches/view/${tenantId}`;
        });

        document.addEventListener('DOMContentLoaded', () => {
            if (tenantSelect.value) {
                tenantSelect.dispatchEvent(new Event('change'));
            } else {
                toggleBranchButtons();
            }
        });

    });
})();

