document.addEventListener("DOMContentLoaded", () => {
	        const cards = document.querySelectorAll(".club-card[data-club-id]");
	        const cache = new Map();

	        const overlay = document.getElementById("clubEditOverlay");
	        const closeBtn = document.getElementById("clubEditClose");
	        const titleEl = document.getElementById("clubEditTitle");
	        const errorEl = document.getElementById("clubEditError");
	        const formEl = document.getElementById("clubEditForm");
	        const fieldsEl = document.getElementById("clubEditFields");
	        const deleteBtn = document.getElementById("clubEditDelete");

	        let activeClubId = null;
	        const UPDATE_PASSWORD = "1923";

	        const showEditError = (msg) => {
	            errorEl.textContent = msg || "Error";
	            errorEl.style.display = "block";
	        };

	        const clearEditError = () => {
	            errorEl.textContent = "";
	            errorEl.style.display = "none";
	        };

	        const verifyUpdatePassword = () => {
	            const entered = window.prompt("Update password:");
	            if (entered === null) return false;
	            if (entered !== UPDATE_PASSWORD) {
	                window.alert("Incorrect password.");
	                return false;
	            }
	            return true;
	        };

	        const closeModal = () => {
	            overlay.hidden = true;
	            activeClubId = null;
	            fieldsEl.innerHTML = "";
	            clearEditError();
	        };

	        const inferInput = (colType) => {
	            const t = (colType || "").toLowerCase();
	            if (t.includes("integer")) return { type: "number", step: "1" };
	            if (t.includes("real") || t.includes("double") || t.includes("numeric") || t.includes("decimal")) {
	                return { type: "number", step: "any" };
	            }
	            if (t.includes("date")) return { type: "date" };
	            return { type: "text" };
	        };

	        const openModal = async (clubId) => {
	            activeClubId = clubId;
	            overlay.hidden = false;
	            fieldsEl.innerHTML = "";
	            clearEditError();
	            titleEl.textContent = `Edit Club #${clubId}`;

	            try {
	                const res = await fetch(`/api/clubs/${encodeURIComponent(clubId)}`);
	                if (!res.ok) throw new Error("Details not received.");
	                const data = await res.json();

	                const club = data.club || {};
	                const schema = data.schema || {};
	                const cols = schema.columns || [];
	                const editable = new Set(["name", "stadium_name", "stadium_seats"]);

	                cols.forEach((c) => {
	                    const name = c.name;
	                    if (!editable.has(name)) return;
	                    const field = document.createElement("div");
	                    field.className = "club-edit-field";

	                    const label = document.createElement("label");
	                    if (name === "name") label.textContent = "name";
	                    else if (name === "stadium_name") label.textContent = "stadium_name";
	                    else if (name === "stadium_seats") label.textContent = "stadium_seats";
	                    else label.textContent = name;
	                    label.htmlFor = `club-edit-${name}`;
	                    field.appendChild(label);

	                    const meta = inferInput(c.type);
	                    const input = document.createElement("input");
	                    input.id = `club-edit-${name}`;
	                    input.name = name;
	                    input.type = meta.type;
	                    if (meta.step) input.step = meta.step;
	                    input.value = club[name] == null ? "" : String(club[name]);

	                    field.appendChild(input);
	                    fieldsEl.appendChild(field);
	                });
	            } catch (e) {
	                console.error("Edit modal load failed:", e);
	                showEditError("Could not load club details.");
	            }
	        };

        // Capture all player links at the document level (event delegation) - run first
        document.addEventListener("click", (event) => {
            // If the link itself or any inner element is clicked
            const playerLink = event.target.closest("a.player-name-link");
            if (playerLink) {
                console.log("Player link clicked:", playerLink.href); // Debug only
                event.preventDefault();
                event.stopPropagation();
                event.stopImmediatePropagation();
                const href = playerLink.getAttribute("href");
                if (href) {
                    window.location.href = href;
                }
                return false;
            }
        }, true); // Capture phase - runs first

        const createBackButton = (slotEl) => {
            const backBtn = document.createElement("button");
            backBtn.className = "players-back-btn";
            backBtn.textContent = "Back to list";
            backBtn.type = "button";
            backBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const card = slotEl.closest(".club-card");
                if (card) {
                    slotEl.innerHTML = "";
                    slotEl.dataset.open = "false";
                    card.classList.remove("expanded");
                }
            });
            return backBtn;
        };

        const renderPlayers = (slotEl, players) => {
            if (!players || players.length === 0) {
                const panel = document.createElement("div");
                panel.className = "club-players-panel";
                
                const backBtn = createBackButton(slotEl);
                panel.appendChild(backBtn);
                
                const emptyMsg = document.createElement("div");
                emptyMsg.className = "players-empty";
                emptyMsg.textContent = "No players found for this club.";
                panel.appendChild(emptyMsg);
                
                slotEl.innerHTML = "";
                slotEl.appendChild(panel);
                return;
            }

            // Build players using the DOM API (instead of innerHTML)
            const panel = document.createElement("div");
            panel.className = "club-players-panel";

                // Back button
            const backBtn = createBackButton(slotEl);
            panel.appendChild(backBtn);

            const header = document.createElement("div");
            header.className = "players-header";
            const headerTitle = document.createElement("div");
            headerTitle.textContent = "Squad";
            const headerCount = document.createElement("span");
            headerCount.textContent = `${players.length} players`;
            header.appendChild(headerTitle);
            header.appendChild(headerCount);
            panel.appendChild(header);

            const searchRow = document.createElement("div");
            searchRow.className = "players-search";

            const searchInput = document.createElement("input");
            searchInput.type = "search";
            searchInput.placeholder = "Oyuncu ara (isim, pozisyon, ülke)...";
            searchInput.autocomplete = "off";
            searchInput.spellcheck = false;
            searchRow.appendChild(searchInput);

            const clearBtn = document.createElement("button");
            clearBtn.type = "button";
            clearBtn.textContent = "Temizle";
            clearBtn.disabled = true;
            searchRow.appendChild(clearBtn);

            panel.appendChild(searchRow);

            const playersList = document.createElement("div");
            playersList.className = "players-list";

            let topValue = 0;
            let topPlayerName = null;
            players.forEach((p) => {
                const v = Number(p.market_value_in_eur);
                if (!Number.isFinite(v) || v <= 0) return;
                if (v > topValue) {
                    topValue = v;
                    topPlayerName = p && p.name ? String(p.name) : null;
                }
            });

            const formatEur = (val) => {
                const n = Number(val);
                if (!Number.isFinite(n) || n <= 0) return null;
                return `${new Intl.NumberFormat("en-US").format(Math.round(n))} EUR`;
            };

            if (topPlayerName && topValue > 0) {
                const mvpRow = document.createElement("div");
                mvpRow.className = "players-mvp";

                const label = document.createElement("span");
                label.className = "players-mvp-label";
                label.textContent = "Most Valuable Player:";
                mvpRow.appendChild(label);

                const nameEl = document.createElement("span");
                nameEl.className = "players-mvp-name";
                nameEl.textContent = topPlayerName;
                mvpRow.appendChild(nameEl);

                const valueLabel = formatEur(topValue);
                if (valueLabel) {
                    const valueEl = document.createElement("span");
                    valueEl.className = "players-mvp-value";
                    valueEl.textContent = `(${valueLabel})`;
                    mvpRow.appendChild(valueEl);
                }

                panel.insertBefore(mvpRow, header);
            }

            const appendPlayerRow = (listEl, p, index) => {
                const metaParts = [];
                if (p.age) metaParts.push(`${p.age} yrs`);
                if (p.sub_position) metaParts.push(p.sub_position);
                if (p.country_of_citizenship) metaParts.push(p.country_of_citizenship);
                const meta = metaParts.join(" | ") || "No info";

                const heightVal = typeof p.height_in_cm === "number" ? Math.round(p.height_in_cm) : null;

                const playerRow = document.createElement("div");
                playerRow.className = "player-row";
                if (index === 0) {
                    playerRow.style.marginTop = "0";
                    playerRow.style.paddingTop = "16px";
                }

                const playerMain = document.createElement("div");
                playerMain.className = "player-main";

                if (p.name) {
                    const playerLink = document.createElement("a");
                    playerLink.className = "player-name player-name-link";
                    playerLink.href = `/players?search=${encodeURIComponent(p.name)}`;
                    playerLink.textContent = p.name;
                    playerMain.appendChild(playerLink);
                } else {
                    const playerSpan = document.createElement("span");
                    playerSpan.className = "player-name";
                    playerSpan.style.cssText = "font-weight: 800; color: #0f172a;";
                    playerSpan.textContent = "Unknown Player";
                    playerMain.appendChild(playerSpan);
                }

                const playerMeta = document.createElement("div");
                playerMeta.className = "player-meta";
                playerMeta.textContent = meta;
                playerMain.appendChild(playerMeta);

                playerRow.appendChild(playerMain);

                const playerTags = document.createElement("div");
                playerTags.className = "player-tags";
                if (heightVal) {
                    const heightBadge = document.createElement("span");
                    heightBadge.className = "player-badge";
                    heightBadge.textContent = `${heightVal} cm`;
                    playerTags.appendChild(heightBadge);
                }
                if (p.foot) {
                    const footBadge = document.createElement("span");
                    footBadge.className = "player-badge";
                    footBadge.textContent = p.foot;
                    playerTags.appendChild(footBadge);
                }
                const mvLabel = formatEur(p.market_value_in_eur);
                if (mvLabel) {
                    const mvBadge = document.createElement("span");
                    mvBadge.className = "player-badge";
                    mvBadge.textContent = mvLabel;
                    playerTags.appendChild(mvBadge);

                    const mvNum = Number(p.market_value_in_eur);
                    if (topValue > 0 && Number.isFinite(mvNum) && mvNum === topValue) {
                        const topBadge = document.createElement("span");
                        topBadge.className = "player-badge";
                        topBadge.textContent = "Top Value";
                        playerTags.appendChild(topBadge);
                    }
                }
                playerRow.appendChild(playerTags);

                listEl.appendChild(playerRow);
            };

            const updateHeaderCount = (filteredCount) => {
                if (filteredCount === players.length) {
                    headerCount.textContent = `${players.length} players`;
                } else {
                    headerCount.textContent = `${filteredCount} / ${players.length} players`;
                }
            };

            const renderList = (filtered) => {
                playersList.innerHTML = "";
                updateHeaderCount(filtered.length);

                if (!filtered || filtered.length === 0) {
                    const empty = document.createElement("div");
                    empty.className = "players-empty";
                    empty.textContent = "Aramanıza uygun oyuncu bulunamadı.";
                    playersList.appendChild(empty);
                    return;
                }

                filtered.forEach((p, index) => appendPlayerRow(playersList, p, index));
            };

            const normalize = (v) => (v == null ? "" : String(v)).toLowerCase();
            const filterPlayers = (query) => {
                const q = normalize(query).trim();
                if (!q) return players;
                return players.filter((p) => {
                    const hay = [
                        normalize(p && p.name),
                        normalize(p && p.sub_position),
                        normalize(p && p.country_of_citizenship),
                    ].join(" ");
                    return hay.includes(q);
                });
            };

            const applySearch = () => {
                const q = searchInput.value || "";
                clearBtn.disabled = q.trim().length === 0;
                renderList(filterPlayers(q));
            };

            searchInput.addEventListener("input", applySearch);
            clearBtn.addEventListener("click", () => {
                searchInput.value = "";
                searchInput.focus();
                applySearch();
            });

            renderList(players);

            panel.appendChild(playersList);
            slotEl.innerHTML = "";
            slotEl.appendChild(panel);
        };

        const createBackButton_DUPLICATE = (slotEl) => {
            const backBtn = document.createElement("button");
            backBtn.className = "players-back-btn";
            backBtn.textContent = "Back to list";
            backBtn.type = "button";
            backBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                const card = slotEl.closest(".club-card");
                if (card) {
                    slotEl.innerHTML = "";
                    slotEl.dataset.open = "false";
                    card.classList.remove("expanded");
                }
            });
            return backBtn;
        };

        const showLoading = (slotEl) => {
            const panel = document.createElement("div");
            panel.className = "club-players-panel";
            
            const backBtn = createBackButton(slotEl);
            panel.appendChild(backBtn);
            
            const loadingMsg = document.createElement("div");
            loadingMsg.className = "players-loading";
            loadingMsg.textContent = "Loading squad...";
            panel.appendChild(loadingMsg);
            
            slotEl.innerHTML = "";
            slotEl.appendChild(panel);
        };

        const showError = (slotEl) => {
            const panel = document.createElement("div");
            panel.className = "club-players-panel";
            
            const backBtn = createBackButton(slotEl);
            panel.appendChild(backBtn);
            
            const errorMsg = document.createElement("div");
            errorMsg.className = "players-error";
            errorMsg.textContent = "Error loading squad.";
            panel.appendChild(errorMsg);
            
            slotEl.innerHTML = "";
            slotEl.appendChild(panel);
        };

	        cards.forEach((card) => {
	            const editBtn = card.querySelector(".club-edit-btn");
	            if (editBtn) {
	                editBtn.addEventListener("click", (e) => {
	                    e.preventDefault();
	                    e.stopPropagation();
	                    const clubId = card.dataset.clubId;
	                    if (!verifyUpdatePassword()) return;
	                    if (clubId) openModal(clubId);
	                });
	            }

            card.addEventListener("click", async (event) => {
                if (event.target.closest(".club-edit-btn")) {
                    return;
                }
                // First: if a player link is clicked, do nothing
                if (event.target.closest("a.player-name-link") || event.target.closest(".player-name-link")) {
                    return; // Event delegation already handles it
                }

                // Ignore other clicks inside the players panel (except the back button)
                if (event.target.closest(".club-players-panel") && !event.target.closest(".players-back-btn")) {
                    return;
                }
                
                // Back button already has its own handler
                if (event.target.closest(".players-back-btn")) {
                    return;
                }

                const slotEl = card.querySelector(".club-players-slot");
                if (!slotEl) return;

                const isOpen = slotEl.dataset.open === "true";
                if (isOpen) {
                    slotEl.innerHTML = "";
                    slotEl.dataset.open = "false";
                    card.classList.remove("expanded");
                    return;
                }

                const clubId = card.dataset.clubId;
                if (!clubId) return;

                slotEl.dataset.open = "true";
                card.classList.add("expanded");
                showLoading(slotEl);

                try {
                    let players = cache.get(clubId);
                    if (!players) {
                        const response = await fetch(`/clubs/${encodeURIComponent(clubId)}/players`);
                        if (!response.ok) {
                            throw new Error("No response received.");
                        }
                        const data = await response.json();
                        players = data.players || [];
                        cache.set(clubId, players);
                    }

                    const rosterCountRaw = card.dataset.rosterPlayerCount;
                    const squadSizeRaw = card.dataset.squadSize;
                    const rosterCount = rosterCountRaw === "" ? null : Number(rosterCountRaw);
                    const squadSize = squadSizeRaw === "" ? null : Number(squadSizeRaw);
                    if (Number.isFinite(rosterCount) && rosterCount !== players.length) {
                        console.warn(
                            "Roster count mismatch for club",
                            clubId,
                            { rosterCount, apiPlayers: players.length, squadSize }
                        );
                    }
                    renderPlayers(slotEl, players);
                } catch (error) {
                    console.error("Club squad could not be loaded:", error);
                    showError(slotEl);
                }
            });
        });

        overlay.addEventListener("click", (e) => {
            if (e.target === overlay) closeModal();
        });

        closeBtn.addEventListener("click", (e) => {
            e.preventDefault();
            closeModal();
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && !overlay.hidden) closeModal();
        });

        formEl.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!activeClubId) return;
            clearEditError();

            const values = {};
            const inputs = fieldsEl.querySelectorAll("input[name]");
            inputs.forEach((inp) => {
                if (inp.disabled) return;
                values[inp.name] = inp.value;
            });

            try {
                const res = await fetch(`/api/clubs/${encodeURIComponent(activeClubId)}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ values }),
                });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.error || "Update failed");
                window.location.reload();
            } catch (err) {
                console.error("Club update failed:", err);
                showEditError("Update failed: " + (err.message || ""));
            }
        });

        deleteBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            if (!activeClubId) return;
            clearEditError();

            const ok = confirm("Are you sure ?");
            if (!ok) return;

            try {
                const res = await fetch(`/api/clubs/${encodeURIComponent(activeClubId)}`, { method: "DELETE" });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.error || "Delete failed");

                const selector = `.club-card[data-club-id="${CSS.escape(String(activeClubId))}"]`;
                const card = document.querySelector(selector);
                if (card) card.remove();
                closeModal();
            } catch (err) {
                console.error("Club delete failed:", err);
                showEditError("Delete failed: " + (err.message || ""));
            }
        });
    });
