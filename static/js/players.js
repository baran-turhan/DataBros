document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // 1. SEARCH (SEARCH BAR) LOGIC - SERVER SIDE
    // ============================================================
    const searchInput = document.getElementById('searchInput');
    const inputSearch = document.getElementById('inputSearch');
    const filterForm = document.getElementById('filterForm');

    // Debounce timer: don't search on every keypress,
    // search 600ms after typing stops.
    let typingTimer;
    const doneTypingInterval = 600; // ms

    if (searchInput) {
        // Reset timer while user types
        searchInput.addEventListener('input', function() {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(performSearch, doneTypingInterval);
        });

        // Search immediately on Enter
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(typingTimer);
                performSearch();
            }
        });
    }

    function performSearch() {
        // 1. Copy search value into the hidden form
        if (inputSearch && searchInput) {
            inputSearch.value = searchInput.value;
        }
        
        // 2. Populate hidden inputs for Foot and Position (helper)
        refreshHiddenInputs();

        // 3. Submit the form (page reloads and data comes from the DB)
        if (filterForm) {
            filterForm.submit();
        }
    }

    // ============================================================
    // 2. AGE FILTER (AGE SLIDER) LOGIC
    // ============================================================
    const sliderContainer = document.getElementById('sliderContainer');
    
    // If the slider isn't on the page (no data), skip slider logic
    if (sliderContainer) {
        const sliderTrack = document.getElementById('sliderTrack');
        const sliderFill = document.getElementById('sliderFill');
        const sliderPointsContainer = document.getElementById('sliderPoints');
        const sliderTooltip = document.getElementById('sliderTooltip');
        const ageButtonLabel = document.getElementById('ageButtonLabel');
        const inputMinAge = document.getElementById('inputMinAge');
        const inputMaxAge = document.getElementById('inputMaxAge');
        const ageDropdownBtn = document.getElementById('ageDropdownBtn');
        const ageDropdown = document.getElementById('ageDropdown');

        // Read dynamic bounds from HTML (global min/max)
        const MIN_AGE = parseInt(sliderContainer.getAttribute('data-global-min')) || 15;
        const MAX_AGE = parseInt(sliderContainer.getAttribute('data-global-max')) || 45;

        // Get selected ages
        let selectedAges = [];
        const serverMin = sliderContainer.getAttribute('data-min');
        const serverMax = sliderContainer.getAttribute('data-max');

        if (serverMin && serverMax) {
            if (serverMin === serverMax) selectedAges = [parseInt(serverMin)];
            else selectedAges = [parseInt(serverMin), parseInt(serverMax)];
        } else if (serverMin) {
            selectedAges = [parseInt(serverMin)];
        }

        // Render the slider on page load
        updateSliderUI();

        // --- Event Listeners (Slider) ---

        // Toggle dropdown
        if (ageDropdownBtn) {
            ageDropdownBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                ageDropdown.classList.toggle('show');
                // Close other open dropdowns
                const footDrop = document.getElementById('footDropdown');
                if(footDrop) footDrop.classList.remove('show');
                const posDrop = document.getElementById('posDropdown');
                if(posDrop) posDrop.classList.remove('show');
                const sortDrop = document.getElementById('sortDropdown');
                if(sortDrop) sortDrop.classList.remove('show');
                const mvDrop = document.getElementById('mvDropdown');
                if(mvDrop) mvDrop.classList.remove('show');
            });
        }

        // Mouse move (show tooltip)
        sliderTrack.parentElement.addEventListener('mousemove', function(e) {
            const rect = sliderTrack.getBoundingClientRect();
            let percent = (e.clientX - rect.left) / rect.width;
            percent = Math.max(0, Math.min(1, percent));
            
            const age = Math.round(MIN_AGE + percent * (MAX_AGE - MIN_AGE));
            
            sliderTooltip.style.left = (percent * 100) + '%';
            sliderTooltip.style.opacity = '1';
            sliderTooltip.innerText = age;
        });

        sliderTrack.parentElement.addEventListener('mouseleave', function() {
            sliderTooltip.style.opacity = '0';
        });

        // Click logic (add/remove/move point)
        sliderTrack.parentElement.addEventListener('click', function(e) {
            e.stopPropagation(); // Keep dropdown open

            const rect = sliderTrack.getBoundingClientRect();
            let percent = (e.clientX - rect.left) / rect.width;
            percent = Math.max(0, Math.min(1, percent));
            const clickedAge = Math.round(MIN_AGE + percent * (MAX_AGE - MIN_AGE));

            // Is the clicked age already selected?
            const existingIndex = selectedAges.indexOf(clickedAge);
            
            if (existingIndex !== -1) {
                // If yes, remove it
                selectedAges.splice(existingIndex, 1);
            } 
            else {
                if (selectedAges.length === 0) {
                    selectedAges.push(clickedAge);
                }
                else if (selectedAges.length === 1) {
                    selectedAges.push(clickedAge);
                }
                else if (selectedAges.length === 2) {
                    // If two points, update the nearest one
                    selectedAges.sort((a, b) => a - b);
                    const distToMin = Math.abs(clickedAge - selectedAges[0]);
                    const distToMax = Math.abs(clickedAge - selectedAges[1]);

                    if (clickedAge < selectedAges[0]) {
                        selectedAges[0] = clickedAge;
                    } else if (clickedAge > selectedAges[1]) {
                        selectedAges[1] = clickedAge;
                    } else {
                        // If clicked between, snap to nearest
                        if (distToMin <= distToMax) {
                            selectedAges[0] = clickedAge;
                        } else {
                            selectedAges[1] = clickedAge;
                        }
                    }
                }
            }
            updateSliderUI();
        });

        // Slider UI update function
        function updateSliderUI() {
            sliderPointsContainer.innerHTML = '';
            selectedAges.sort((a, b) => a - b); // Sort ascending

            if (selectedAges.length === 2) {
                // Fill the range
                const percent1 = ((selectedAges[0] - MIN_AGE) / (MAX_AGE - MIN_AGE)) * 100;
                const percent2 = ((selectedAges[1] - MIN_AGE) / (MAX_AGE - MIN_AGE)) * 100;
                sliderFill.style.left = percent1 + '%';
                sliderFill.style.width = (percent2 - percent1) + '%';
                
                ageButtonLabel.innerText = `${selectedAges[0]} - ${selectedAges[1]}`;
                inputMinAge.value = selectedAges[0];
                inputMaxAge.value = selectedAges[1];
            } 
            else if (selectedAges.length === 1) {
                // Single point
                sliderFill.style.width = '0';
                ageButtonLabel.innerText = `${selectedAges[0]}`;
                inputMinAge.value = selectedAges[0];
                inputMaxAge.value = selectedAges[0];
            } 
            else {
                // None
                sliderFill.style.width = '0';
                ageButtonLabel.innerText = 'All';
                inputMinAge.value = '';
                inputMaxAge.value = '';
            }

            // Render points
            selectedAges.forEach(age => {
                let safeAge = Math.max(MIN_AGE, Math.min(MAX_AGE, age));
                const percent = ((safeAge - MIN_AGE) / (MAX_AGE - MIN_AGE)) * 100;
                
                const point = document.createElement('div');
                point.className = 'slider-point';
                point.style.left = percent + '%';
                sliderPointsContainer.appendChild(point);
            });
        }
    }

    // ============================================================
    // 3. FOOT FILTER LOGIC
    // ============================================================
    const footDropdownBtn = document.getElementById('footDropdownBtn');
    const footDropdown = document.getElementById('footDropdown');
    const footAllCheckbox = document.getElementById('footAll');
    const footOptions = document.querySelectorAll('.foot-option');
    const footButtonLabel = document.getElementById('footButtonLabel');
    const footHiddenInputsContainer = document.getElementById('footHiddenInputs');
    const applyBtn = document.getElementById('applyFilterBtn');

    // Initial state check (process server data)
    const initialSelectedFeet = [];
    if (footHiddenInputsContainer) {
        const inputs = footHiddenInputsContainer.querySelectorAll('input');
        inputs.forEach(input => initialSelectedFeet.push(input.value));
    }

    if (initialSelectedFeet.length > 0) {
        footOptions.forEach(opt => {
            if (initialSelectedFeet.includes(opt.value)) {
                opt.checked = true;
            }
        });
        checkAllStatus();
        updateFootLabel();
    } else {
        // Default to "All"
        if (footAllCheckbox) footAllCheckbox.checked = true;
        footOptions.forEach(opt => opt.checked = true);
        updateFootLabel();
    }

    // Toggle dropdown
    if (footDropdownBtn) {
        footDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            footDropdown.classList.toggle('show');
            // Close age dropdown if open
            const ageDrop = document.getElementById('ageDropdown');
            if(ageDrop) ageDrop.classList.remove('show');
            const posDrop = document.getElementById('posDropdown');
            if(posDrop) posDrop.classList.remove('show');
            const sortDrop = document.getElementById('sortDropdown');
            if(sortDrop) sortDrop.classList.remove('show');
            const mvDrop = document.getElementById('mvDropdown');
            if(mvDrop) mvDrop.classList.remove('show');
        });
    }

    // "All" checkbox logic
    if (footAllCheckbox) {
        footAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            footOptions.forEach(opt => {
                opt.checked = isChecked;
            });
            updateFootLabel();
        });
    }

    // When sub-checkboxes change
    footOptions.forEach(opt => {
        opt.addEventListener('change', function() {
            checkAllStatus();
            updateFootLabel();
        });
    });

    function checkAllStatus() {
        const allChecked = Array.from(footOptions).every(opt => opt.checked);
        if (footAllCheckbox) footAllCheckbox.checked = allChecked;
    }

    function updateFootLabel() {
        if (!footButtonLabel) return;

        const checkedOpts = Array.from(footOptions).filter(opt => opt.checked);
        
        if (footAllCheckbox && footAllCheckbox.checked) {
            footButtonLabel.innerText = "All";
        } else if (checkedOpts.length === 0) {
            footButtonLabel.innerText = "None Selected";
        } else {
            const values = checkedOpts.map(opt => opt.value);
            footButtonLabel.innerText = values.join(" & ");
        }
    }

    // ============================================================
    // 4. POSITION FILTER LOGIC (NEW)
    // ============================================================
    const posDropdownBtn = document.getElementById('posDropdownBtn');
    const posDropdown = document.getElementById('posDropdown');
    const posAllCheckbox = document.getElementById('posAll');
    const posOptions = document.querySelectorAll('.pos-option');
    const posButtonLabel = document.getElementById('posButtonLabel');
    const posHiddenInputsContainer = document.getElementById('posHiddenInputs');

    // Initialize label
    // (Checked state comes from HTML, so only the label needs updating)
    if (posOptions.length > 0) {
        checkPosAllStatus();
        updatePosLabel();
    }

    // Toggle dropdown
    if (posDropdownBtn) {
        posDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            posDropdown.classList.toggle('show');
            // Close other dropdowns if open
            if(document.getElementById('ageDropdown')) document.getElementById('ageDropdown').classList.remove('show');
            if(document.getElementById('footDropdown')) document.getElementById('footDropdown').classList.remove('show');
            if(document.getElementById('sortDropdown')) document.getElementById('sortDropdown').classList.remove('show');
            if(document.getElementById('mvDropdown')) document.getElementById('mvDropdown').classList.remove('show');
        });
    }

    // "All" logic
    if (posAllCheckbox) {
        posAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            posOptions.forEach(opt => opt.checked = isChecked);
            updatePosLabel();
        });
    }

    // Single selection logic
    posOptions.forEach(opt => {
        opt.addEventListener('change', function() {
            checkPosAllStatus();
            updatePosLabel();
        });
    });

    function checkPosAllStatus() {
        const allChecked = Array.from(posOptions).every(opt => opt.checked);
        if (posAllCheckbox) posAllCheckbox.checked = allChecked;
    }

    function updatePosLabel() {
        if (!posButtonLabel) return;
        const checkedOpts = Array.from(posOptions).filter(opt => opt.checked);
        
        if (posAllCheckbox && posAllCheckbox.checked) {
            posButtonLabel.innerText = "All";
        } else if (checkedOpts.length === 0) {
            posButtonLabel.innerText = "None";
        } else if (checkedOpts.length === 1) {
            // If only one is selected, show its name
            posButtonLabel.innerText = checkedOpts[0].value;
        } else {
            // If multiple, show count (avoid long labels)
            posButtonLabel.innerText = `${checkedOpts.length} Selected`;
        }
    }

    // ============================================================
    // 5. APPLY FILTER AND OUTSIDE CLICK (UPDATED)
    // ============================================================
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            // A) Prepare foot values
            if (footHiddenInputsContainer) {
                footHiddenInputsContainer.innerHTML = '';
                if (footAllCheckbox && !footAllCheckbox.checked) {
                    Array.from(document.querySelectorAll('.foot-option'))
                        .filter(opt => opt.checked)
                        .forEach(opt => {
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = 'foot';
                            input.value = opt.value;
                            footHiddenInputsContainer.appendChild(input);
                        });
                }
            }

            // B) Prepare position values (NEW)
            if (posHiddenInputsContainer) {
                posHiddenInputsContainer.innerHTML = '';
                if (posAllCheckbox && !posAllCheckbox.checked) {
                    Array.from(document.querySelectorAll('.pos-option'))
                        .filter(opt => opt.checked)
                        .forEach(opt => {
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = 'position'; // name must be 'position'
                            input.value = opt.value;
                            posHiddenInputsContainer.appendChild(input);
                        });
                }
            }

            // Submit form
            const form = document.getElementById('filterForm');
            if (form) form.submit();
        });
    }

    // Close on outside click (global)
    // Navigate table rows to the profile page
    const playerRows = document.querySelectorAll('.players-table .player-row[data-player-id]');
    playerRows.forEach((row) => {
        const playerId = row.getAttribute('data-player-id');
        if (!playerId) return;
        row.style.cursor = 'pointer';
        row.addEventListener('click', (e) => {
            if (e.target.closest('.player-link')) return;
            window.location.href = `/players/${encodeURIComponent(playerId)}`;
        });
    });

    window.addEventListener('click', function(e) {
        const dropdowns = [
            {box: document.getElementById('ageDropdown'), btn: document.getElementById('ageDropdownBtn')},
            {box: document.getElementById('footDropdown'), btn: document.getElementById('footDropdownBtn')},
            {box: document.getElementById('posDropdown'), btn: document.getElementById('posDropdownBtn')}, // Newly added
            {box: document.getElementById('mvDropdown'), btn: document.getElementById('mvDropdownBtn')}, // Market Value
            {box: document.getElementById('sortDropdown'), btn: document.getElementById('sortDropdownBtn')}
        ];

        dropdowns.forEach(item => {
            if (item.box && item.btn && !item.box.contains(e.target) && !item.btn.contains(e.target)) {
                item.box.classList.remove('show');
            }
        });
    });

    // ============================================================
    // 6. CLOSE ON OUTSIDE CLICK (GLOBAL)
    // ============================================================
    window.addEventListener('click', function(e) {
        // Close age dropdown
        const ageDrop = document.getElementById('ageDropdown');
        const ageBtn = document.getElementById('ageDropdownBtn');
        if (ageDrop && ageBtn && !ageDrop.contains(e.target) && !ageBtn.contains(e.target)) {
            ageDrop.classList.remove('show');
        }

        // Close foot dropdown
        const footDrop = document.getElementById('footDropdown');
        const footBtn = document.getElementById('footDropdownBtn');
        if (footDrop && footBtn && !footDrop.contains(e.target) && !footBtn.contains(e.target)) {
            footDrop.classList.remove('show');
        }
    });

    // ============================================================
    // 7. SORTING LOGIC
    // ============================================================
    const sortDropdownBtn = document.getElementById('sortDropdownBtn');
    const sortDropdown = document.getElementById('sortDropdown');
    const sortItems = document.querySelectorAll('.sort-item');
    const sortButtonLabel = document.getElementById('sortButtonLabel');
    const inputSort = document.getElementById('inputSort');

    // Set initial label
    if (inputSort && inputSort.value) {
        // Find item with current value and read its label
        const currentItem = Array.from(sortItems).find(item => item.getAttribute('data-value') === inputSort.value);
        if (currentItem) {
            sortButtonLabel.innerText = currentItem.getAttribute('data-label');
            // Add a visual style to the selected item
            currentItem.style.backgroundColor = '#f0f4f8';
            currentItem.style.fontWeight = 'bold';
        }
    }

    // Toggle dropdown
    if (sortDropdownBtn) {
        sortDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sortDropdown.classList.toggle('show');
            // Close other dropdowns if open
            if(document.getElementById('ageDropdown')) document.getElementById('ageDropdown').classList.remove('show');
            if(document.getElementById('footDropdown')) document.getElementById('footDropdown').classList.remove('show');
            if(document.getElementById('posDropdown')) document.getElementById('posDropdown').classList.remove('show');
            if(document.getElementById('mvDropdown')) document.getElementById('mvDropdown').classList.remove('show');
        });
    }

    // Sorting selection
    sortItems.forEach(item => {
        item.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            
            // Update input
            if (inputSort) inputSort.value = value;
            
            // Submit the form immediately (sorting is usually instant)
            // If you want to integrate with Apply Filter, comment this out
            // and wait for the Apply button.
            // For UX, instant sorting is usually better:
            
            // Fill hidden inputs for Foot and Position (before submit)
            // (This mirrors applyBtn logic and refreshes data before submit)
            refreshHiddenInputs(); 
            
            document.getElementById('filterForm').submit();
        });
    });

    // Helper: populate hidden inputs from checkboxes before submit
    function refreshHiddenInputs() {
        const footContainer = document.getElementById('footHiddenInputs');
        const posContainer = document.getElementById('posHiddenInputs');
        const footAll = document.getElementById('footAll');
        const posAll = document.getElementById('posAll');

        if (footContainer) {
            footContainer.innerHTML = '';
            if (footAll && !footAll.checked) {
                Array.from(document.querySelectorAll('.foot-option'))
                    .filter(opt => opt.checked)
                    .forEach(opt => {
                        const i = document.createElement('input');
                        i.type = 'hidden'; i.name = 'foot'; i.value = opt.value;
                        footContainer.appendChild(i);
                    });
            }
        }
        if (posContainer) {
            posContainer.innerHTML = '';
            if (posAll && !posAll.checked) {
                Array.from(document.querySelectorAll('.pos-option'))
                    .filter(opt => opt.checked)
                    .forEach(opt => {
                        const i = document.createElement('input');
                        i.type = 'hidden'; i.name = 'position'; i.value = opt.value;
                        posContainer.appendChild(i);
                    });
            }
        }
    }

    // Include sort dropdown in outside click handling
    window.addEventListener('click', function(e) {
        // ... (Existing code) ...
        const sortDrop = document.getElementById('sortDropdown');
        const sortBtn = document.getElementById('sortDropdownBtn');
        if (sortDrop && sortBtn && !sortDrop.contains(e.target) && !sortBtn.contains(e.target)) {
            sortDrop.classList.remove('show');
        }
    });

    /* ============================================================
    MARKET VALUE SLIDER LOGIC (same structure as Age Slider)
    ============================================================ */
    
    const mvContainer = document.getElementById('mvSliderContainer');
    // if (!mvContainer) return; // Keep disabled so the rest of the code runs.

    // Read data from HTML data attributes
    if (mvContainer) {
        const gMin = parseInt(mvContainer.getAttribute('data-global-min')) || 0;
        const gMax = parseInt(mvContainer.getAttribute('data-global-max')) || 100000000;
        
        // If no selected values, use global limits
        let selMin = parseInt(mvContainer.getAttribute('data-min'));
        let selMax = parseInt(mvContainer.getAttribute('data-max'));
        if (isNaN(selMin)) selMin = gMin;
        if (isNaN(selMax)) selMax = gMax;

        const track = document.getElementById('mvSliderTrack');
        const fill = document.getElementById('mvSliderFill');
        const tooltip = document.getElementById('mvSliderTooltip');
        const pointsContainer = document.getElementById('mvSliderPoints');
        
        const labelBtn = document.getElementById('mvButtonLabel');
        const inputMinMv = document.getElementById('inputMinMv');
        const inputMaxMv = document.getElementById('inputMaxMv');
        
        // Create two points (min/max handles)
        const pointMin = document.createElement('div');
        pointMin.className = 'slider-point';
        const pointMax = document.createElement('div');
        pointMax.className = 'slider-point';
        
        pointsContainer.appendChild(pointMin);
        pointsContainer.appendChild(pointMax);

        // Helper to format numbers (e.g. 1.000.000)
        function formatMoney(num) {
            return '€' + num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        }
        
        // Short format (1M, 500K - optional, for button label)
        function formatShort(num) {
            if(num >= 1000000) return (num/1000000).toFixed(1) + 'M';
            if(num >= 1000) return (num/1000).toFixed(0) + 'K';
            return num;
        }

        function updateUI() {
            const range = gMax - gMin;
            const percentMin = ((selMin - gMin) / range) * 100;
            const percentMax = ((selMax - gMin) / range) * 100;

            // Point positions (percent from left)
            pointMin.style.left = percentMin + '%';
            pointMax.style.left = percentMax + '%';

            // Fill bar between points
            fill.style.left = percentMin + '%';
            fill.style.width = (percentMax - percentMin) + '%';

            // Update button label
            if (selMin === gMin && selMax === gMax) {
                labelBtn.innerText = "All";
                inputMinMv.value = "";
                inputMaxMv.value = "";
            } else {
                labelBtn.innerText = formatShort(selMin) + " - " + formatShort(selMax);
                inputMinMv.value = selMin;
                inputMaxMv.value = selMax;
            }
        }

        // Drag logic
        let isDraggingMin = false;
        let isDraggingMax = false;

        pointMin.addEventListener('mousedown', (e) => { isDraggingMin = true; e.preventDefault(); });
        pointMax.addEventListener('mousedown', (e) => { isDraggingMax = true; e.preventDefault(); });

        document.addEventListener('mouseup', () => {
            isDraggingMin = false;
            isDraggingMax = false;
            tooltip.style.opacity = '0'; // Hide tooltip on release
        });

        document.addEventListener('mousemove', (e) => {
            if (!isDraggingMin && !isDraggingMax) return;

            const rect = track.getBoundingClientRect();
            let offsetX = e.clientX - rect.left;
            // Clamp to bounds
            if (offsetX < 0) offsetX = 0;
            if (offsetX > rect.width) offsetX = rect.width;

            const percent = offsetX / rect.width;
            const range = gMax - gMin;
            let value = Math.round(gMin + (range * percent));

            // Apply step interval (e.g., 100,000 increments)
            const step = 100000;
            value = Math.round(value / step) * step;

            if (isDraggingMin) {
                if (value >= selMax) value = selMax - step; // Don't exceed max
                if (value < gMin) value = gMin;
                selMin = value;
            } else {
                if (value <= selMin) value = selMin + step; // Don't go below min
                if (value > gMax) value = gMax;
                selMax = value;
            }

            updateUI();
            
            // Update tooltip
            tooltip.style.opacity = '1';
            tooltip.innerText = formatMoney(isDraggingMin ? selMin : selMax);
            tooltip.style.left = (isDraggingMin ? pointMin.style.left : pointMax.style.left);
        });

        // Update UI on initial load
        updateUI();
    }

    // Slider button toggle (moved to the end)
    const mvBtn = document.getElementById('mvDropdownBtn');
    const mvDrop = document.getElementById('mvDropdown');
    
    if(mvBtn) {
        mvBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            mvDrop.classList.toggle('show');
            // Close other dropdowns (if any)
            if(document.getElementById('ageDropdown')) document.getElementById('ageDropdown').classList.remove('show');
            if(document.getElementById('footDropdown')) document.getElementById('footDropdown').classList.remove('show');
            if(document.getElementById('posDropdown')) document.getElementById('posDropdown').classList.remove('show');
            if(document.getElementById('sortDropdown')) document.getElementById('sortDropdown').classList.remove('show');
        });
    }

});
