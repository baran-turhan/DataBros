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

    // League row click -> fetch clubs for that competition
    const leagueRows = document.querySelectorAll('.league-row-trigger');
    const createLoadingRow = (leagueName) => {
        return `
            <div class="league-clubs-card">
                <div class="clubs-header">
                    <div class="clubs-title">Clubs in ${leagueName}</div>
                    <div class="clubs-subtitle">Fetching squads and stadium info…</div>
                </div>
                <div class="clubs-body">
                    <div class="clubs-loading">Loading clubs…</div>
                </div>
            </div>
        `;
    };

    const formatNumber = (value) => {
        const num = Number(value);
        return Number.isFinite(num) ? num : null;
    };

    const renderClubs = (clubs) => {
        if (!clubs || clubs.length === 0) {
            return `
                <div class="club-empty">
                    <div class="club-empty-title">No clubs found</div>
                    <div class="club-empty-subtitle">This league has no clubs in the database yet.</div>
                </div>
            `;
        }

        const clubRows = clubs.map((club) => {
            const capacityNum = formatNumber(club.stadium_capacity);
            const avgAgeNum = formatNumber(club.average_age);
            const squadNum = formatNumber(club.squad_size);
            const foreignNum = formatNumber(club.foreign_number);
            const nationalNum = formatNumber(club.national_number);

            const capacity = capacityNum !== null ? `${capacityNum.toLocaleString()} seats` : '—';
            const averageAge = avgAgeNum !== null ? `${avgAgeNum.toFixed(1)} avg age` : '—';
            const squadSize = squadNum !== null ? `${squadNum} squad` : '—';
            return `
                <div class="club-row">
                    <div class="club-name">${club.name || 'Unknown Club'}</div>
                    <div class="club-meta">
                        <span>${club.stadium_name || 'Stadium N/A'}</span>
                        <span class="dot">•</span>
                        <span>${capacity}</span>
                    </div>
                    <div class="club-tags">
                        <span class="chip">Squad: ${squadSize}</span>
                        <span class="chip">Foreigners: ${foreignNum !== null ? foreignNum : 0}</span>
                        <span class="chip">National Team: ${nationalNum !== null ? nationalNum : 0}</span>
                        <span class="chip">Age: ${averageAge}</span>
                    </div>
                </div>
            `;
        }).join('');

        return `<div class="clubs-list">${clubRows}</div>`;
    };

    const toggleLeagueRow = async (row) => {
        const existingDetail = row.nextElementSibling;
        if (existingDetail && existingDetail.classList.contains('league-clubs-row')) {
            existingDetail.remove();
            row.classList.remove('clubs-open');
            return;
        }

        const competitionId = row.getAttribute('data-competition-id');
        const leagueName = row.getAttribute('data-league-name') || 'League';
        if (!competitionId) return;

        const detailRow = document.createElement('div');
        detailRow.className = 'league-clubs-row';
        detailRow.innerHTML = createLoadingRow(leagueName);
        row.insertAdjacentElement('afterend', detailRow);
        row.classList.add('clubs-open');

        const bodyEl = detailRow.querySelector('.clubs-body');

        try {
            const response = await fetch(`/competitions/${encodeURIComponent(competitionId)}/clubs`);
            if (!response.ok) {
                throw new Error('Failed to fetch clubs');
            }
            const data = await response.json();
            bodyEl.innerHTML = renderClubs(data.clubs || []);
        } catch (err) {
            bodyEl.innerHTML = `
                <div class="club-empty error">
                    <div class="club-empty-title">Could not load clubs</div>
                    <div class="club-empty-subtitle">${err.message || 'Something went wrong.'}</div>
                </div>
            `;
            row.classList.remove('clubs-open');
        }
    };

    leagueRows.forEach((row) => {
        row.addEventListener('click', (event) => {
            if (event.target.closest('a')) return; // let the link behave normally
            toggleLeagueRow(row);
        });
    });
});
