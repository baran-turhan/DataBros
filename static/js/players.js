document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // 1. ARAMA (SEARCH BAR) MANTIĞI - SERVER SIDE
    // ============================================================
    const searchInput = document.getElementById('searchInput');
    const inputSearch = document.getElementById('inputSearch');
    const filterForm = document.getElementById('filterForm');

    // Debounce Timer: Kullanıcı her harfe bastığında değil, 
    // yazmayı bitirdikten 600ms sonra arama yapsın.
    let typingTimer;
    const doneTypingInterval = 600; // ms

    if (searchInput) {
        // Kullanıcı yazarken sayacı sıfırla
        searchInput.addEventListener('input', function() {
            clearTimeout(typingTimer);
            typingTimer = setTimeout(performSearch, doneTypingInterval);
        });

        // Enter'a basarsa hemen ara
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                clearTimeout(typingTimer);
                performSearch();
            }
        });
    }

    function performSearch() {
        // 1. Search değerini gizli forma aktar
        if (inputSearch && searchInput) {
            inputSearch.value = searchInput.value;
        }
        
        // 2. Foot ve Position verilerini hidden inputlara doldur (yardımcı fonk.)
        refreshHiddenInputs();

        // 3. Formu gönder (Sayfa yenilenecek ve veritabanından veri gelecek)
        if (filterForm) {
            filterForm.submit();
        }
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
    // 4. POZİSYON FİLTRESİ (POSITION) MANTIĞI (YENİ)
    // ============================================================
    const posDropdownBtn = document.getElementById('posDropdownBtn');
    const posDropdown = document.getElementById('posDropdown');
    const posAllCheckbox = document.getElementById('posAll');
    const posOptions = document.querySelectorAll('.pos-option');
    const posButtonLabel = document.getElementById('posButtonLabel');
    const posHiddenInputsContainer = document.getElementById('posHiddenInputs');

    // Başlangıç Etiketi Güncelle
    // (HTML tarafında 'checked' geldiği için sadece etiketi düzeltmemiz yeterli)
    if (posOptions.length > 0) {
        checkPosAllStatus();
        updatePosLabel();
    }

    // Dropdown Aç/Kapa
    if (posDropdownBtn) {
        posDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            posDropdown.classList.toggle('show');
            // Diğerleri açıksa kapat
            if(document.getElementById('ageDropdown')) document.getElementById('ageDropdown').classList.remove('show');
            if(document.getElementById('footDropdown')) document.getElementById('footDropdown').classList.remove('show');
        });
    }

    // "All" Mantığı
    if (posAllCheckbox) {
        posAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            posOptions.forEach(opt => opt.checked = isChecked);
            updatePosLabel();
        });
    }

    // Tekil Seçim Mantığı
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
            // Sadece 1 tane seçiliyse ismini yaz
            posButtonLabel.innerText = checkedOpts[0].value;
        } else {
            // Birden fazla ise sayı göster (Çok uzun olmasın diye)
            posButtonLabel.innerText = `${checkedOpts.length} Selected`;
        }
    }

    // ============================================================
    // 5. APPLY FILTER VE DIŞARI TIKLAMA (GÜNCELLENMİŞ)
    // ============================================================
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            // A) Foot Verilerini Hazırla
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

            // B) Position Verilerini Hazırla (YENİ)
            if (posHiddenInputsContainer) {
                posHiddenInputsContainer.innerHTML = '';
                if (posAllCheckbox && !posAllCheckbox.checked) {
                    Array.from(document.querySelectorAll('.pos-option'))
                        .filter(opt => opt.checked)
                        .forEach(opt => {
                            const input = document.createElement('input');
                            input.type = 'hidden';
                            input.name = 'position'; // name='position' olmalı
                            input.value = opt.value;
                            posHiddenInputsContainer.appendChild(input);
                        });
                }
            }

            // Formu Gönder
            const form = document.getElementById('filterForm');
            if (form) form.submit();
        });
    }

    // Dışarı tıklayınca kapatma (Global)
    window.addEventListener('click', function(e) {
        const dropdowns = [
            {box: document.getElementById('ageDropdown'), btn: document.getElementById('ageDropdownBtn')},
            {box: document.getElementById('footDropdown'), btn: document.getElementById('footDropdownBtn')},
            {box: document.getElementById('posDropdown'), btn: document.getElementById('posDropdownBtn')} // Yeni eklendi
        ];

        dropdowns.forEach(item => {
            if (item.box && item.btn && !item.box.contains(e.target) && !item.btn.contains(e.target)) {
                item.box.classList.remove('show');
            }
        });
    });

    // ============================================================
    // 6. DIŞARI TIKLAYINCA KAPATMA (GLOBAL)
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

    // ============================================================
    // 7. SIRALAMA (SORTING) MANTIĞI 
    // ============================================================
    const sortDropdownBtn = document.getElementById('sortDropdownBtn');
    const sortDropdown = document.getElementById('sortDropdown');
    const sortItems = document.querySelectorAll('.sort-item');
    const sortButtonLabel = document.getElementById('sortButtonLabel');
    const inputSort = document.getElementById('inputSort');

    // Başlangıç Etiketini Ayarla
    if (inputSort && inputSort.value) {
        // Mevcut değere sahip item'ı bul ve etiketini al
        const currentItem = Array.from(sortItems).find(item => item.getAttribute('data-value') === inputSort.value);
        if (currentItem) {
            sortButtonLabel.innerText = currentItem.getAttribute('data-label');
            // Seçili olana görsel bir stil ekleyebiliriz
            currentItem.style.backgroundColor = '#f0f4f8';
            currentItem.style.fontWeight = 'bold';
        }
    }

    // Dropdown Aç/Kapa
    if (sortDropdownBtn) {
        sortDropdownBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            sortDropdown.classList.toggle('show');
            // Diğerleri açıksa kapat
            if(document.getElementById('ageDropdown')) document.getElementById('ageDropdown').classList.remove('show');
            if(document.getElementById('footDropdown')) document.getElementById('footDropdown').classList.remove('show');
            if(document.getElementById('posDropdown')) document.getElementById('posDropdown').classList.remove('show');
        });
    }

    // Sıralama Seçimi
    sortItems.forEach(item => {
        item.addEventListener('click', function() {
            const value = this.getAttribute('data-value');
            
            // Input'u güncelle
            if (inputSort) inputSort.value = value;
            
            // Formu hemen gönder (Sıralama genelde anlık olur)
            // Ancak Apply Filter ile entegre olsun dersen burayı yorum satırı yapıp
            // Apply butonuna basılmasını bekleyebilirsin.
            // Kullanıcı deneyimi için sıralamanın hemen çalışması daha iyidir:
            
            // Foot ve Position verilerini hidden inputlara doldur (Form submit öncesi)
            // (Aşağıdaki kod applyBtn logic'inin aynısıdır, formu göndermeden önce verileri tazeler)
            refreshHiddenInputs(); 
            
            document.getElementById('filterForm').submit();
        });
    });

    // Yardımcı Fonksiyon: Formu göndermeden önce checkbox verilerini hidden inputlara doldurur
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

    // Dışarı tıklama olayına Sort dropdown'ı da ekle
    window.addEventListener('click', function(e) {
        // ... (Eski kodlar) ...
        const sortDrop = document.getElementById('sortDropdown');
        const sortBtn = document.getElementById('sortDropdownBtn');
        if (sortDrop && sortBtn && !sortDrop.contains(e.target) && !sortBtn.contains(e.target)) {
            sortDrop.classList.remove('show');
        }
    });

});
