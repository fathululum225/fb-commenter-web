let accountCounter = 0;
let currentJobId = null;
let autoScroll = true;
let eventSource = null;

// ============================================================
//  ACCOUNT MANAGEMENT
// ============================================================
function createAccountCard() {
    accountCounter++;
    const idx = accountCounter;

    const div = document.createElement("div");
    div.className = "account-card";
    div.dataset.accountId = idx;
    div.innerHTML = `
        <div class="account-header">
            <span class="account-title">👤 Akun ${idx}</span>
            <button type="button" class="remove-btn" onclick="removeAccount(${idx})">✕ Hapus</button>
        </div>
        <div class="form-group">
            <label>c_user</label>
            <input type="text" class="acc-c-user" placeholder="100012345678901">
        </div>
        <div class="form-group">
            <label>xs</label>
            <input type="text" class="acc-xs" placeholder="28%3Aabc...xyz">
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>datr (opsional)</label>
                <input type="text" class="acc-datr" placeholder="2lOVanNsXO...">
            </div>
            <div class="form-group">
                <label>fr (opsional)</label>
                <input type="text" class="acc-fr" placeholder="1tKAp54GHIE7...">
            </div>
        </div>
    `;
    document.getElementById("accounts-list").appendChild(div);
    renumberAccounts();
}

function removeAccount(id) {
    const cards = document.querySelectorAll(".account-card");
    if (cards.length <= 1) {
        alert("Minimal harus ada 1 akun");
        return;
    }
    const card = document.querySelector(`[data-account-id="${id}"]`);
    if (card) {
        card.remove();
        renumberAccounts();
    }
}

function renumberAccounts() {
    const cards = document.querySelectorAll(".account-card");
    cards.forEach((card, i) => {
        card.querySelector(".account-title").textContent = `👤 Akun ${i + 1}`;
    });
}

// ============================================================
//  FORM SUBMIT
// ============================================================
async function startJob() {
    const target = document.getElementById("target_username").value.trim().replace(/^@/, "");
    if (!target) {
        alert("Target username wajib diisi!");
        return;
    }

    const accounts = [];
    document.querySelectorAll(".account-card").forEach((card, i) => {
        const c_user = card.querySelector(".acc-c-user").value.trim();
        const xs = card.querySelector(".acc-xs").value.trim();
        const datr = card.querySelector(".acc-datr").value.trim();
        const fr = card.querySelector(".acc-fr").value.trim();

        if (c_user && xs) {
            accounts.push({
                name: `Akun-${i + 1}`,
                c_user: c_user,
                xs: xs,
                datr: datr,
                fr: fr,
            });
        }
    });

    if (accounts.length === 0) {
        alert("Minimal 1 akun harus diisi lengkap (c_user + xs)!");
        return;
    }

    const payload = {
        target_username: target,
        accounts: accounts,
        max_posts: parseInt(document.getElementById("max_posts").value) || 5,
        comments_per_post: parseInt(document.getElementById("comments_per_post").value) || 3,
        comment_delay_min: parseInt(document.getElementById("comment_delay_min").value) || 5,
        comment_delay_max: parseInt(document.getElementById("comment_delay_max").value) || 12,
        account_delay_min: parseInt(document.getElementById("account_delay_min").value) || 60,
        account_delay_max: parseInt(document.getElementById("account_delay_max").value) || 120,
        auto_like: document.getElementById("auto_like").checked,
        headless: true,
        scroll_count: 5,
    };

    const btn = document.getElementById("start-btn");
    btn.disabled = true;
    btn.textContent = "⏳ Mengirim...";

    try {
        const res = await fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!res.ok) {
            alert("Error: " + (data.error || "Gagal memulai job"));
            btn.disabled = false;
            btn.textContent = "🚀 Mulai Komentar";
            return;
        }

        currentJobId = data.job_id;
        showLogSection();
        connectSSE(currentJobId);
    } catch (e) {
        alert("Gagal terhubung ke server: " + e.message);
        btn.disabled = false;
        btn.textContent = "🚀 Mulai Komentar";
    }
}

// ============================================================
//  SSE LOG STREAMING
// ============================================================
function connectSSE(jobId) {
    if (eventSource) {
        eventSource.close();
    }

    const logEl = document.getElementById("log-output");
    logEl.textContent = "";
    setStatus("running");

    eventSource = new EventSource(`/api/logs/${jobId}`);

    eventSource.onmessage = (e) => {
        const msg = e.data;

        if (msg === "__END__") {
            eventSource.close();
            eventSource = null;
            setStatus("done");
            document.getElementById("start-btn").disabled = false;
            document.getElementById("start-btn").textContent = "🚀 Mulai Komentar";
            return;
        }

        const line = msg.replace(/\\n/g, "\n");
        logEl.textContent += line + "\n";

        if (autoScroll) {
            logEl.scrollTop = logEl.scrollHeight;
        }
    };

    eventSource.onerror = (e) => {
        console.error("SSE error", e);
        setStatus("error");
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }
    };
}

function setStatus(status) {
    const badge = document.getElementById("status-badge");
    badge.className = "status-badge " + status;
    const labels = { running: "Berjalan", done: "Selesai", error: "Error" };
    badge.textContent = labels[status] || status;
}

function showLogSection() {
    document.getElementById("log-section").classList.remove("hidden");
    document.getElementById("log-section").scrollIntoView({ behavior: "smooth" });
}

function newJob() {
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    document.getElementById("log-section").classList.add("hidden");
    document.getElementById("log-output").textContent = "";
    document.getElementById("start-btn").disabled = false;
    document.getElementById("start-btn").textContent = "🚀 Mulai Komentar";
}

// ============================================================
//  INIT
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
    createAccountCard();
    createAccountCard();

    document.getElementById("add-account").addEventListener("click", createAccountCard);
    document.getElementById("start-btn").addEventListener("click", startJob);
    document.getElementById("new-job").addEventListener("click", newJob);

    document.getElementById("stop-scroll").addEventListener("click", (e) => {
        autoScroll = !autoScroll;
        e.target.textContent = autoScroll ? "⏸️ Auto-scroll: ON" : "▶️ Auto-scroll: OFF";
    });
});