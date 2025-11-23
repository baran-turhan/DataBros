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
});
