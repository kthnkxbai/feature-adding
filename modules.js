document.addEventListener('DOMContentLoaded', async function () {
    const tenantSelect                     = document.getElementById('tenantSelect');
    const branchSelect                     = document.getElementById('branchSelect');
    const productSelect                    = document.getElementById('productSelect');
    const moduleToggle                     = document.getElementById('moduleMultiSelectToggle');
    const selectedModuleCountSpan          = document.getElementById('selectedModuleCount');
    const moduleSearchInput                = document.getElementById('moduleSearchInput');
    const moduleCheckboxesContainer        = document.getElementById('moduleCheckboxes');
    const hiddenModuleIdsInput             = document.getElementById('module_ids_hidden');
    const previewConfiguredContainer       = document.getElementById('preview-configured-modules');
    const previewPendingContainer          = document.getElementById('preview-new-selection-modules');

    const MODULE_ID_SEQUENCES     = window.module_id_sequences             || {};  
    const initialSelectedStr      = window.initial_selected_module_ids_str || '';

    let selectedTenantId   = Number(tenantSelect.value)  || null;
    let selectedBranchId   = Number(branchSelect.value)  || null;
    let selectedProductId  = Number(productSelect.value) || null;

    let allAvailableModules      = [];           
    const initialConfiguredIds   = new Set();    
    const currentlySelectedIds   = new Set();    

    const getSeq = id => MODULE_ID_SEQUENCES[id] || 9999;

    const setHiddenValue = () => {
        hiddenModuleIdsInput.value = Array.from(currentlySelectedIds).join(',');
    };

    const setSelectedCount = () => {
        selectedModuleCountSpan.textContent = `${currentlySelectedIds.size} modules selected`;
    };

    const clearModulesUI = (message = 'Select a Branch and Product to load modules.') => {
        moduleCheckboxesContainer.innerHTML   = `<div class="list-group-item px-2 border-0 text-muted">${message}</div>`;
        previewConfiguredContainer.innerHTML  = '<div class="list-group-item text-muted">Select a Branch and Product</div>';
        previewPendingContainer.innerHTML     = '<div class="list-group-item text-muted">Select a Branch and Product</div>';
        moduleToggle.disabled  = true;
        moduleSearchInput.value = '';
        moduleSearchInput.disabled = true;
    };

    async function fetchProducts(){
        productSelect.innerHTML = '<option value="">Loading…</option>';
        try{
            const res = await fetch(`/api/products`);
            if(!res.ok) throw new Error(`Status ${res.status}`);
            const products = await res.json();
            productSelect.innerHTML = '<option value="">Select Product</option>';
            products.forEach(p=>{
                const opt = document.createElement('option');
                opt.value = p.product_id;
                opt.textContent = p.name || p.code || `Product ${p.product_id}`;
                productSelect.appendChild(opt);
            });
            productSelect.disabled = false;
        }catch(err){
            console.error('Failed to fetch products', err);
            productSelect.innerHTML = '<option value="">No products</option>';
            productSelect.disabled = true;
        }
    }

    async function fetchAndRenderModules(){
        selectedBranchId  = Number(branchSelect.value)  || null;
        selectedProductId = Number(productSelect.value) || null;

        clearModulesUI('Loading modules…');
        currentlySelectedIds.clear();
        initialConfiguredIds.clear();
        setHiddenValue();
        setSelectedCount();

        if(!selectedBranchId || !selectedProductId) return; 

        try{
            const res = await fetch(`/api/products/${selectedProductId}/modules?branch_id=${selectedBranchId}`);
            if(!res.ok) throw new Error(`Status ${res.status}`);
            const modules = await res.json();
            allAvailableModules = modules.map(m => ({id:m.id, name:m.name, is_configured: m.is_configured}));
            allAvailableModules.forEach(m => {
                if(m.is_configured) initialConfiguredIds.add(m.id);
            });
            initialConfiguredIds.forEach(id => currentlySelectedIds.add(id));
            initialSelectedStr.split(',').map(Number).filter(Boolean).forEach(id => currentlySelectedIds.add(id));

            renderModuleCheckboxes('');
            renderPreview();

            moduleToggle.disabled   = false;
            moduleSearchInput.disabled = false;
            setHiddenValue();
            setSelectedCount();
        }catch(err){
            console.error('Failed to fetch modules', err);
            clearModulesUI('Error loading modules');
        }
    }

    function renderModuleCheckboxes(search = ''){
        const term = search.trim().toLowerCase();
        const list = allAvailableModules
            .filter(m => m.name && m.name.toLowerCase().includes(term))
            .sort((a,b)=>{
                const seqDiff = getSeq(a.id) - getSeq(b.id);
                return seqDiff !== 0 ? seqDiff : a.name.localeCompare(b.name);
            });

        moduleCheckboxesContainer.innerHTML = '';
        if(list.length === 0){
            moduleCheckboxesContainer.innerHTML = '<div class="list-group-item px-2 border-0 text-muted">No matching modules.</div>';
            return;
        }

        list.forEach(m=>{
            const checked = currentlySelectedIds.has(m.id);
            const configured = initialConfiguredIds.has(m.id);
            const row = document.createElement('div');
            row.className = 'list-group-item px-2 border-0';
            row.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input module-checkbox" type="checkbox" value="${m.id}" id="moduleCheck${m.id}" ${checked? 'checked':''}>
                    <label class="form-check-label" for="moduleCheck${m.id}">
                        ${m.name} <span class="badge bg-secondary ms-2">Seq: ${getSeq(m.id)}</span>
                        ${configured? '<span class="badge bg-info ms-2">Configured</span>':''}
                    </label>
                </div>`;
            row.querySelector('input').addEventListener('change', e=>{
                if(e.target.checked){ currentlySelectedIds.add(m.id); } else { currentlySelectedIds.delete(m.id); }
                setHiddenValue();
                setSelectedCount();
                renderPreview();
            });
            moduleCheckboxesContainer.appendChild(row);
        });
    }

    function renderPreview(){
        previewConfiguredContainer.innerHTML = '';
        previewPendingContainer.innerHTML    = '';

        const toKeep   = [];
        const toAdd    = [];
        const toRemove = [];

        allAvailableModules.forEach(m=>{
            const selected   = currentlySelectedIds.has(m.id);
            const configured = initialConfiguredIds.has(m.id);
            if(selected && configured)      toKeep.push(m);
            else if(selected && !configured) toAdd.push(m);
            else if(!selected && configured) toRemove.push(m);
        });

        const buildList = (arr, badgeClass, badgeText) => {
            const frag = document.createDocumentFragment();
            arr.sort((a,b)=>getSeq(a.id)-getSeq(b.id)).forEach(m=>{
                const div = document.createElement('div');
                div.className = 'list-group-item d-flex justify-content-between align-items-center';
                div.innerHTML = `<span>${m.name}</span><span class="badge ${badgeClass}">${badgeText}</span>`;
                frag.appendChild(div);
            });
            return frag;
        };

        if(toKeep.length){
            previewConfiguredContainer.appendChild(buildList(toKeep,'bg-secondary','Seq'));
        }else{
            previewConfiguredContainer.innerHTML = '<div class="list-group-item text-muted">No modules currently configured.</div>';
        }

        if(toAdd.length || toRemove.length){
            if(toAdd.length){
                const head = document.createElement('div');
                head.className = 'list-group-item text-primary fw-bold';
                head.textContent = 'Modules to Add:';
                previewPendingContainer.appendChild(head);
                previewPendingContainer.appendChild(buildList(toAdd,'bg-success','Add'));
            }
            if(toRemove.length){
                const head = document.createElement('div');
                head.className = 'list-group-item text-danger fw-bold';
                head.textContent = 'Modules to Remove:';
                previewPendingContainer.appendChild(head);
                previewPendingContainer.appendChild(buildList(toRemove,'bg-danger','Remove'));
            }
        }else{
            previewPendingContainer.innerHTML = '<div class="list-group-item text-muted">No pending changes.</div>';
        }
    }

    async function onTenantChange(){
        selectedTenantId = Number(tenantSelect.value) || null;
        await fetchProducts();

        branchSelect.innerHTML = '<option value="">Loading branches…</option>';
        try {
            const res = await fetch(`/api/tenants/${selectedTenantId}/branches`);
            if (!res.ok) throw new Error(`Status ${res.status}`);
            const branches = await res.json();

            if (branches.length === 0) {
                branchSelect.innerHTML = '<option value="">No branches available for this tenant</option>';
                branchSelect.disabled = true;
            } else {
                branchSelect.innerHTML = '<option value="">Select Branch</option>';
                branches.forEach(b => {
                    const opt = document.createElement('option');
                    opt.value = b.branch_id;
                    opt.textContent = b.name;
                    branchSelect.appendChild(opt);
                });
                branchSelect.disabled = false;
            }
        } catch (err) {
            console.error('Failed to fetch branches', err);
            branchSelect.innerHTML = '<option value="">Error loading branches</option>';
            branchSelect.disabled = true;
        }

        clearModulesUI();
    }

    tenantSelect .addEventListener('change', onTenantChange);
    branchSelect .addEventListener('change', fetchAndRenderModules);
    productSelect.addEventListener('change', fetchAndRenderModules);
    moduleSearchInput.addEventListener('input', e=> renderModuleCheckboxes(e.target.value));

    if(selectedTenantId) await onTenantChange();
    if(selectedBranchId && selectedProductId) await fetchAndRenderModules();

    if(initialSelectedStr){
        initialSelectedStr.split(',').map(Number).filter(Boolean).forEach(id=> currentlySelectedIds.add(id));
        setHiddenValue();
        setSelectedCount();
        renderPreview();
    }
});

