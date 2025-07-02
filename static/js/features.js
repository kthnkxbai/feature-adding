document.addEventListener('DOMContentLoaded', function() {
    const tenantSelect = document.getElementById('tenantSelect');
    const enabledList = document.getElementById('enabledFeaturesList');
    const disabledList = document.getElementById('disabledFeaturesList');
    const enabledInput = document.getElementById('enabled_feature_ids_input');
    const disabledInput = document.getElementById('disabled_feature_ids_input');
    const enabledNoFeaturesMessage = document.getElementById('enabledNoFeaturesMessage');
    const disabledNoFeaturesMessage = document.getElementById('disabledNoFeaturesMessage');

    const initialSelectedTenantId = tenantSelect ? tenantSelect.value : null;

    let enabledSortableInstance = null;
    let disabledSortableInstance = null;

    function updateHiddenInputs() {
        const enabledIds = Array.from(enabledList.children)
                               .filter(item => item.dataset.id)
                               .map(item => item.dataset.id);
        enabledInput.value = enabledIds.join(',');
        
        if (enabledNoFeaturesMessage) {
            if (enabledIds.length === 0) {
                enabledNoFeaturesMessage.style.display = 'block';
            } else {
                enabledNoFeaturesMessage.style.display = 'none';
            }
        }

        const disabledIds = Array.from(disabledList.children)
                                .filter(item => item.dataset.id)
                                .map(item => item.dataset.id);
        disabledInput.value = disabledIds.join(',');

        if (disabledNoFeaturesMessage) {
            if (disabledIds.length === 0) {
                disabledNoFeaturesMessage.style.display = 'block';
            } else {
                disabledNoFeaturesMessage.style.display = 'none';
            }
        }
    }

    function populateFeatureList(listElement, features) {
        listElement.innerHTML = '';
        features.forEach(feature => {
            const listItem = document.createElement('li');
            listItem.classList.add('feature-item');
            listItem.dataset.id = feature.id;
            listItem.textContent = feature.name;
            listElement.appendChild(listItem);
        });
    }

    function initializeSortableLists() {
        if (enabledSortableInstance) {
            enabledSortableInstance.destroy();
        }
        if (disabledSortableInstance) {
            disabledSortableInstance.destroy();
        }

        enabledSortableInstance = new Sortable(enabledList, {
            group: 'features',
            animation: 150,
            onEnd: updateHiddenInputs
        });

        disabledSortableInstance = new Sortable(disabledList, {
            group: 'features',
            animation: 150,
            onEnd: updateHiddenInputs
        });
    }

    async function fetchAndPopulateTenantFeatures(tenantId) {
        if (enabledNoFeaturesMessage) enabledNoFeaturesMessage.style.display = 'none';
        if (disabledNoFeaturesMessage) disabledNoFeaturesMessage.style.display = 'none';
        
        enabledList.innerHTML = '<li class="no-selection">Loading enabled features...</li>';
        disabledList.innerHTML = '<li class="no-selection">Loading disabled features...</li>';

        try {
            const response = await fetch(`/api/tenant_features/${tenantId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            populateFeatureList(enabledList, data.enabled_features);
            populateFeatureList(disabledList, data.disabled_features);
            
            initializeSortableLists(); 
            updateHiddenInputs(); 
            
        } catch (error) {
            console.error('Error fetching tenant features:', error);
            enabledList.innerHTML = '<li class="no-selection text-danger">Error loading features.</li>';
            disabledList.innerHTML = '<li class="no-selection text-danger">Error loading features.</li>';
            
            if (enabledNoFeaturesMessage) enabledNoFeaturesMessage.style.display = 'block';
            if (disabledNoFeaturesMessage) disabledNoFeaturesMessage.style.display = 'block';
        }
    }

    if (tenantSelect) {
        tenantSelect.addEventListener('change', function() {
            const selectedTenantId = this.value;
            if (selectedTenantId) {
                window.location.href = `${window.location.pathname}?tenant_id=${selectedTenantId}`;
            } else {
                window.location.href = window.location.pathname;
            }
        });

        if (initialSelectedTenantId) {
            const featureConfigForm = document.getElementById('featureConfigForm');
            if (featureConfigForm) {
                fetchAndPopulateTenantFeatures(initialSelectedTenantId);
            } else {
                console.warn("Selected tenant ID present, but featureConfigForm not found.");
            }
        } else {
            if (enabledNoFeaturesMessage) enabledNoFeaturesMessage.style.display = 'block';
            if (disabledNoFeaturesMessage) disabledNoFeaturesMessage.style.display = 'block';
        }
    } else {
        console.error("Tenant select dropdown (id='tenantSelect') not found. Check your HTML.");
    }
});
