document.addEventListener('DOMContentLoaded', function () {
    const tenantSelect = document.getElementById('tenantSelect');
    const enabledList = document.getElementById('enabledFeaturesList');
    const disabledList = document.getElementById('disabledFeaturesList');
    const enabledInput = document.getElementById('enabled_feature_ids_input');
    const disabledInput = document.getElementById('disabled_feature_ids_input');
    const enabledNoFeaturesMessage = document.getElementById('enabledNoFeaturesMessage');
    const disabledNoFeaturesMessage = document.getElementById('disabledNoFeaturesMessage');
    const featureForm = document.getElementById('featureConfigForm');

    let enabledSortableInstance = null;
    let disabledSortableInstance = null;

    function updateHiddenInputs() {
        const enabledIds = Array.from(enabledList.children)
            .filter(item => item.classList.contains('feature-item'))
            .map(item => item.dataset.id);
        enabledInput.value = enabledIds.join(',');

        if (enabledNoFeaturesMessage) {
            enabledNoFeaturesMessage.style.display = enabledIds.length === 0 ? 'block' : 'none';
        }

        const disabledIds = Array.from(disabledList.children)
            .filter(item => item.classList.contains('feature-item'))
            .map(item => item.dataset.id);
        disabledInput.value = disabledIds.join(',');

        if (disabledNoFeaturesMessage) {
            disabledNoFeaturesMessage.style.display = disabledIds.length === 0 ? 'block' : 'none';
        }

        console.log('Hidden Inputs Updated:');
        console.log('Enabled:', enabledInput.value);
        console.log('Disabled:', disabledInput.value);
    }

    function populateFeatureList(listElement, features, noFeaturesMsgElement) {
        listElement.innerHTML = '';
        

        if (features.length === 0) {
            if (noFeaturesMsgElement) {
                listElement.appendChild(noFeaturesMsgElement);
                noFeaturesMsgElement.style.display = 'block';
            }
        } else {
            if (noFeaturesMsgElement) noFeaturesMsgElement.style.display = 'none';
            features.forEach(feature => {
               

                const listItem = document.createElement('li');
                listItem.classList.add('feature-item');
                listItem.dataset.id = feature.feature_id;
                listItem.textContent = feature.name;
                listElement.appendChild(listItem);
            });
        }
    }

    function initializeSortableLists() {
        if (enabledSortableInstance) enabledSortableInstance.destroy();
        if (disabledSortableInstance) disabledSortableInstance.destroy();

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
        if (enabledNoFeaturesMessage) {
            enabledNoFeaturesMessage.textContent = 'Loading enabled features...';
            enabledNoFeaturesMessage.style.display = 'block';
        }
        if (disabledNoFeaturesMessage) {
            disabledNoFeaturesMessage.textContent = 'Loading disabled features...';
            disabledNoFeaturesMessage.style.display = 'block';
        }
        enabledList.innerHTML = '';
        disabledList.innerHTML = '';

        try {
            const response = await fetch(`/api/tenant-features/${tenantId}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            populateFeatureList(enabledList, data.enabled_features, enabledNoFeaturesMessage);
            populateFeatureList(disabledList, data.disabled_features, disabledNoFeaturesMessage);

            initializeSortableLists();
            updateHiddenInputs();

        } catch (error) {
            console.error('Error fetching tenant features:', error);
            if (enabledNoFeaturesMessage) {
                enabledNoFeaturesMessage.textContent = `Error loading features: ${error.message}`;
                enabledNoFeaturesMessage.style.display = 'block';
            }
            if (disabledNoFeaturesMessage) {
                disabledNoFeaturesMessage.textContent = `Error loading features: ${error.message}`;
                disabledNoFeaturesMessage.style.display = 'block';
            }
            enabledList.innerHTML = '';
            disabledList.innerHTML = '';
        }
    }

    if (tenantSelect) {
        tenantSelect.addEventListener('change', function () {
            const selectedTenantId = this.value;
            if (selectedTenantId) {
                window.location.href = `${window.location.pathname}?tenant_id=${selectedTenantId}`;
            } else {
                window.location.href = window.location.pathname;
            }
        });

        const urlParams = new URLSearchParams(window.location.search);
        const initialSelectedTenantIdFromUrl = urlParams.get('tenant_id');

        if (initialSelectedTenantIdFromUrl) {
            if (tenantSelect.value !== initialSelectedTenantIdFromUrl) {
                tenantSelect.value = initialSelectedTenantIdFromUrl;
            }
            document.getElementById('features-section').hidden = false;
            fetchAndPopulateTenantFeatures(initialSelectedTenantIdFromUrl);
        } else {
            document.getElementById('features-section').hidden = true;
            if (enabledNoFeaturesMessage) enabledNoFeaturesMessage.style.display = 'block';
            if (disabledNoFeaturesMessage) disabledNoFeaturesMessage.style.display = 'block';
            enabledList.innerHTML = '';
            disabledList.innerHTML = '';
        }
    } else {
        console.error("Tenant select dropdown (id='tenantSelect') not found. Check your HTML.");
    }

    if (featureForm) {
        featureForm.addEventListener('submit', function (event) {
            updateHiddenInputs();
        });
    }
});
