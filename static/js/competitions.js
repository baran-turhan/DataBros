document.addEventListener('DOMContentLoaded', function() {
    // Country Dropdown
    const countryDropdownBtn = document.getElementById('countryDropdownBtn');
    const countryDropdown = document.getElementById('countryDropdown');
    const countryInput = document.getElementById('countryInput');
    const countryButtonLabel = document.getElementById('countryButtonLabel');
    
    // Major League Dropdown
    const majorLeagueDropdownBtn = document.getElementById('majorLeagueDropdownBtn');
    const majorLeagueDropdown = document.getElementById('majorLeagueDropdown');
    const majorLeagueInput = document.getElementById('majorLeagueInput');
    const majorLeagueButtonLabel = document.getElementById('majorLeagueButtonLabel');
    
    // Toggle Country Dropdown
    if (countryDropdownBtn && countryDropdown) {
        countryDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            countryDropdown.classList.toggle('show');
            // Close other dropdown
            if (majorLeagueDropdown) majorLeagueDropdown.classList.remove('show');
        });
        
        // Handle Country Selection
        const countryItems = countryDropdown.querySelectorAll('.sort-item');
        countryItems.forEach(item => {
            item.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const label = this.getAttribute('data-label');
                
                countryInput.value = value;
                countryButtonLabel.textContent = label || 'Select country';
                
                // Update active state
                countryItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                
                // Close dropdown
                countryDropdown.classList.remove('show');
            });
        });
    }
    
    // Toggle Major League Dropdown
    if (majorLeagueDropdownBtn && majorLeagueDropdown) {
        majorLeagueDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            majorLeagueDropdown.classList.toggle('show');
            // Close other dropdown
            if (countryDropdown) countryDropdown.classList.remove('show');
        });
        
        // Handle Major League Selection
        const majorLeagueItems = majorLeagueDropdown.querySelectorAll('.sort-item');
        majorLeagueItems.forEach(item => {
            item.addEventListener('click', function() {
                const value = this.getAttribute('data-value');
                const label = this.getAttribute('data-label');
                
                majorLeagueInput.value = value;
                majorLeagueButtonLabel.textContent = label || 'All';
                
                // Update active state
                majorLeagueItems.forEach(i => i.classList.remove('active'));
                this.classList.add('active');
                
                // Close dropdown
                majorLeagueDropdown.classList.remove('show');
            });
        });
    }
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        if (countryDropdown && !countryDropdown.contains(e.target) && !countryDropdownBtn.contains(e.target)) {
            countryDropdown.classList.remove('show');
        }
        if (majorLeagueDropdown && !majorLeagueDropdown.contains(e.target) && !majorLeagueDropdownBtn.contains(e.target)) {
            majorLeagueDropdown.classList.remove('show');
        }
    });
});

