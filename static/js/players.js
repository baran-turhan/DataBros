document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // 1. ARAMA (SEARCH BAR) MANTIĞI
    // ============================================================
    const searchInput = document.getElementById('searchInput');
    const playerRows = document.querySelectorAll('.player-row');
    const noResultsRow = document.getElementById('noResultsRow');

    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase().trim();
            let visibleCount = 0;
            
            playerRows.forEach(row => {
                const playerName = row.getAttribute('data-player-name');
                const isVisible = playerName.includes(searchTerm);
                row.style.display = isVisible ? '' : 'none';
                if (isVisible) visibleCount += 1;
            });

            if (noResultsRow) {
                noResultsRow.style.display = visibleCount === 0 ? '' : 'none';
            }
        });
    }

    // ============================================================
    // 2. YAŞ FİLTRESİ (AGE SLIDER) MANTIĞI
    // ============================================================
    const sliderContainer = document.getElementById('sliderContainer');
    
    // Eğer sayfada slider yoksa (veri yoksa) slider kodlarını çalıştırma
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

        // Dinamik Sınırları HTML'den Oku (Global Min/Max)
        const MIN_AGE = parseInt(sliderContainer.getAttribute('data-global-min')) || 15;
        const MAX_AGE = parseInt(sliderContainer.getAttribute('data-global-max')) || 45;

        // Seçili yaşları al
        let selectedAges = [];
        const serverMin = sliderContainer.getAttribute('data-min');
        const serverMax = sliderContainer.getAttribute('data-max');

        if (serverMin && serverMax) {
            if (serverMin === serverMax) selectedAges = [parseInt(serverMin)];
            else selectedAges = [parseInt(serverMin), parseInt(serverMax)];
        } else if (serverMin) {
            selectedAges = [parseInt(serverMin)];
        }

        // Sayfa yüklenince Slider'ı çiz
        updateSliderUI();

        // --- Event Listeners (Slider) ---

        // Dropdown Aç/Kapa
        if (ageDropdownBtn) {
            ageDropdownBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                ageDropdown.classList.toggle('show');
                // Diğer dropdown açıksa kapat
                const footDrop = document.getElementById('footDropdown');
                if(footDrop) footDrop.classList.remove('show');
            });
        }

        // Mouse Hareketi (Tooltip Gösterimi)
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

        // Tıklama Mantığı (Nokta Ekle/Çıkar/Kaydır)
        sliderTrack.parentElement.addEventListener('click', function(e) {
            e.stopPropagation(); // Dropdown kapanmasın

            const rect = sliderTrack.getBoundingClientRect();
            let percent = (e.clientX - rect.left) / rect.width;
            percent = Math.max(0, Math.min(1, percent));
            const clickedAge = Math.round(MIN_AGE + percent * (MAX_AGE - MIN_AGE));

            // Tıklanan yaş zaten var mı?
            const existingIndex = selectedAges.indexOf(clickedAge);
            
            if (existingIndex !== -1) {
                // Varsa kaldır
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
                    // İki nokta varsa, en yakındakini güncelle
                    selectedAges.sort((a, b) => a - b);
                    const distToMin = Math.abs(clickedAge - selectedAges[0]);
                    const distToMax = Math.abs(clickedAge - selectedAges[1]);

                    if (clickedAge < selectedAges[0]) {
                        selectedAges[0] = clickedAge;
                    } else if (clickedAge > selectedAges[1]) {
                        selectedAges[1] = clickedAge;
                    } else {
                        // Ortaya tıklandıysa yakına git
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

        // Slider UI Güncelleme Fonksiyonu
        function updateSliderUI() {
            sliderPointsContainer.innerHTML = '';
            selectedAges.sort((a, b) => a - b); // Küçükten büyüğe sırala

            if (selectedAges.length === 2) {
                // Aralığı Boya
                const percent1 = ((selectedAges[0] - MIN_AGE) / (MAX_AGE - MIN_AGE)) * 100;
                const percent2 = ((selectedAges[1] - MIN_AGE) / (MAX_AGE - MIN_AGE)) * 100;
                sliderFill.style.left = percent1 + '%';
                sliderFill.style.width = (percent2 - percent1) + '%';
                
                ageButtonLabel.innerText = `${selectedAges[0]} - ${selectedAges[1]}`;
                inputMinAge.value = selectedAges[0];
                inputMaxAge.value = selectedAges[1];
            } 
            else if (selectedAges.length === 1) {
                // Tek nokta
                sliderFill.style.width = '0';
                ageButtonLabel.innerText = `${selectedAges[0]}`;
                inputMinAge.value = selectedAges[0];
                inputMaxAge.value = selectedAges[0];
            } 
            else {
                // Hiçbiri
                sliderFill.style.width = '0';
                ageButtonLabel.innerText = 'All';
                inputMinAge.value = '';
                inputMaxAge.value = '';
            }

            // Noktaları Çiz
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
    // 3. AYAK FİLTRESİ (FOOT FILTER) MANTIĞI
    // ============================================================
    const footDropdownBtn = document.getElementById('footDropdownBtn');
    const footDropdown = document.getElementById('footDropdown');
    const footAllCheckbox = document.getElementById('footAll');
    const footOptions = document.querySelectorAll('.foot-option');
    const footButtonLabel = document.getElementById('footButtonLabel');
    const footHiddenInputsContainer = document.getElementById('footHiddenInputs');
    const applyBtn = document.getElementById('applyFilterBtn');

    // Başlangıç Durumu Kontrolü (Serverdan gelen veriyi işle)
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
        // Varsayılan olarak "All" seçili olsun
        if (footAllCheckbox) footAllCheckbox.checked = true;
        footOptions.forEach(opt => opt.checked = true);
        updateFootLabel();
    }

    // Dropdown Aç/Kapa
    if (footDropdownBtn) {
        footDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            footDropdown.classList.toggle('show');
            // Age dropdown açıksa kapat
            const ageDrop = document.getElementById('ageDropdown');
            if(ageDrop) ageDrop.classList.remove('show');
        });
    }

    // "All" Checkbox Mantığı
    if (footAllCheckbox) {
        footAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            footOptions.forEach(opt => {
                opt.checked = isChecked;
            });
            updateFootLabel();
        });
    }

    // Alt Checkboxlar değişince
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
    // 4. APPLY FILTER (UYGULA) VE FORM SUBMIT
    // ============================================================
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            // Foot verilerini forma dinamik olarak ekle
            if (footHiddenInputsContainer) {
                footHiddenInputsContainer.innerHTML = ''; // Temizle

                // Eğer "All" seçili DEĞİLSE, seçili olanları tek tek ekle
                // (All seçiliyse URL'i temiz tutmak için foot parametresi göndermiyoruz)
                if (footAllCheckbox && !footAllCheckbox.checked) {
                    const checkedOpts = Array.from(footOptions).filter(opt => opt.checked);
                    checkedOpts.forEach(opt => {
                        const input = document.createElement('input');
                        input.type = 'hidden';
                        input.name = 'foot';
                        input.value = opt.value;
                        footHiddenInputsContainer.appendChild(input);
                    });
                }
            }

            // Formu Gönder
            const form = document.getElementById('filterForm');
            if (form) form.submit();
        });
    }

    // ============================================================
    // 5. DIŞARI TIKLAYINCA KAPATMA (GLOBAL)
    // ============================================================
    window.addEventListener('click', function(e) {
        // Age Dropdown Kapatma
        const ageDrop = document.getElementById('ageDropdown');
        const ageBtn = document.getElementById('ageDropdownBtn');
        if (ageDrop && ageBtn && !ageDrop.contains(e.target) && !ageBtn.contains(e.target)) {
            ageDrop.classList.remove('show');
        }

        // Foot Dropdown Kapatma
        const footDrop = document.getElementById('footDropdown');
        const footBtn = document.getElementById('footDropdownBtn');
        if (footDrop && footBtn && !footDrop.contains(e.target) && !footBtn.contains(e.target)) {
            footDrop.classList.remove('show');
        }
    });

});