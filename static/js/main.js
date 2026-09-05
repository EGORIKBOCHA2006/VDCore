document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form.task-form");
    if (!form) return;

    const submitBtn = form.querySelector("button[type=submit]");
    const startInput = form.querySelector("#id_start_id");
    const endInput = form.querySelector("#id_end_id");

    function validateRange() {
        if (!startInput || !endInput) return true;
        const start = parseInt(startInput.value, 10);
        const end = parseInt(endInput.value, 10);
        if (isNaN(start) || isNaN(end)) return true;
        return start <= end;
    }

    function updateHint() {
        let hint = form.querySelector(".range-hint");
        if (!hint) {
            hint = document.createElement("div");
            hint.className = "hint range-hint";
            endInput.closest("p").appendChild(hint);
        }
        if (!validateRange()) {
            hint.textContent = "Начальный ID должен быть меньше или равен конечному";
            hint.style.color = "#ff8f8f";
        } else if (startInput.value && endInput.value) {
            const total = parseInt(endInput.value, 10) - parseInt(startInput.value, 10) + 1;
            hint.textContent = `Диапазон: ${total} записей, будет разбит на 3 чанка`;
            hint.style.color = "#6b7280";
        } else {
            hint.textContent = "";
        }
    }

    [startInput, endInput].forEach((el) => {
        if (el) el.addEventListener("input", updateHint);
    });

    form.addEventListener("submit", (e) => {
        if (!validateRange()) {
            e.preventDefault();
            return;
        }
        submitBtn.disabled = true;
        submitBtn.textContent = "Отправка...";
    });
});