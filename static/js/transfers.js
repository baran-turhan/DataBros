function formatWithDots(value) {
    const digits = value.replace(/\D/g, "");
    if (!digits) return "";
    return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

function attachMoneyFormatter(id) {
    const el = document.getElementById(id);
    if (!el) return;
    // format existing value
    el.value = formatWithDots(el.value);
    el.addEventListener("input", () => {
        const before = el.value;
        const start = el.selectionStart || 0;
        const formatted = formatWithDots(before);
        el.value = formatted;
        const diff = formatted.length - before.length;
        const newPos = Math.max(0, start + diff);
        el.setSelectionRange(newPos, newPos);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    attachMoneyFormatter("min_fee");
    attachMoneyFormatter("max_fee");

    const modal = document.getElementById("transfer-edit-modal");
    const form = document.getElementById("transfer-edit-form");
    const closeBtn = document.getElementById("transfer-edit-close");
    const cancelBtn = document.getElementById("transfer-edit-cancel");
    const deleteBtn = document.getElementById("transfer-delete-btn");
    const saveBtn = document.getElementById("transfer-edit-save");
    const errorBox = document.getElementById("transfer-edit-error");
    const editButtons = Array.from(document.querySelectorAll(".edit-btn"));
    const fromClubField = document.getElementById("transfer-from-club");
    const toClubField = document.getElementById("transfer-to-club");
    const transferFeeField = document.getElementById("transfer-fee");
    const transferValueField = document.getElementById("transfer-value");
    let currentTransferId = null;

    const setError = (msg) => {
        if (!errorBox) return;
        if (msg) {
            errorBox.textContent = msg;
            errorBox.style.display = "block";
        } else {
            errorBox.textContent = "";
            errorBox.style.display = "none";
        }
    };

    const setLoading = (btn, isLoading) => {
        if (!btn) return;
        if (isLoading) {
            btn.classList.add("loading");
        } else {
            btn.classList.remove("loading");
        }
        btn.disabled = !!isLoading;
    };

    const fillField = (field, value) => {
        if (!field) return;
        field.value = value || "";
    };

    const openModal = (btn) => {
        if (!modal || !btn) return;
        currentTransferId = btn.dataset.transferId;
        fillField(fromClubField, btn.dataset.fromClubId);
        fillField(toClubField, btn.dataset.toClubId);
        fillField(transferFeeField, btn.dataset.transferFee);
        fillField(transferValueField, btn.dataset.marketValue);
        setError("");
        modal.classList.add("active");
        modal.setAttribute("aria-hidden", "false");
    };

    const closeModal = () => {
        if (!modal) return;
        currentTransferId = null;
        form?.reset();
        setError("");
        modal.classList.remove("active");
        modal.setAttribute("aria-hidden", "true");
    };

    editButtons.forEach((btn) => {
        btn.addEventListener("click", () => openModal(btn));
    });

    closeBtn?.addEventListener("click", closeModal);
    cancelBtn?.addEventListener("click", closeModal);
    modal?.addEventListener("click", (event) => {
        if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal?.classList.contains("active")) {
            closeModal();
        }
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!currentTransferId) return;
        setError("");
        setLoading(saveBtn, true);
        deleteBtn?.setAttribute("disabled", "true");
        cancelBtn?.setAttribute("disabled", "true");

        const payload = {
            from_club_id: fromClubField?.value || null,
            to_club_id: toClubField?.value || null,
            transfer_fee: transferFeeField?.value || null,
            market_value_in_eur: transferValueField?.value || null,
        };

        try {
            const response = await fetch(`/transfers/${currentTransferId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                setError(data.message || "Update failed. Please check the fields.");
            } else {
                window.location.reload();
            }
        } catch (err) {
            setError("Network error. Please try again.");
        } finally {
            setLoading(saveBtn, false);
            deleteBtn?.removeAttribute("disabled");
            cancelBtn?.removeAttribute("disabled");
        }
    });

    deleteBtn?.addEventListener("click", async () => {
        if (!currentTransferId) return;
        const confirmed = window.confirm("Are you sure?");
        if (!confirmed) return;
        setError("");
        setLoading(deleteBtn, true);
        saveBtn?.setAttribute("disabled", "true");
        cancelBtn?.setAttribute("disabled", "true");

        try {
            const response = await fetch(`/transfers/${currentTransferId}`, {
                method: "DELETE",
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                setError(data.message || "Delete failed.");
            } else {
                window.location.reload();
            }
        } catch (err) {
            setError("Network error. Please try again.");
        } finally {
            setLoading(deleteBtn, false);
            saveBtn?.removeAttribute("disabled");
            cancelBtn?.removeAttribute("disabled");
        }
    });
});
