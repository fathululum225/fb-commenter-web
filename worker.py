#!/usr/bin/env python3
"""
Facebook Auto Commenter Worker
Dipanggil oleh Flask app untuk menjalankan komentar otomatis di Facebook Reels
"""

import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright

# ============================================================
#  BANK KOMENTAR
# ============================================================
COMMENT_BANK = [
    "Keren banget! 🔥", "Mantap jiwa!", "Bagus banget!", "Wah keren!",
    "Top banget!", "Gokil! 🔥", "Kece parah!", "Mantul!", "Sip banget!",
    "Oke banget!", "Cakep!", "Nais!", "Jos gandos!", "Solid! 💯",
    "Keren abis!", "Mantap pol!", "Gila sih ini 🔥", "Wah wah wah!",
    "Nice!", "Good!", "Top markotop!", "Keren cuy!", "Mantul bgt!",
    "Bagus bgt!", "Ciamik!", "Ngeri!", "Pro!", "Gass!", "Lanjut!",
    "Sip!", "Oke!", "Yes!", "Gas!", "Legit!", "Mantab!", "Joss!",
    "Terima kasih sharingnya!", "Makasih infonya!", "Berguna banget ini!",
    "Sangat bermanfaat!", "Nice share! 🙏", "Lanjutkan! 💪",
    "Semangat terus!", "Sukses selalu!", "Tetap berkarya!",
    "Jangan berhenti bikin konten!", "Thanks infonya bro!",
    "Bermanfaat banget buat aku!", "Ini yang aku cari!",
    "Baru tau ini, makasih!", "Info penting nih, thanks!",
    "Setuju banget!", "Bener banget sih ini!", "Nah ini dia!", "Fakta! 💯",
    "Real banget!", "Relate parah!", "Sama banget!", "Gue banget!",
    "This is me!", "Auto setuju!", "Setuju 100%!", "Bener bgt!",
    "Nah kan bener!", "Gue juga gitu!", "Sama dong!", "Akurat banget!",
    "Fakta lapangan!", "Real no fek!", "No debat!", "Fix bener!",
    "Boleh share lebih detail?", "Menarik nih, lanjut terus!",
    "Penasaran kelanjutannya!", "Tunggu part 2-nya!",
    "Bikin konten kayak gini terus ya!", "Suka sama konten beginian!",
    "Kontennya berbobot!", "Quality content! 👏", "Underrated banget ini!",
    "Wajib viral nih!", "Kenapa gak viral dari kemarin?",
    "Ini sih harusnya trending!", "Gimana kelanjutannya?",
    "Update terus ya min!", "Ada tips lain gak?",
    "Bikin senyum sendiri 😊", "Senyum-senyum sendiri baca ini",
    "Good vibes banget! ✨", "Bikin hari jadi lebih baik!",
    "Fresh banget infonya!", "Energi positif! 💫", "Hati jadi hangat! ❤️",
    "Legit banget!", "Gemas! 🥰", "Lucu banget! 😄",
    "Haha ngakak!", "Ketawa sendiri!", "Ngakak baca ini!",
    "Bikin nggak bisa berhenti senyum!", "Suasana hati membaik!",
    "Konten kayak gini yang gue tunggu-tunggu!",
    "Baru nemu akun sebagus ini, langsung follow!",
    "Kenapa baru nemu akun ini sekarang 😭",
    "Algoritma Facebook akhirnya nunjukin konten berkualitas!",
    "Ini nih yang namanya konten berbobot!",
    "Sumpah ya, kontennya selalu relatable!",
    "Nggak pernah nyesel follow akun ini!",
    "Selalu ditunggu konten barunya!",
    "Bahasanya enak dibaca, isinya berbobot!",
    "Ini sih wajib banget di-bookmark!",
    "Nggak pernah bosen baca kontennya!",
    "Sering-sering bikin konten kayak gini ya!",
    "Kontennya ngena banget di hati!",
    "Yang beginian nih yang aku butuhin!",
    "Suka banget sama gaya bahasanya!",
    "Wkwkwk gokil!", "Anjir keren!", "Gila gila gila!",
    "Edan sih ini!", "Bener-bener dah!", "Yakin deh ini bagus!",
    "Top dah pokoknya!", "Nice one!", "Good job! 👍", "Well done!",
    "Salam dari Indonesia! 🇮🇩", "Semangat dari sini! 💪",
    "Ditunggu konten selanjutnya ya!", "Keep up the good work!",
    "Sukses terus buat kamu!", "Semoga makin sukses!",
    "Sukses selalu ya min!", "Ditunggu update-nya!",
    "Salam satu hobi!", "Salam kenal dari aku!",
]


# ============================================================
#  UTIL
# ============================================================
def make_log(log_callback):
    def log(msg="", indent=0):
        log_callback("   " * indent + str(msg))
    return log


async def random_delay(min_sec, max_sec, label, log):
    delay = random.uniform(min_sec, max_sec)
    mins = int(delay // 60)
    secs = int(delay % 60)
    time_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"
    log(f"⏳ {label} menunggu {time_str}...", 1)
    await asyncio.sleep(delay)


# ============================================================
#  SETUP BROWSER
# ============================================================
async def setup_browser_for_account(playwright, account, headless, log):
    log(f"🌐 Membuka browser untuk {account['name']}...")

    browser = await playwright.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
        ]
    )

    context = await browser.new_context(
        viewport={"width": 1366, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        locale="id-ID",
        timezone_id="Asia/Jakarta",
    )

    cookies = [
        {"name": "c_user", "value": account["c_user"],
         "domain": ".facebook.com", "path": "/",
         "httpOnly": False, "secure": True},
        {"name": "xs", "value": account["xs"],
         "domain": ".facebook.com", "path": "/",
         "httpOnly": True, "secure": True},
    ]
    if account.get("datr"):
        cookies.append({"name": "datr", "value": account["datr"],
                        "domain": ".facebook.com", "path": "/",
                        "httpOnly": True, "secure": True})
    if account.get("fr"):
        cookies.append({"name": "fr", "value": account["fr"],
                        "domain": ".facebook.com", "path": "/",
                        "httpOnly": True, "secure": True})

    await context.add_cookies(cookies)
    page = await context.new_page()

    await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'languages', {get: () => ['id-ID', 'id', 'en-US']});
    """)

    return browser, context, page


# ============================================================
#  CHECK LOGIN
# ============================================================
async def check_login(page, account_name, log):
    log(f"🔐 [{account_name}] Memeriksa status login...")
    try:
        await page.goto("https://www.facebook.com/",
                        wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)

        # Cek redirect login
        if "login" in page.url.lower() or "checkpoint" in page.url.lower():
            log(f"❌ [{account_name}] Redirect login - cookie invalid")
            return False

        for sel in [
            '[aria-label="Facebook"]',
            '[role="navigation"]',
            'div[aria-label="Buat postingan"]',
            'div[aria-label="Create post"]',
        ]:
            try:
                await page.wait_for_selector(sel, timeout=5000, state="attached")
                log(f"✅ [{account_name}] Berhasil login!")
                return True
            except Exception:
                continue

        log(f"⚠️  [{account_name}] Tidak yakin login, coba lanjut...")
        return True
    except Exception as e:
        log(f"❌ [{account_name}] Gagal buka Facebook: {e}")
        return False


# ============================================================
#  KUMPULKAN LINK REEL
# ============================================================
async def collect_reel_links(page, username, max_links, scroll_count, log):
    log(f"📋 Mencari REELS di @{username}...")
    reel_links = set()

    urls_to_try = [
        f"https://www.facebook.com/{username}/reels_tab",
        f"https://www.facebook.com/{username}/videos",
        f"https://www.facebook.com/{username}",
    ]

    for target_url in urls_to_try:
        if len(reel_links) >= max_links:
            break

        log(f"   🔗 Coba: {target_url}", 1)
        try:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)

            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(1)
            except Exception:
                pass

            for i in range(scroll_count):
                await page.evaluate("window.scrollBy(0, window.innerHeight * 0.9)")
                await asyncio.sleep(2)

            links = await page.evaluate("""
                () => {
                    const anchors = document.querySelectorAll('a[href]');
                    const reels = new Set();
                    for (const a of anchors) {
                        const h = a.getAttribute('href');
                        if (!h) continue;
                        const match = h.match(/\\/reel\\/(\\d+)/);
                        if (match) {
                            reels.add('https://www.facebook.com/reel/' + match[1] + '/');
                        }
                    }
                    return Array.from(reels);
                }
            """)

            log(f"      Ditemukan {len(links)} link /reel/", 1)
            for l in links:
                reel_links.add(l)
                if len(reel_links) >= max_links:
                    break

        except Exception as e:
            log(f"      ❌ Gagal: {e}", 1)
            continue

    reel_links = list(reel_links)[:max_links]
    log(f"   ✅ Total {len(reel_links)} link reel", 1)
    return reel_links


# ============================================================
#  LIKE
# ============================================================
async def like_post(page, log):
    try:
        unlike = await page.query_selector(
            'div[aria-label="Unlike"], div[aria-label="Batal Suka"]'
        )
        if unlike:
            log("❤️  Sudah di-like", 1)
            return True

        for sel in ['div[aria-label="Like"]', 'div[aria-label="Suka"]']:
            try:
                btn = await page.query_selector(sel)
                if btn and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(1.5)
                    log("❤️  Like berhasil", 1)
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


# ============================================================
#  BUKA PANEL KOMENTAR
# ============================================================
async def open_comment_sidebar(page, log):
    log("   → Buka panel komentar...", 1)

    comment_btn_selectors = [
        'div[aria-label="Comment"]',
        'div[aria-label="Komentari"]',
        'div[aria-label="Beri komentar"]',
        'div[role="button"][aria-label*="Comment"]',
        'div[role="button"][aria-label*="Komentar"]',
        '[aria-label*="Comment" i][role="button"]',
        '[aria-label*="Komentar" i][role="button"]',
    ]

    for sel in comment_btn_selectors:
        try:
            btns = await page.query_selector_all(sel)
            for btn in btns:
                if await btn.is_visible():
                    await btn.click()
                    log("   ✅ Tombol komentar diklik", 1)
                    await asyncio.sleep(3)
                    return True
        except Exception:
            continue

    try:
        clicked = await page.evaluate("""
            () => {
                const candidates = document.querySelectorAll(
                    '[aria-label*="Comment" i], [aria-label*="Komentar" i]'
                );
                for (let el of candidates) {
                    if (el.offsetParent !== null) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        if clicked:
            log("   ✅ Tombol komentar diklik (JS)", 1)
            await asyncio.sleep(3)
            return True
    except Exception:
        pass

    log("   ⚠️  Tidak bisa buka panel komentar", 1)
    return False


# ============================================================
#  CARI KOTAK INPUT KOMENTAR
# ============================================================
async def find_comment_input(page):
    selectors = [
        'div[contenteditable="true"][role="textbox"][aria-label*="Comment as"]',
        'div[contenteditable="true"][role="textbox"][aria-label*="Komentar sebagai"]',
        'div[contenteditable="true"][role="textbox"][aria-label*="Write a comment"]',
        'div[contenteditable="true"][role="textbox"][aria-label*="Tulis komentar"]',
        'div[contenteditable="true"][role="textbox"][aria-label*="komentar" i]',
        'div[contenteditable="true"][role="textbox"][aria-label*="comment" i]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"]',
    ]
    exclude = ["cari", "search", "pesan", "message", "chat"]

    for sel in selectors:
        try:
            boxes = await page.query_selector_all(sel)
            for b in boxes:
                if not await b.is_visible():
                    continue
                aria = (await b.get_attribute("aria-label") or "").lower()
                if any(x in aria for x in exclude):
                    continue
                return b
        except Exception:
            continue
    return None


# ============================================================
#  KIRIM KOMENTAR
# ============================================================
async def send_comment(page, text, log):
    box = await find_comment_input(page)
    if not box:
        log("   ❌ Kotak komentar tidak ditemukan", 1)
        return False

    try:
        await page.evaluate("""(el) => {
            el.focus();
            const sel = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(el);
            sel.removeAllRanges();
            sel.addRange(range);
        }""", box)
        await asyncio.sleep(0.5)

        await page.keyboard.press("Control+A")
        await page.keyboard.press("Delete")
        await asyncio.sleep(0.3)

        await page.keyboard.type(text, delay=random.randint(40, 70))
        await asyncio.sleep(1.2)
        log(f"   📝 Diketik: \"{text[:40]}\"", 1)
    except Exception as e:
        log(f"   ❌ Gagal ketik: {e}", 1)
        return False

    try:
        await page.keyboard.press("Enter")
        await asyncio.sleep(3)
    except Exception as e:
        log(f"   ❌ Gagal Enter: {e}", 1)
        return False

    try:
        current = await page.evaluate(
            "(el) => el.innerText || el.textContent || ''", box
        )
        if not current or current.strip() == "":
            log("   ✅ Komentar TERKIRIM!", 1)
            return True
        else:
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
            current = await page.evaluate(
                "(el) => el.innerText || el.textContent || ''", box
            )
            if not current or current.strip() == "":
                log("   ✅ Komentar TERKIRIM!", 1)
                return True
            return False
    except Exception:
        return True


# ============================================================
#  PROSES SATU REEL
# ============================================================
async def process_reel(page, reel_url, num, total, comments_count, delays, log):
    log(f"\n{'='*50}")
    log(f"📌 REEL {num}/{total}")
    log(f"🔗 {reel_url}")
    log(f"{'='*50}")

    loaded = False
    for attempt in range(3):
        try:
            log(f"   🌐 Load (attempt {attempt+1}/3)...", 1)
            await page.goto(reel_url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(8)
            loaded = True
            break
        except Exception as e:
            log(f"   ⚠️  Timeout attempt {attempt+1}, retry...", 1)
            await asyncio.sleep(3)

    if not loaded:
        log("❌ Gagal load setelah 3x coba", 1)
        return 0

    if "login" in page.url.lower() or "checkpoint" in page.url.lower():
        log("❌ Redirect login", 1)
        return 0

    if delays.get("auto_like", True):
        await like_post(page, log)
        await asyncio.sleep(1)

    if not await open_comment_sidebar(page, log):
        log("⚠️  Panel komentar gagal dibuka", 1)

    await asyncio.sleep(2)

    used = set()
    sent = 0

    for i in range(comments_count):
        log(f"💭 Komentar {i+1}/{comments_count}", 1)

        pool = [c for c in COMMENT_BANK if c not in used]
        if not pool:
            used.clear()
            pool = COMMENT_BANK[:]

        text = random.choice(pool)
        used.add(text)

        box = await find_comment_input(page)
        if not box:
            log("   → Coba buka panel komentar lagi...", 1)
            await open_comment_sidebar(page, log)
            await asyncio.sleep(2)

        if await send_comment(page, text, log):
            sent += 1
        else:
            log("   ⚠️  Gagal kirim", 1)

        if i < comments_count - 1:
            await random_delay(delays["comment"][0], delays["comment"][1],
                               "antar komentar", log)

    log(f"📊 Reel {num}: {sent}/{comments_count} berhasil", 1)
    return sent


# ============================================================
#  PROSES SATU AKUN
# ============================================================
async def process_account(playwright, account, account_idx, total_accounts,
                          config, log):
    log(f"\n{'█'*50}")
    log(f"█  AKUN {account_idx}/{total_accounts}: {account['name']}")
    log(f"█  c_user: {account['c_user']}")
    log(f"{'█'*50}")

    if account_idx > 1:
        delay = random.uniform(15, 30)
        log(f"⏳ Warm-up {delay:.0f}s sebelum buka akun...", 1)
        await asyncio.sleep(delay)

    browser = None
    account_success = 0
    max_posts = config["max_posts"]
    comments_per_post = config["comments_per_post"]
    account_target = max_posts * comments_per_post
    delays = config["delays"]

    try:
        browser, context, page = await setup_browser_for_account(
            playwright, account, config["headless"], log
        )

        if not await check_login(page, account["name"], log):
            log(f"❌ [{account['name']}] Login gagal - skip akun ini")
            return 0, 0

        reel_links = await collect_reel_links(
            page, config["target_username"], max_posts,
            config.get("scroll_count", 5), log
        )
        if not reel_links:
            log(f"⚠️  [{account['name']}] Tidak ada reel ditemukan")
            return 0, 0

        log(f"✅ [{account['name']}] Siap memproses {len(reel_links)} reels")

        for i, url in enumerate(reel_links, 1):
            sent = await process_reel(
                page, url, i, len(reel_links), comments_per_post, delays, log
            )
            account_success += sent

            if i < len(reel_links):
                await random_delay(delays["reel"][0], delays["reel"][1],
                                   "antar reel", log)

        log(f"\n{'─'*50}")
        log(f"📊 [{account['name']}] SELESAI: {account_success}/{account_target}")
        log(f"{'─'*50}")

    except Exception as e:
        log(f"❌ [{account['name']}] Error: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        if browser:
            try:
                await browser.close()
                log(f"🔒 [{account['name']}] Browser ditutup", 1)
            except Exception:
                pass

    return account_success, account_target


# ============================================================
#  MAIN RUN JOB
# ============================================================
async def run_job(config, log_callback):
    """Entry point yang dipanggil dari Flask."""
    log = make_log(log_callback)

    log("=" * 55)
    log("  FACEBOOK AUTO COMMENTER")
    log("=" * 55)
    log(f"  Target        : {config['target_username']}")
    log(f"  Total akun    : {len(config['accounts'])}")
    log(f"  Reels/akun    : {config['max_posts']}")
    log(f"  Komentar/reel : {config['comments_per_post']}")
    log("")

    full_config = {
        "target_username": config["target_username"],
        "max_posts": config["max_posts"],
        "comments_per_post": config["comments_per_post"],
        "scroll_count": config.get("scroll_count", 5),
        "headless": config.get("headless", True),
        "delays": {
            "comment": (config.get("comment_delay_min", 5),
                        config.get("comment_delay_max", 12)),
            "reel": (config.get("reel_delay_min", 20),
                     config.get("reel_delay_max", 35)),
            "account": (config.get("account_delay_min", 60),
                        config.get("account_delay_max", 120)),
            "auto_like": config.get("auto_like", True),
        },
    }

    start_time = datetime.now()
    grand_total_success = 0
    grand_total_target = 0
    account_results = []

    async with async_playwright() as p:
        accounts = config["accounts"]
        for idx, account in enumerate(accounts, 1):
            success, target = await process_account(
                p, account, idx, len(accounts), full_config, log
            )
            grand_total_success += success
            grand_total_target += target
            account_results.append({
                "name": account["name"],
                "c_user": account["c_user"],
                "success": success,
                "target": target,
            })

            if idx < len(accounts):
                d = random.uniform(*full_config["delays"]["account"])
                log(f"\n{'█'*50}")
                log(f"█  JEDA ANTAR AKUN {d:.0f}s...")
                log(f"{'█'*50}")
                await asyncio.sleep(d)

    elapsed = (datetime.now() - start_time).total_seconds()
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    log("\n" + "█" * 50)
    log("█  📊 RINGKASAN AKHIR")
    log("█" * 50)

    for r in account_results:
        rate = (r["success"] / r["target"] * 100) if r["target"] > 0 else 0
        log(f"  {r['name']:10s} ({r['c_user']}): "
            f"{r['success']}/{r['target']} ({rate:.0f}%)")

    log("─" * 50)
    total_rate = (grand_total_success / grand_total_target * 100) if grand_total_target > 0 else 0
    log(f"  TOTAL      : {grand_total_success}/{grand_total_target} ({total_rate:.1f}%)")
    log(f"  Waktu      : {mins}m {secs}s")
    log("█" * 50)
    log("🎉 Selesai!")

    return {
        "total_success": grand_total_success,
        "total_target": grand_total_target,
        "elapsed_seconds": int(elapsed),
        "accounts": account_results,
    }