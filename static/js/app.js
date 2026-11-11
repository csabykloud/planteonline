/**
 * PlanteOnline.ro - Modern Interactive Client Scripts
 */

// Global Touch Swipe Helper for Mobile Gestures
function setupTouchSwipe(element, onSwipeLeft, onSwipeRight) {
    if (!element) return;
    let touchStartX = 0;
    let touchStartY = 0;
    let touchEndX = 0;
    let touchEndY = 0;

    element.addEventListener('touchstart', (e) => {
        if (!e.touches || e.touches.length === 0) return;
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
    }, { passive: true });

    element.addEventListener('touchend', (e) => {
        if (!e.changedTouches || e.changedTouches.length === 0) return;
        touchEndX = e.changedTouches[0].clientX;
        touchEndY = e.changedTouches[0].clientY;
        const deltaX = touchEndX - touchStartX;
        const deltaY = touchEndY - touchStartY;
        // Require horizontal motion > 40px and dominant over vertical scroll
        if (Math.abs(deltaX) > 40 && Math.abs(deltaX) > Math.abs(deltaY)) {
            if (deltaX < 0) {
                if (typeof onSwipeLeft === 'function') onSwipeLeft();
            } else {
                if (typeof onSwipeRight === 'function') onSwipeRight();
            }
        }
    }, { passive: true });
}

// Mobile Navigation Toggle & Drawer Controller
document.addEventListener('DOMContentLoaded', () => {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    const menuBackdrop = document.getElementById('mobile-menu-backdrop');
    const menuIcon = document.getElementById('mobile-menu-icon');

    function toggleMobileMenu(forceClose = false) {
        if (!mobileMenu) return;
        const isOpen = !mobileMenu.classList.contains('hidden');
        if (isOpen || forceClose) {
            mobileMenu.classList.add('hidden');
            if (menuBackdrop) menuBackdrop.classList.add('hidden');
            if (menuBtn) menuBtn.setAttribute('aria-expanded', 'false');
            document.body.style.overflow = '';
            if (menuIcon) {
                menuIcon.setAttribute('data-lucide', 'menu');
                if (window.lucide) window.lucide.createIcons();
            }
        } else {
            mobileMenu.classList.remove('hidden');
            if (menuBackdrop) menuBackdrop.classList.remove('hidden');
            if (menuBtn) menuBtn.setAttribute('aria-expanded', 'true');
            document.body.style.overflow = 'hidden';
            if (menuIcon) {
                menuIcon.setAttribute('data-lucide', 'x');
                if (window.lucide) window.lucide.createIcons();
            }
        }
    }

    // Close mobile menu on Escape key or window resize to desktop
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && mobileMenu && !mobileMenu.classList.contains('hidden')) {
            toggleMobileMenu(true);
        }
    });
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 1024 && mobileMenu && !mobileMenu.classList.contains('hidden')) {
            toggleMobileMenu(true);
        }
    }, { passive: true });

    if (menuBtn) {
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleMobileMenu();
        });
    }

    if (menuBackdrop) {
        menuBackdrop.addEventListener('click', () => toggleMobileMenu(true));
    }

    if (mobileMenu) {
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => toggleMobileMenu(true));
        });
    }

    // Floating Back to Top Button Listener
    const bttBtn = document.getElementById('back-to-top-btn');
    if (bttBtn) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                bttBtn.classList.remove('opacity-0', 'pointer-events-none');
                bttBtn.classList.add('opacity-100', 'pointer-events-auto');
            } else {
                bttBtn.classList.add('opacity-0', 'pointer-events-none');
                bttBtn.classList.remove('opacity-100', 'pointer-events-auto');
            }
        }, { passive: true });
    }

    // Initialize product carousel
    initProductCarousel();
    // Initialize showcase / termékbemutató carousel
    initShowcaseCarousel();
});

// --- ROTATING PRODUCT CAROUSEL WITH STRICT CONSTRAINTS ---
// Rule 1: No product that has already appeared may reappear until all products have been shown (full cycle).
// Rule 2: "Vitaflora Solutie Nutritiva" cannot appear consecutively, unless no other products remain in the cycle.

let currentProductIndex = 0;
let productSlides = [];
let carouselInterval = null;
let productCycleQueue = [];
let productHistory = [];
let productHistoryPointer = -1;

function isVitafloraSlide(slideEl) {
    if (!slideEl) return false;
    if (slideEl.getAttribute('data-is-vitaflora') === 'true') return true;
    const nameEl = slideEl.querySelector('h4');
    const name = nameEl ? nameEl.textContent.toLowerCase() : '';
    const clean = name.replace(/ț/g, 't').replace(/ș/g, 's').replace(/ă/g, 'a').replace(/â/g, 'a').replace(/î/g, 'i');
    return clean.includes('vitaflora solutie nutritiva');
}

function generateConstrainedCycle(slides, prevWasVitaflora = false) {
    const total = slides.length;
    if (total === 0) return [];
    
    const vIndices = [];
    const otherIndices = [];
    
    slides.forEach((slide, idx) => {
        if (isVitafloraSlide(slide)) {
            vIndices.push(idx);
        } else {
            otherIndices.push(idx);
        }
    });

    function shuffleArray(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }

    const vShuffled = shuffleArray([...vIndices]);
    const otherShuffled = shuffleArray([...otherIndices]);

    const totalSlots = otherShuffled.length + 1;
    let availableSlots = Array.from({ length: totalSlots }, (_, i) => i);
    
    // If previous slide was Vitaflora, Slot 0 cannot be Vitaflora
    if (prevWasVitaflora && availableSlots.includes(0)) {
        availableSlots = availableSlots.filter(s => s !== 0);
    }

    const numV = vShuffled.length;
    const slotCounts = {};

    if (numV <= availableSlots.length) {
        // Shuffle available slots and pick numV distinct slots
        const chosenSlots = new Set(shuffleArray([...availableSlots]).slice(0, numV));
        for (let s = 0; s < totalSlots; s++) {
            slotCounts[s] = chosenSlots.has(s) ? 1 : 0;
        }
    } else {
        // If other products are exhausted, distribute across available slots
        for (const s of availableSlots) {
            slotCounts[s] = 1;
        }
        const rem = numV - availableSlots.length;
        const pool = availableSlots.length > 0 ? availableSlots : Array.from({ length: totalSlots }, (_, i) => i);
        for (let r = 0; r < rem; r++) {
            const randomSlot = pool[Math.floor(Math.random() * pool.length)];
            slotCounts[randomSlot] = (slotCounts[randomSlot] || 0) + 1;
        }
    }

    const result = [];
    let vIdx = 0;
    for (let slot = 0; slot < totalSlots; slot++) {
        const count = slotCounts[slot] || 0;
        for (let c = 0; c < count; c++) {
            result.push(vShuffled[vIdx++]);
        }
        if (slot < otherShuffled.length) {
            result.push(otherShuffled[slot]);
        }
    }

    return result;
}

function initProductCarousel() {
    productSlides = Array.from(document.querySelectorAll('.product-slide'));
    if (!productSlides || productSlides.length === 0) return;

    // The server delivers sidebar_products in a pre-constrained cycle.
    // Slide 0 is shown first, and remaining slides (1..N-1) form the first cycle queue.
    currentProductIndex = 0;
    productHistory = [0];
    productHistoryPointer = 0;
    showProductSlide(0, false);

    productCycleQueue = [];
    for (let i = 1; i < productSlides.length; i++) {
        productCycleQueue.push(i);
    }

    // Auto rotate every 4.5 seconds
    startProductCarousel();

    const container = document.getElementById('product-carousel-container');
    if (container) {
        container.addEventListener('mouseenter', () => clearInterval(carouselInterval));
        container.addEventListener('mouseleave', () => startProductCarousel());
        setupTouchSwipe(container, () => nextProductSlide(false), () => prevProductSlide());
    }
}

function startProductCarousel() {
    clearInterval(carouselInterval);
    carouselInterval = setInterval(() => {
        nextProductSlide(true);
    }, 4500);
}

function showProductSlide(index, resetTimer = true) {
    if (!productSlides || productSlides.length === 0) return;
    
    currentProductIndex = (index + productSlides.length) % productSlides.length;

    productSlides.forEach((slide, idx) => {
        if (idx === currentProductIndex) {
            slide.classList.remove('hidden');
            slide.classList.add('block');
        } else {
            slide.classList.add('hidden');
            slide.classList.remove('block');
        }
    });

    const counter = document.getElementById('product-slide-counter');
    if (counter) {
        counter.textContent = `${currentProductIndex + 1} din ${productSlides.length}`;
    }

    if (resetTimer) {
        startProductCarousel();
    }
}

function nextProductSlide(fromInterval = false) {
    if (!productSlides || productSlides.length === 0) return;

    // If user navigated backwards with prevProductSlide, forward step returns through history
    if (productHistoryPointer < productHistory.length - 1) {
        productHistoryPointer++;
        showProductSlide(productHistory[productHistoryPointer], !fromInterval);
        return;
    }

    // Otherwise, consume next product from current cycle queue
    if (productCycleQueue.length === 0) {
        // Rule 1: All products have been shown once! Start next fresh constrained cycle.
        const lastShownIdx = productHistory.length > 0 ? productHistory[productHistory.length - 1] : -1;
        const lastWasV = lastShownIdx >= 0 ? isVitafloraSlide(productSlides[lastShownIdx]) : false;
        productCycleQueue = generateConstrainedCycle(productSlides, lastWasV);
    }

    const nextIdx = productCycleQueue.shift();
    productHistory.push(nextIdx);
    productHistoryPointer = productHistory.length - 1;
    showProductSlide(nextIdx, !fromInterval);
}

function prevProductSlide() {
    if (!productSlides || productSlides.length === 0) return;

    if (productHistoryPointer > 0) {
        productHistoryPointer--;
        showProductSlide(productHistory[productHistoryPointer], true);
    } else {
        // At start of history; keep current slide and restart timer
        showProductSlide(currentProductIndex, true);
    }
}

// --- PRODUCT MODAL DIALOG ---
// Prompt requirement: "Ha ra klikkelsz egy ajanlott termek kepre akkor nyissa meg az adott termek kepet nagyban egy termek leirassal mellette es egy linkel ahol elerheto lesz a termek."

async function openProductModal(prodId) {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    try {
        const response = await fetch(`${window.PLANTEONLINE_BASE_PREFIX || ''}/api/product/${prodId}/`);
        if (!response.ok) throw new Error('Produsul nu a putut fi încărcat');
        const prod = await response.json();

        // Populate modal fields
        const imgEl = document.getElementById('modal-product-img');
        const titleEl = document.getElementById('modal-product-title');
        const brandEl = document.getElementById('modal-product-brand');
        const codeEl = document.getElementById('modal-product-code');
        const pkgBoxEl = document.getElementById('modal-product-packaging-box');
        const pkgEl = document.getElementById('modal-product-packaging');
        const descEl = document.getElementById('modal-product-desc');
        const linkEl = document.getElementById('modal-product-link');
        const detailLinkEl = document.getElementById('modal-product-detail-link');

        if (imgEl) {
            imgEl.src = prod.image_url || 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?auto=format&fit=crop&w=500&q=80';
            imgEl.alt = prod.name;
        }
        if (detailLinkEl && prod.id) {
            detailLinkEl.href = `${window.PLANTEONLINE_BASE_PREFIX || ''}/produs/${prod.id}/`;
        }
        if (titleEl) titleEl.textContent = prod.name;
        if (brandEl) brandEl.textContent = prod.brand || 'Florasol';
        if (codeEl) codeEl.textContent = prod.code ? `Cod: ${prod.code}` : '';
        if (pkgBoxEl && pkgEl) {
            if (prod.packaging) {
                pkgEl.textContent = `Ambalaje disponibile: ${prod.packaging}`;
                pkgBoxEl.classList.remove('hidden');
            } else {
                pkgBoxEl.classList.add('hidden');
            }
        }
        if (descEl) descEl.textContent = prod.description || 'Soluție profesională pentru îngrijirea optimă a plantelor.';
        if (linkEl) {
            linkEl.href = prod.external_url || '#';
            linkEl.setAttribute('target', '_blank');
            linkEl.setAttribute('rel', 'noopener noreferrer');
            window.currentActiveModalProductId = prodId;
            if (!linkEl.dataset.trackBound) {
                linkEl.dataset.trackBound = 'true';
                linkEl.addEventListener('click', function() {
                    const activeId = window.currentActiveModalProductId;
                    if (activeId) {
                        try {
                            fetch(`/api/track/product/${activeId}`, { method: 'POST' });
                        } catch (e) {}
                    }
                });
            }
        }

        // Show modal with transition
        modal.classList.remove('opacity-0', 'pointer-events-none');
        modal.classList.add('opacity-100', 'pointer-events-auto');
        const dialogBox = modal.querySelector('div');
        if (dialogBox) {
            dialogBox.classList.remove('scale-95');
            dialogBox.classList.add('scale-100');
        }

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    } catch (err) {
        console.error('Eroare la deschiderea modalului de produs:', err);
    }
}

function closeProductModal() {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    modal.classList.add('opacity-0', 'pointer-events-none');
    modal.classList.remove('opacity-100', 'pointer-events-auto');
    const dialogBox = modal.querySelector('div');
    if (dialogBox) {
        dialogBox.classList.add('scale-95');
        dialogBox.classList.remove('scale-100');
    }

    document.body.style.overflow = '';
}

// Close modal on backdrop click or Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeProductModal();
});

document.addEventListener('click', (e) => {
    const modal = document.getElementById('product-modal');
    if (modal && e.target === modal) {
        closeProductModal();
    }
});

// --- CALENDAR ARTICLE COLLAPSIBLE ---
function toggleCalendarArticle() {
    const box = document.getElementById('full-calendar-article-box');
    const btnText = document.getElementById('expand-btn-text');
    const icon = document.getElementById('expand-icon');

    if (!box) return;

    if (box.classList.contains('hidden')) {
        box.classList.remove('hidden');
        if (btnText) btnText.textContent = 'Ascunde articolul complet';
        if (icon) icon.classList.add('rotate-180');
    } else {
        box.classList.add('hidden');
        if (btnText) btnText.textContent = 'Citește articolul complet al lunii';
        if (icon) icon.classList.remove('rotate-180');
    }
}

// --- MEDIA UPLOAD ASYNC (ADMIN) ---
async function uploadImageAsync(input) {
    if (!input.files || input.files.length === 0) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);

    const resultBox = document.getElementById('media-upload-result');
    const previewImg = document.getElementById('media-preview-img');
    const copyUrlInput = document.getElementById('media-copy-url');

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            if (resultBox) resultBox.classList.remove('hidden');
            if (previewImg) previewImg.src = data.url;
            if (copyUrlInput) copyUrlInput.value = window.location.origin + data.url;
        } else {
            alert(data.error || 'Eroare la încărcarea imaginii');
        }
    } catch (err) {
        alert('Eroare de rețea la încărcare');
    }
}

function copyMediaUrl() {
    const input = document.getElementById('media-copy-url');
    if (input) {
        input.select();
        navigator.clipboard.writeText(input.value);
        alert('URL-ul imaginii a fost copiat în clipboard!');
    }
}

// --- GHID VIZUAL / SHOWCASE ADMIN PREVIEW ---
function previewShowcaseUpload(input) {
    const container = document.getElementById('showcase-upload-preview-container');
    const list = document.getElementById('showcase-selected-list');
    const countLabel = document.getElementById('showcase-selected-count');
    if (!container || !list) return;

    list.innerHTML = '';
    const files = Array.from(input.files || []);
    if (files.length === 0) {
        container.classList.add('hidden');
        return;
    }

    if (countLabel) {
        countLabel.textContent = `${files.length} fișier(e) selectat(e) pentru încărcare:`;
    }
    container.classList.remove('hidden');

    files.forEach(file => {
        const item = document.createElement('div');
        item.className = 'bg-white rounded-xl p-2 border border-stone-200 text-center text-xs space-y-1 shadow-xs';
        
        const img = document.createElement('img');
        img.className = 'w-full h-16 object-cover rounded-lg mb-1 bg-stone-100';
        img.src = URL.createObjectURL(file);
        
        const name = document.createElement('div');
        name.className = 'truncate text-[10px] text-stone-700 font-medium';
        name.textContent = file.name;

        item.appendChild(img);
        item.appendChild(name);
        list.appendChild(item);
    });

    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function clearShowcaseSelected() {
    const input = document.getElementById('showcase-file-input');
    if (input) input.value = '';
    const container = document.getElementById('showcase-upload-preview-container');
    if (container) container.classList.add('hidden');
}

// --- ROTATING SHOWCASE / TERMÉKBEMUTATÓ CAROUSEL ---
let currentShowcaseIndex = 0;
let showcaseSlides = [];
let showcaseInterval = null;

function initShowcaseCarousel() {
    showcaseSlides = document.querySelectorAll('.showcase-slide');
    if (!showcaseSlides || showcaseSlides.length === 0) return;

    // Pick a random slide on initial load
    const initialScIdx = Math.floor(Math.random() * showcaseSlides.length);
    showShowcaseSlide(initialScIdx);

    // Auto rotate randomly every 4 seconds
    startShowcaseCarousel();

    const container = document.getElementById('showcase-carousel-container');
    if (container) {
        container.addEventListener('mouseenter', () => clearInterval(showcaseInterval));
        container.addEventListener('mouseleave', () => startShowcaseCarousel());
        setupTouchSwipe(container, () => nextShowcaseSlide(false), () => prevShowcaseSlide());
    }
}

function startShowcaseCarousel() {
    clearInterval(showcaseInterval);
    showcaseInterval = setInterval(() => {
        nextShowcaseSlide(true); // random rotation
    }, 4000);
}

function showShowcaseSlide(index) {
    if (!showcaseSlides || showcaseSlides.length === 0) return;

    if (index >= showcaseSlides.length) currentShowcaseIndex = 0;
    else if (index < 0) currentShowcaseIndex = showcaseSlides.length - 1;
    else currentShowcaseIndex = index;

    showcaseSlides.forEach((slide, idx) => {
        if (idx === currentShowcaseIndex) {
            slide.classList.remove('hidden');
            slide.classList.add('block');
        } else {
            slide.classList.add('hidden');
            slide.classList.remove('block');
        }
    });

    const counter = document.getElementById('showcase-slide-counter');
    if (counter) {
        counter.textContent = `${currentShowcaseIndex + 1} din ${showcaseSlides.length}`;
    }
}

function nextShowcaseSlide(isRandom = false) {
    if (isRandom && showcaseSlides.length > 2) {
        let nextIdx;
        do {
            nextIdx = Math.floor(Math.random() * showcaseSlides.length);
        } while (nextIdx === currentShowcaseIndex);
        showShowcaseSlide(nextIdx);
    } else {
        showShowcaseSlide(currentShowcaseIndex + 1);
    }
}

function prevShowcaseSlide() {
    showShowcaseSlide(currentShowcaseIndex - 1);
}

// --- SHOWCASE LIGHTBOX MODAL ---
function openShowcaseLightbox(imgUrl) {
    const modal = document.getElementById('showcase-modal');
    if (!modal) return;

    const imgEl = document.getElementById('showcase-modal-img');
    if (imgEl) imgEl.src = imgUrl;

    modal.classList.remove('opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');
    const dialogBox = modal.querySelector('div');
    if (dialogBox) {
        dialogBox.classList.remove('scale-95');
        dialogBox.classList.add('scale-100');
    }
    document.body.style.overflow = 'hidden';
}

function closeShowcaseLightbox() {
    const modal = document.getElementById('showcase-modal');
    if (!modal) return;

    modal.classList.add('opacity-0', 'pointer-events-none');
    modal.classList.remove('opacity-100', 'pointer-events-auto');
    const dialogBox = modal.querySelector('div');
    if (dialogBox) {
        dialogBox.classList.add('scale-95');
        dialogBox.classList.remove('scale-100');
    }
    document.body.style.overflow = '';
}

// Escape key and backdrop click listener for showcase modal
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeShowcaseLightbox();
    }
});

document.addEventListener('click', (e) => {
    const scModal = document.getElementById('showcase-modal');
    if (scModal && e.target === scModal) {
        closeShowcaseLightbox();
    }
});

// --- AUTO SUGGEST RECOMMENDED PRODUCTS FOR PLANT (ADMIN) ---
async function autoSuggestPlantProducts() {
    const nameInput = document.querySelector('input[name="name"]');
    const latinInput = document.querySelector('input[name="latin_name"]');
    const categoryInput = document.querySelector('input[name="category"]');
    const descInput = document.querySelector('textarea[name="description"]');
    const leavesInput = document.querySelector('input[name="leaves"]');
    const flowersInput = document.querySelector('input[name="flowers"]');
    const statusMsg = document.getElementById('auto-suggest-status');

    const payload = {
        name: nameInput ? nameInput.value : '',
        latin_name: latinInput ? latinInput.value : '',
        category: categoryInput ? categoryInput.value : '',
        description: descInput ? descInput.value : '',
        leaves: leavesInput ? leavesInput.value : '',
        flowers: flowersInput ? flowersInput.value : ''
    };

    if (statusMsg) {
        statusMsg.textContent = 'Analiză caracteristici botanice în curs...';
        statusMsg.classList.remove('hidden', 'text-emerald-700', 'text-rose-600');
        statusMsg.classList.add('text-stone-500');
    }

    try {
        const res = await fetch('/api/plant/suggest-products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success && data.recommended_product_ids) {
            const checkboxes = document.querySelectorAll('.plant-rec-checkbox');
            const targetIds = new Set(data.recommended_product_ids);

            checkboxes.forEach(cb => {
                const id = parseInt(cb.value);
                const isSelected = targetIds.has(id);
                cb.checked = isSelected;

                const parentCard = cb.closest('.plant-rec-card');
                if (parentCard) {
                    if (isSelected) {
                        parentCard.classList.add('border-botanic-500', 'bg-emerald-50/40');
                        parentCard.classList.remove('border-stone-200');
                    } else {
                        parentCard.classList.remove('border-botanic-500', 'bg-emerald-50/40');
                        parentCard.classList.add('border-stone-200');
                    }
                }
            });

            if (statusMsg) {
                const subName = data.primary_substrate ? data.primary_substrate.name : '';
                const fertName = data.primary_fertilizer ? data.primary_fertilizer.name : '';
                statusMsg.textContent = `✓ Detectat optim: Substrat [${subName}] + Nutriție [${fertName}] (${data.recommended_product_ids.length} produse selectate)`;
                statusMsg.classList.remove('text-stone-500', 'text-rose-600');
                statusMsg.classList.add('text-emerald-700');
            }
        }
    } catch (err) {
        if (statusMsg) {
            statusMsg.textContent = 'Eroare la obținerea sugestiilor automate.';
            statusMsg.classList.remove('text-stone-500', 'text-emerald-700');
            statusMsg.classList.add('text-rose-600');
        }
    }
}

// --- DUPLICATE PLANT DETECTION & POPUP WARNING ---
let _lastWarnedDuplicatePlantId = null;

function getCurrentEditedPlantId() {
    const idEl = document.querySelector('#plant-form input[name="id"]');
    if (!idEl || !idEl.value) return null;
    const parsed = parseInt(idEl.value, 10);
    return isNaN(parsed) ? null : parsed;
}

function findDuplicatePlantClientSide(nameVal, latinVal, excludeId = null) {
    const rows = document.querySelectorAll('#plants-table-body .plant-row');
    if (!rows || rows.length === 0) return null;

    const candidates = new Set();
    [nameVal, latinVal].forEach(raw => {
        if (!raw) return;
        const norm = cleanDiacritics(raw).trim();
        if (norm.length >= 2) candidates.add(norm);
        if (norm.includes(' - ')) {
            norm.split(' - ').forEach(part => {
                const pClean = part.trim();
                if (pClean.length >= 2) candidates.add(pClean);
            });
        }
    });

    if (candidates.size === 0) return null;

    for (const row of rows) {
        const rowId = parseInt(row.dataset.id || '0', 10);
        if (excludeId !== null && rowId === excludeId) continue;

        const rowName = row.dataset.name || '';
        const rowLatin = row.dataset.latin || '';
        const rowCat = row.dataset.category || '';

        const normName = cleanDiacritics(rowName).trim();
        const normLatin = cleanDiacritics(rowLatin).trim();

        const tokens = new Set([normName, normLatin]);
        if (normName.includes(' - ')) {
            normName.split(' - ').forEach(seg => {
                const sClean = seg.trim();
                if (sClean) tokens.add(sClean);
                sClean.split(/\bsau\b|,|\(|\)/).forEach(sub => {
                    const subClean = sub.trim();
                    if (subClean.length >= 3) tokens.add(subClean);
                });
            });
        }
        tokens.delete('');

        for (const cand of candidates) {
            if (tokens.has(cand)) {
                return {
                    id: rowId,
                    name: rowName,
                    latin_name: rowLatin,
                    category: rowCat
                };
            }
        }
    }
    return null;
}

function showDuplicatePlantWarning(dupPlant, showModalPopup = true) {
    if (!dupPlant || !dupPlant.id) return;

    const editUrl = `/admin?tab=plants&edit_plant=${dupPlant.id}#plant-form`;

    // 1. Update inline warning banner
    const banner = document.getElementById('plant-duplicate-warning');
    const bannerText = document.getElementById('plant-duplicate-warning-text');
    const bannerLink = document.getElementById('plant-duplicate-edit-link');
    if (banner) {
        if (bannerText) {
            bannerText.textContent = `Specia „${dupPlant.name}” (${dupPlant.latin_name || 'Nume latin'}, ID #${dupPlant.id}) se află deja în catalogul Plante A-Z.`;
        }
        if (bannerLink) {
            bannerLink.href = editUrl;
        }
        banner.classList.remove('hidden');
    }

    // 2. Pop up warning modal if requested and not already dismissed for this exact plant ID
    if (showModalPopup && _lastWarnedDuplicatePlantId !== dupPlant.id) {
        _lastWarnedDuplicatePlantId = dupPlant.id;
        openDuplicatePlantModal(dupPlant);
    }
}

function openDuplicatePlantModal(dupPlant) {
    const modal = document.getElementById('duplicate-plant-modal');
    if (!modal || !dupPlant) return;

    const idEl = document.getElementById('dup-modal-plant-id');
    const nameEl = document.getElementById('dup-modal-plant-name');
    const latinEl = document.getElementById('dup-modal-plant-latin');
    const catEl = document.getElementById('dup-modal-plant-category');
    const editBtn = document.getElementById('dup-modal-edit-btn');

    if (idEl) idEl.textContent = `#${dupPlant.id}`;
    if (nameEl) nameEl.textContent = dupPlant.name || '--';
    if (latinEl) latinEl.textContent = dupPlant.latin_name || '--';
    if (catEl) catEl.textContent = dupPlant.category || 'Plante';
    if (editBtn) editBtn.href = `/admin?tab=plants&edit_plant=${dupPlant.id}#plant-form`;

    modal.classList.remove('opacity-0', 'pointer-events-none');
    modal.classList.add('opacity-100', 'pointer-events-auto');
    const dialogBox = modal.querySelector('div');
    if (dialogBox) {
        dialogBox.classList.remove('scale-95');
        dialogBox.classList.add('scale-100');
    }
}

function closeDuplicatePlantModal() {
    const modal = document.getElementById('duplicate-plant-modal');
    if (!modal) return;
    modal.classList.add('opacity-0', 'pointer-events-none');
    modal.classList.remove('opacity-100', 'pointer-events-auto');
    const dialogBox = modal.querySelector('div');
    if (dialogBox) {
        dialogBox.classList.add('scale-95');
        dialogBox.classList.remove('scale-100');
    }
}

function hideDuplicatePlantWarning() {
    const banner = document.getElementById('plant-duplicate-warning');
    if (banner) banner.classList.add('hidden');
    _lastWarnedDuplicatePlantId = null;
}

function checkDuplicatePlantOnSubmit(event) {
    const nameInput = document.querySelector('#plant-form input[name="name"]');
    const latinInput = document.querySelector('#plant-form input[name="latin_name"]');
    const currentId = getCurrentEditedPlantId();
    const nameVal = nameInput ? nameInput.value.trim() : '';
    const latinVal = latinInput ? latinInput.value.trim() : '';

    const dup = findDuplicatePlantClientSide(nameVal, latinVal, currentId);
    if (dup) {
        if (event) event.preventDefault();
        _lastWarnedDuplicatePlantId = null; // Force modal popup on submit attempt
        showDuplicatePlantWarning(dup, true);
        return false;
    }
    return true;
}

// --- AUTO-FILL ALL PLANT FIELDS FROM INTERNET (WIKIPEDIA / INATURALIST / WIKIDATA) ---
let _plantAutofillTimer = null;
let _lastAutofillQuery = '';

function onPlantIdentityInputChanged(sourceField) {
    clearTimeout(_plantAutofillTimer);
    const nameInput = document.querySelector('#plant-form input[name="name"]');
    const latinInput = document.querySelector('#plant-form input[name="latin_name"]');
    const nameVal = nameInput ? nameInput.value.trim() : '';
    const latinVal = latinInput ? latinInput.value.trim() : '';
    const val = (sourceField === 'latin_name' ? latinVal : nameVal);
    if (val.length < 3) {
        hideDuplicatePlantWarning();
        return;
    }

    // Immediate client-side check against the catalog
    const currentId = getCurrentEditedPlantId();
    const localDup = findDuplicatePlantClientSide(nameVal, latinVal, currentId);
    if (localDup) {
        showDuplicatePlantWarning(localDup, true);
    } else {
        hideDuplicatePlantWarning();
    }

    // Trigger automatic fill when user finishes entering Nume Românesc or Nume Latin
    autoFillPlantFromWeb(false, sourceField);
}

async function autoFillPlantFromWeb(forceOverwrite = false, sourceField = '') {
    const form = document.querySelector('#plant-form form');
    if (!form) return;

    const nameInput = form.querySelector('input[name="name"]');
    const latinInput = form.querySelector('input[name="latin_name"]');
    const categoryInput = form.querySelector('input[name="category"]');
    const originInput = form.querySelector('input[name="origin"]');
    const flowersInput = form.querySelector('input[name="flowers"]');
    const leavesInput = form.querySelector('input[name="leaves"]');
    const shapeInput = form.querySelector('input[name="shape"]');
    const imageInput = form.querySelector('input[name="image_url"]');
    const imageInput2 = form.querySelector('input[name="image_url_2"]');
    const imageInput3 = form.querySelector('input[name="image_url_3"]');
    const luminaInput = form.querySelector('input[name="lumina"]');
    const tempInput = form.querySelector('input[name="temperatura"]');
    const udareInput = form.querySelector('input[name="udare"]');
    const solInput = form.querySelector('input[name="sol"]');
    const fertInput = form.querySelector('input[name="fertilizare"]');
    const descInput = form.querySelector('textarea[name="description"]');

    const statusBox = document.getElementById('plant-autofill-status');
    const previewBox = document.getElementById('plant-autofill-images-preview');
    const btn = document.getElementById('btn-autofill-plant');

    const nameVal = nameInput ? nameInput.value.trim() : '';
    const latinVal = latinInput ? latinInput.value.trim() : '';
    const currentId = getCurrentEditedPlantId();

    if (!nameVal && !latinVal) {
        if (statusBox) {
            statusBox.textContent = 'Vă rugăm să introduceți mai întâi Numele Românesc sau Numele Latin al plantei.';
            statusBox.className = 'mb-3 px-3.5 py-2 rounded-xl text-xs font-semibold border bg-amber-50 text-amber-800 border-amber-200';
        }
        return;
    }

    // Immediate client-side duplicate check
    const preDup = findDuplicatePlantClientSide(nameVal, latinVal, currentId);
    if (preDup) {
        showDuplicatePlantWarning(preDup, true);
    }

    const queryKey = `${nameVal.toLowerCase()}|${latinVal.toLowerCase()}`;
    if (!forceOverwrite && queryKey === _lastAutofillQuery) {
        return;
    }
    _lastAutofillQuery = queryKey;

    if (statusBox) {
        statusBox.textContent = 'Se caută informațiile botanice și fotografiile plantei pe internet (Wikipedia, Wikidata, iNaturalist)...';
        statusBox.className = 'mb-3 px-3.5 py-2 rounded-xl text-xs font-semibold border bg-stone-100 text-stone-700 border-stone-200 animate-pulse';
    }
    if (btn) {
        btn.disabled = true;
        btn.classList.add('opacity-75');
    }

    try {
        const payload = {
            id: currentId,
            name: sourceField === 'latin_name' && !forceOverwrite ? '' : nameVal,
            latin_name: sourceField === 'name' && !forceOverwrite ? '' : latinVal
        };
        if (!payload.name && !payload.latin_name) {
            payload.name = nameVal;
            payload.latin_name = latinVal;
        }

        const res = await fetch('/api/plant/autofill', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (!data.success || !data.plant) {
            throw new Error(data.error || 'Nu s-au putut prelua datele plantei.');
        }

        const p = data.plant;

        // If backend or resolved plant name indicates the plant already exists in the database, trigger warning popup!
        const resolvedDup = (data.already_exists && data.existing_plant)
            ? data.existing_plant
            : findDuplicatePlantClientSide(p.name || nameVal, p.latin_name || latinVal, currentId);

        if (resolvedDup) {
            showDuplicatePlantWarning(resolvedDup, true);
        } else {
            hideDuplicatePlantWarning();
        }

        function setField(el, newVal, allowDefaultOverwrite = false) {
            if (!el || !newVal) return;
            const cur = el.value.trim();
            if (forceOverwrite || !cur || (allowDefaultOverwrite && cur === 'Perene')) {
                el.value = newVal;
                el.classList.add('ring-2', 'ring-emerald-400', 'bg-emerald-50/40');
                setTimeout(() => {
                    el.classList.remove('ring-2', 'ring-emerald-400', 'bg-emerald-50/40');
                }, 1800);
            }
        }

        // Always update missing or combined Nume Românesc & Nume Latin
        if (nameInput && p.name && (forceOverwrite || !nameInput.value.trim() || sourceField === 'latin_name' || !nameInput.value.includes(' - '))) {
            setField(nameInput, p.name, true);
        }
        if (latinInput && p.latin_name && (forceOverwrite || !latinInput.value.trim() || sourceField === 'name')) {
            setField(latinInput, p.latin_name, true);
        }

        setField(categoryInput, p.category, true);
        setField(originInput, p.origin);
        setField(flowersInput, p.flowers);
        setField(leavesInput, p.leaves);
        setField(shapeInput, p.shape);

        // Update all 3 visual photo slots
        const imgs = p.images || (p.image_url ? [p.image_url] : []);
        const slotInputs = [imageInput, imageInput2, imageInput3];
        for (let s = 0; s < 3; s++) {
            const slotEl = slotInputs[s];
            const newImg = imgs[s] || '';
            if (slotEl && newImg && (forceOverwrite || !slotEl.value.trim())) {
                slotEl.value = newImg;
            }
            if (slotEl) {
                renderPlantPhotoSlot(s + 1, slotEl.value.trim());
            }
        }

        setField(luminaInput, p.lumina);
        setField(tempInput, p.temperatura);
        setField(udareInput, p.udare);
        setField(solInput, p.sol);
        setField(fertInput, p.fertilizare);
        setField(descInput, p.description);

        // Check recommended products checkboxes
        if (data.recommended_product_ids) {
            const checkboxes = document.querySelectorAll('.plant-rec-checkbox');
            const targetIds = new Set(data.recommended_product_ids);
            checkboxes.forEach(cb => {
                const id = parseInt(cb.value, 10);
                const isSelected = targetIds.has(id);
                cb.checked = isSelected;
                const parentCard = cb.closest('.plant-rec-card');
                if (parentCard) {
                    parentCard.classList.toggle('border-botanic-500', isSelected);
                    parentCard.classList.toggle('bg-emerald-50/40', isSelected);
                    parentCard.classList.toggle('border-stone-200', !isSelected);
                }
            });

            const prodStatus = document.getElementById('auto-suggest-status');
            if (prodStatus) {
                const subName = data.primary_substrate ? data.primary_substrate.name : '';
                const fertName = data.primary_fertilizer ? data.primary_fertilizer.name : '';
                prodStatus.textContent = `✓ Produse asociate automat: Substrat [${subName}] + Nutriție [${fertName}]`;
                prodStatus.className = 'text-xs font-semibold py-1 text-emerald-700';
            }
        }

        if (statusBox) {
            statusBox.textContent = `✓ Fișa botanică pentru „${p.name}” a fost completată automat (${data.source}). Puteți modifica liber orice câmp înainte de salvare!`;
            statusBox.className = 'mb-3 px-3.5 py-2 rounded-xl text-xs font-semibold border bg-emerald-50 text-emerald-800 border-emerald-200';
        }
    } catch (err) {
        if (statusBox) {
            statusBox.textContent = 'Nu s-au putut prelua automat toate datele. Puteți completa sau corecta manual câmpurile.';
            statusBox.className = 'mb-3 px-3.5 py-2 rounded-xl text-xs font-semibold border bg-rose-50 text-rose-700 border-rose-200';
        }
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.classList.remove('opacity-75');
        }
    }
}

// --- PLANT PHOTO SLOTS MANAGEMENT (VIEW, DELETE, REPLACE / UPLOAD) ---
function normalizePlantImageUrl(rawUrl) {
    if (!rawUrl) return '';
    let url = rawUrl.trim();

    // 1. Convert Wikipedia/Wikimedia MediaViewer links: .../wiki/...#/media/Fișier:Example.jpg or #/media/File:Example.jpg
    if (url.includes('#/media/')) {
        try {
            const afterMedia = url.split('#/media/')[1].split(/[?&]/)[0];
            const decoded = decodeURIComponent(afterMedia);
            // Strip namespace prefix like "Fișier:", "File:", "Imagine:", "Fájl:", etc.
            const colonIdx = decoded.indexOf(':');
            const fileName = (colonIdx !== -1 ? decoded.substring(colonIdx + 1) : decoded).trim().replace(/ /g, '_');
            if (fileName) {
                return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(fileName)}`;
            }
        } catch (e) {}
    }

    // 2. Convert Wikipedia/Wikimedia File page links: .../wiki/Fișier:Example.jpg or .../wiki/File:Example.jpg
    if ((url.includes('wikipedia.org/wiki/') || url.includes('wikimedia.org/wiki/')) && !url.includes('Special:FilePath')) {
        try {
            const wikiPart = url.split('/wiki/')[1].split(/[?#]/)[0];
            const decoded = decodeURIComponent(wikiPart);
            const match = decoded.match(/^(?:Fișier|Fisier|File|Imagine|Image|Fájl|Datei|Fichier|Archivo|Plik):(.+)$/i);
            if (match && match[1]) {
                const fileName = match[1].trim().replace(/ /g, '_');
                return `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(fileName)}`;
            }
        } catch (e) {}
    }

    return url;
}

function renderPlantPhotoSlot(slotIdx, imgSrc) {
    const imgEl = document.getElementById(`plant-photo-img-${slotIdx}`);
    const emptyEl = document.getElementById(`plant-photo-empty-${slotIdx}`);
    const delBtn = document.getElementById(`plant-photo-del-btn-${slotIdx}`);
    const uploadLabel = document.getElementById(`plant-photo-upload-label-${slotIdx}`);
    const normalizedSrc = normalizePlantImageUrl(imgSrc);

    if (normalizedSrc) {
        if (imgEl) {
            imgEl.src = normalizedSrc;
            imgEl.classList.remove('hidden');
        }
        if (emptyEl) emptyEl.classList.add('hidden');
        if (delBtn) delBtn.classList.remove('hidden');
        if (uploadLabel) uploadLabel.textContent = 'Înlocuiește cu altă poză';
    } else {
        if (imgEl) {
            imgEl.src = '';
            imgEl.classList.add('hidden');
        }
        if (emptyEl) emptyEl.classList.remove('hidden');
        if (delBtn) delBtn.classList.add('hidden');
        if (uploadLabel) uploadLabel.textContent = 'Încarcă poză din calculator';
    }
}

function updatePlantPhotoSlotFromUrl(slotIdx) {
    const urlInput = document.getElementById(`plant-photo-url-${slotIdx}`);
    const fileInput = document.getElementById(`plant-photo-file-${slotIdx}`);
    if (fileInput) fileInput.value = '';
    let val = urlInput ? urlInput.value.trim() : '';
    const normalized = normalizePlantImageUrl(val);
    if (urlInput && normalized && normalized !== val) {
        urlInput.value = normalized;
        val = normalized;
    }
    renderPlantPhotoSlot(slotIdx, val);
}

function deletePlantPhotoSlot(slotIdx) {
    // Shift subsequent photos forward so if Photo #1 is deleted, Photo #2 automatically becomes Photo #1 (Principală)
    const urls = [1, 2, 3].map(i => {
        const el = document.getElementById(`plant-photo-url-${i}`);
        return el ? el.value.trim() : '';
    });

    // Clear file input on deleted slot
    const deletedFileInput = document.getElementById(`plant-photo-file-${slotIdx}`);
    if (deletedFileInput) deletedFileInput.value = '';

    // Remove the deleted slot (0-based index = slotIdx - 1) and pad with empty string at the end
    urls.splice(slotIdx - 1, 1);
    urls.push('');

    // Update all 3 slots with the shifted URLs and re-render previews
    for (let i = 1; i <= 3; i++) {
        const urlEl = document.getElementById(`plant-photo-url-${i}`);
        const newUrl = normalizePlantImageUrl(urls[i - 1] || '');
        if (urlEl) urlEl.value = newUrl;
        renderPlantPhotoSlot(i, newUrl);
    }
}

async function onPlantPhotoFileSelected(slotIdx, fileInput) {
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;
    const file = fileInput.files[0];

    // Show immediate local preview
    const localUrl = URL.createObjectURL(file);
    renderPlantPhotoSlot(slotIdx, localUrl);

    // Also upload immediately via /api/upload so the URL input is populated with the saved server path
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success && data.url) {
            const urlInput = document.getElementById(`plant-photo-url-${slotIdx}`);
            if (urlInput) {
                urlInput.value = data.url;
            }
            fileInput.value = '';
            renderPlantPhotoSlot(slotIdx, data.url);
        }
    } catch (e) {
        // If offline or error, the form's multipart submission will still upload image_file_{slotIdx} on Save
    }
}

// --- PLANT PHOTOS REORDERING & DRAG-AND-DROP ---
let _draggedSlotIdx = null;

function movePlantPhotoSlot(slotIdx, direction) {
    const targetIdx = slotIdx + direction;
    if (targetIdx < 1 || targetIdx > 3) return;
    reorderPlantPhotoSlots(slotIdx, targetIdx);
}

function reorderPlantPhotoSlots(fromIdx, toIdx) {
    if (fromIdx === toIdx || fromIdx < 1 || fromIdx > 3 || toIdx < 1 || toIdx > 3) return;

    // Read current URLs from all slots
    const urls = [1, 2, 3].map(i => {
        const el = document.getElementById(`plant-photo-url-${i}`);
        return el ? el.value.trim() : '';
    });

    // Move item from (fromIdx - 1) to (toIdx - 1)
    const moved = urls.splice(fromIdx - 1, 1)[0];
    urls.splice(toIdx - 1, 0, moved);

    // Apply new values to each slot and update UI
    for (let i = 1; i <= 3; i++) {
        const urlEl = document.getElementById(`plant-photo-url-${i}`);
        const newUrl = normalizePlantImageUrl(urls[i - 1] || '');
        if (urlEl) urlEl.value = newUrl;
        renderPlantPhotoSlot(i, newUrl);
    }

    // Flash visual feedback on the target card
    const targetCard = document.getElementById(`plant-photo-card-${toIdx}`);
    if (targetCard) {
        targetCard.classList.add('ring-4', 'ring-botanic-500/50', 'bg-botanic-50/80');
        setTimeout(() => {
            targetCard.classList.remove('ring-4', 'ring-botanic-500/50', 'bg-botanic-50/80');
        }, 500);
    }

    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function initPlantPhotoDragAndDrop() {
    const cards = document.querySelectorAll('.plant-photo-card');
    if (!cards || cards.length === 0) return;

    cards.forEach(card => {
        card.addEventListener('dragstart', (e) => {
            // Prevent drag if interaction is on input, button or label
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'BUTTON' || e.target.closest('button') || e.target.closest('input') || e.target.closest('label')) {
                e.preventDefault();
                return;
            }
            const slotIdx = parseInt(card.dataset.slotIdx, 10);
            _draggedSlotIdx = slotIdx;
            e.dataTransfer.setData('text/plain', String(slotIdx));
            e.dataTransfer.effectAllowed = 'move';

            card.classList.add('opacity-50', 'ring-2', 'ring-botanic-500', 'scale-[0.98]');
        });

        card.addEventListener('dragend', () => {
            _draggedSlotIdx = null;
            cards.forEach(c => {
                c.classList.remove('opacity-50', 'ring-2', 'ring-botanic-500', 'scale-[0.98]', 'border-botanic-500', 'border-dashed', 'bg-botanic-50/70');
            });
        });

        card.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            const slotIdx = parseInt(card.dataset.slotIdx, 10);
            if (_draggedSlotIdx && _draggedSlotIdx !== slotIdx) {
                card.classList.add('border-botanic-500', 'border-dashed', 'bg-botanic-50/70');
            }
        });

        card.addEventListener('dragleave', (e) => {
            if (!card.contains(e.relatedTarget)) {
                card.classList.remove('border-botanic-500', 'border-dashed', 'bg-botanic-50/70');
            }
        });

        card.addEventListener('drop', (e) => {
            e.preventDefault();
            card.classList.remove('border-botanic-500', 'border-dashed', 'bg-botanic-50/70');
            const toIdx = parseInt(card.dataset.slotIdx, 10);
            const fromIdx = _draggedSlotIdx || parseInt(e.dataTransfer.getData('text/plain'), 10);
            if (fromIdx && toIdx && fromIdx !== toIdx) {
                reorderPlantPhotoSlots(fromIdx, toIdx);
            }
            _draggedSlotIdx = null;
        });
    });
}

// Make functions globally available
window.movePlantPhotoSlot = movePlantPhotoSlot;
window.reorderPlantPhotoSlots = reorderPlantPhotoSlots;
window.initPlantPhotoDragAndDrop = initPlantPhotoDragAndDrop;

// Bind debounced input listeners on Nume Românesc and Nume Latin when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initPlantPhotoDragAndDrop();
    const nameInput = document.getElementById('plant-name-input');
    const latinInput = document.getElementById('plant-latin-input');

    [nameInput, latinInput].forEach(inp => {
        if (!inp) return;
        inp.addEventListener('input', () => {
            clearTimeout(_plantAutofillTimer);
            const val = inp.value.trim();
            const currentId = getCurrentEditedPlantId();
            const nVal = nameInput ? nameInput.value.trim() : '';
            const lVal = latinInput ? latinInput.value.trim() : '';

            if (val.length < 3) {
                hideDuplicatePlantWarning();
                return;
            }

            if (val.length >= 4) {
                _plantAutofillTimer = setTimeout(() => {
                    const localDup = findDuplicatePlantClientSide(nVal, lVal, currentId);
                    if (localDup) {
                        showDuplicatePlantWarning(localDup, true);
                    }
                    const src = inp.name === 'latin_name' ? 'latin_name' : 'name';
                    autoFillPlantFromWeb(false, src);
                }, 900);
            }
        });
    });

    // Close duplicate plant modal on Escape or backdrop click
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeDuplicatePlantModal();
    });
    document.addEventListener('click', (e) => {
        const dupModal = document.getElementById('duplicate-plant-modal');
        if (dupModal && e.target === dupModal) {
            closeDuplicatePlantModal();
        }
    });
});

// =============================================================================
// --- ADMIN CLIENT-SIDE FILTER, SORT & PAGINATION SYSTEM ---
// =============================================================================

function cleanDiacritics(str) {
    if (!str) return '';
    return str.toLowerCase()
        .replace(/ț/g, 't').replace(/ș/g, 's')
        .replace(/ă/g, 'a').replace(/â/g, 'a').replace(/î/g, 'i')
        .normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

function parseAdminDateScore(dateStr) {
    if (!dateStr) return 0;
    const parts = dateStr.trim().split('.');
    if (parts.length === 3) {
        return parseInt(parts[2] + parts[1].padStart(2, '0') + parts[0].padStart(2, '0'), 10) || 0;
    }
    return 0;
}

class AdminPaginator {
    constructor(opts) {
        this.container = document.querySelector(opts.containerSelector);
        if (!this.container) return;

        this.itemsSelector = opts.itemsSelector;
        this.listContainer = this.container.querySelector(opts.listContainerSelector);
        if (!this.listContainer) return;

        this.allItems = Array.from(this.listContainer.querySelectorAll(this.itemsSelector));
        this.filteredItems = [...this.allItems];

        this.searchInput = this.container.querySelector(opts.searchSelector);
        this.categoryFilter = this.container.querySelector(opts.categorySelector);
        this.letterFilter = this.container.querySelector(opts.letterSelector);
        this.brandFilter = this.container.querySelector(opts.brandSelector);
        this.sortSelect = this.container.querySelector(opts.sortSelector);
        this.pageSizeSelect = this.container.querySelector(opts.pageSizeSelector);
        this.resetBtn = this.container.querySelector(opts.resetSelector);
        this.infoEl = this.container.querySelector(opts.infoSelector);
        this.controlsEl = this.container.querySelector(opts.controlsSelector);
        this.emptyEl = this.container.querySelector(opts.emptySelector);

        this.pageSize = opts.defaultPageSize || 15;
        this.currentPage = 1;
        this.itemName = opts.itemName || 'elemente';
        this.extractDataFn = opts.extractDataFn || ((el) => ({ ...el.dataset }));
        this.filterFn = opts.filterFn;
        this.sortFn = opts.sortFn;

        this.bindEvents();
        this.apply();
    }

    bindEvents() {
        if (this.searchInput) {
            let debounceTimer;
            this.searchInput.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.currentPage = 1;
                    this.apply();
                }, 100);
            });
        }

        if (this.categoryFilter) {
            this.categoryFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.apply();
            });
        }

        if (this.letterFilter) {
            this.letterFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.apply();
            });
        }

        if (this.brandFilter) {
            this.brandFilter.addEventListener('change', () => {
                this.currentPage = 1;
                this.apply();
            });
        }

        if (this.sortSelect) {
            this.sortSelect.addEventListener('change', () => {
                this.apply();
            });
        }

        if (this.pageSizeSelect) {
            this.pageSizeSelect.addEventListener('change', (e) => {
                const val = e.target.value;
                this.pageSize = val === 'all' ? 999999 : parseInt(val, 10);
                this.currentPage = 1;
                this.apply();
            });
        }

        if (this.resetBtn) {
            this.resetBtn.addEventListener('click', () => {
                this.reset();
            });
        }
    }

    reset() {
        if (this.searchInput) this.searchInput.value = '';
        if (this.categoryFilter) this.categoryFilter.value = 'all';
        if (this.letterFilter) this.letterFilter.value = 'all';
        if (this.brandFilter) this.brandFilter.value = 'all';
        if (this.sortSelect) this.sortSelect.selectedIndex = 0;
        this.currentPage = 1;
        this.apply();
    }

    apply() {
        // 1. Filter
        const query = this.searchInput ? cleanDiacritics(this.searchInput.value.trim()) : '';
        const cat = this.categoryFilter ? this.categoryFilter.value : 'all';
        const letter = this.letterFilter ? this.letterFilter.value : 'all';
        const brand = this.brandFilter ? this.brandFilter.value : 'all';

        this.filteredItems = this.allItems.filter(item => {
            const data = this.extractDataFn(item);
            return this.filterFn(data, { query, cat, letter, brand });
        });

        // 2. Sort
        const sortVal = this.sortSelect ? this.sortSelect.value : '';
        if (this.sortFn) {
            this.filteredItems.sort((a, b) => {
                const dataA = this.extractDataFn(a);
                const dataB = this.extractDataFn(b);
                return this.sortFn(dataA, dataB, sortVal);
            });
        }

        // Re-append items in sorted order
        this.filteredItems.forEach(el => this.listContainer.appendChild(el));

        // 3. Paginate
        this.renderPagination();
    }

    renderPagination() {
        const total = this.filteredItems.length;
        const totalPages = Math.ceil(total / this.pageSize) || 1;

        if (this.currentPage > totalPages) {
            this.currentPage = totalPages;
        }
        if (this.currentPage < 1) {
            this.currentPage = 1;
        }

        const startIdx = (this.currentPage - 1) * this.pageSize;
        const endIdx = startIdx + this.pageSize;

        // Toggle visibility
        this.allItems.forEach(el => {
            el.style.display = 'none';
        });

        this.filteredItems.slice(startIdx, endIdx).forEach(el => {
            el.style.display = '';
        });

        // Update Empty state
        if (this.emptyEl) {
            const tableEl = this.listContainer.closest('table');
            if (total === 0) {
                this.emptyEl.classList.remove('hidden');
                if (tableEl) tableEl.style.display = 'none';
                else this.listContainer.style.display = 'none';
            } else {
                this.emptyEl.classList.add('hidden');
                if (tableEl) tableEl.style.display = '';
                else this.listContainer.style.display = '';
            }
        }

        // Update Info text
        if (this.infoEl) {
            if (total === 0) {
                this.infoEl.textContent = `Niciun rezultat găsit (din total ${this.allItems.length} ${this.itemName})`;
            } else {
                const showingStart = startIdx + 1;
                const showingEnd = Math.min(endIdx, total);
                this.infoEl.textContent = `Afișare ${showingStart} - ${showingEnd} din ${total} ${this.itemName}` + 
                    (total !== this.allItems.length ? ` (filtrat din ${this.allItems.length})` : '');
            }
        }

        // Build pagination buttons: < Prev, numbers, Next >
        if (!this.controlsEl) return;
        this.controlsEl.innerHTML = '';

        if (totalPages <= 1) return;

        // < Prev button
        const prevBtn = document.createElement('button');
        prevBtn.type = 'button';
        prevBtn.className = `px-2.5 py-1.5 rounded-xl border text-xs font-semibold flex items-center space-x-1 transition-all ${
            this.currentPage === 1 
            ? 'opacity-40 cursor-not-allowed border-stone-200 text-stone-400 bg-stone-50' 
            : 'border-stone-200 text-stone-700 bg-white hover:bg-stone-100 hover:border-stone-300 shadow-2xs'
        }`;
        prevBtn.innerHTML = `<span>&larr;</span><span>Anterior</span>`;
        prevBtn.disabled = this.currentPage === 1;
        prevBtn.onclick = () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderPagination();
                this.scrollToContainer();
            }
        };
        this.controlsEl.appendChild(prevBtn);

        // Smart page number buttons with ellipsis
        const pages = this.getPageNumbers(this.currentPage, totalPages);
        pages.forEach(p => {
            if (p === '...') {
                const dots = document.createElement('span');
                dots.className = 'px-2 py-1 text-stone-400 text-xs font-semibold select-none';
                dots.textContent = '...';
                this.controlsEl.appendChild(dots);
            } else {
                const pageNum = parseInt(p, 10);
                const btn = document.createElement('button');
                btn.type = 'button';
                const isActive = pageNum === this.currentPage;
                btn.className = `min-w-[32px] h-8 px-2 rounded-xl text-xs font-bold transition-all ${
                    isActive 
                    ? 'bg-botanic-700 text-white shadow-xs' 
                    : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-50 hover:border-stone-300'
                }`;
                btn.textContent = pageNum;
                btn.onclick = () => {
                    this.currentPage = pageNum;
                    this.renderPagination();
                    this.scrollToContainer();
                };
                this.controlsEl.appendChild(btn);
            }
        });

        // Next > button
        const nextBtn = document.createElement('button');
        nextBtn.type = 'button';
        nextBtn.className = `px-2.5 py-1.5 rounded-xl border text-xs font-semibold flex items-center space-x-1 transition-all ${
            this.currentPage === totalPages 
            ? 'opacity-40 cursor-not-allowed border-stone-200 text-stone-400 bg-stone-50' 
            : 'border-stone-200 text-stone-700 bg-white hover:bg-stone-100 hover:border-stone-300 shadow-2xs'
        }`;
        nextBtn.innerHTML = `<span>Următor</span><span>&rarr;</span>`;
        nextBtn.disabled = this.currentPage === totalPages;
        nextBtn.onclick = () => {
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.renderPagination();
                this.scrollToContainer();
            }
        };
        this.controlsEl.appendChild(nextBtn);

        if (window.lucide && typeof lucide.createIcons === 'function') {
            lucide.createIcons();
        }
    }

    getPageNumbers(current, total) {
        if (total <= 7) {
            return Array.from({ length: total }, (_, i) => i + 1);
        }
        if (current <= 4) {
            return [1, 2, 3, 4, 5, '...', total];
        }
        if (current >= total - 3) {
            return [1, '...', total - 4, total - 3, total - 2, total - 1, total];
        }
        return [1, '...', current - 1, current, current + 1, '...', total];
    }

    scrollToContainer() {
        if (this.container) {
            const rect = this.container.getBoundingClientRect();
            if (rect.top < 0) {
                this.container.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }
    }
}

// Initialise Admin Paginators when DOM is loaded
function initAdminPaginators() {
    // 1. Articles Paginator
    if (document.getElementById('articles-admin-container')) {
        window.adminArticlesPaginator = new AdminPaginator({
            containerSelector: '#articles-admin-container',
            listContainerSelector: '#articles-table-body',
            itemsSelector: '.article-row',
            searchSelector: '#articles-search-input',
            categorySelector: '#articles-category-filter',
            sortSelector: '#articles-sort-select',
            pageSizeSelector: '#articles-pagesize-select',
            resetSelector: '#articles-reset-btn',
            infoSelector: '#articles-pagination-info',
            controlsSelector: '#articles-pagination-controls',
            emptySelector: '#articles-empty-msg',
            defaultPageSize: 15,
            itemName: 'articole',
            extractDataFn: (el) => ({
                id: parseInt(el.dataset.id || '0', 10),
                title: el.dataset.title || '',
                cleanTitle: cleanDiacritics(el.dataset.title || ''),
                category: el.dataset.category || '',
                date: el.dataset.date || '',
                dateScore: parseAdminDateScore(el.dataset.date || ''),
                views: parseInt(el.dataset.views || '0', 10)
            }),
            filterFn: (data, { query, cat }) => {
                if (cat !== 'all' && data.category !== cat) return false;
                if (query) {
                    const matchTitle = data.cleanTitle.includes(query);
                    const matchId = String(data.id) === query || String(data.id) === query.replace('#', '');
                    const matchCat = cleanDiacritics(data.category).includes(query);
                    if (!matchTitle && !matchId && !matchCat) return false;
                }
                return true;
            },
            sortFn: (a, b, sortVal) => {
                if (sortVal === 'date-desc') return b.dateScore - a.dateScore || b.id - a.id;
                if (sortVal === 'date-asc') return a.dateScore - b.dateScore || a.id - b.id;
                if (sortVal === 'views-desc') return b.views - a.views || b.id - a.id;
                if (sortVal === 'views-asc') return a.views - b.views || a.id - b.id;
                if (sortVal === 'title-asc') return a.cleanTitle.localeCompare(b.cleanTitle);
                if (sortVal === 'id-desc') return b.id - a.id;
                if (sortVal === 'id-asc') return a.id - b.id;
                return b.dateScore - a.dateScore;
            }
        });
    }

    // 2. Plants Paginator
    if (document.getElementById('plants-admin-container')) {
        window.adminPlantsPaginator = new AdminPaginator({
            containerSelector: '#plants-admin-container',
            listContainerSelector: '#plants-table-body',
            itemsSelector: '.plant-row',
            searchSelector: '#plants-search-input',
            categorySelector: '#plants-category-filter',
            letterSelector: '#plants-letter-filter',
            sortSelector: '#plants-sort-select',
            pageSizeSelector: '#plants-pagesize-select',
            resetSelector: '#plants-reset-btn',
            infoSelector: '#plants-pagination-info',
            controlsSelector: '#plants-pagination-controls',
            emptySelector: '#plants-empty-msg',
            defaultPageSize: 25,
            itemName: 'specii',
            extractDataFn: (el) => ({
                id: parseInt(el.dataset.id || '0', 10),
                name: el.dataset.name || '',
                cleanName: cleanDiacritics(el.dataset.name || ''),
                latin: el.dataset.latin || '',
                cleanLatin: cleanDiacritics(el.dataset.latin || ''),
                category: el.dataset.category || '',
                letter: el.dataset.letter || ''
            }),
            filterFn: (data, { query, cat, letter }) => {
                if (cat !== 'all' && data.category !== cat) return false;
                if (letter !== 'all' && data.letter !== letter) return false;
                if (query) {
                    const matchName = data.cleanName.includes(query);
                    const matchLatin = data.cleanLatin.includes(query);
                    const matchId = String(data.id) === query || String(data.id) === query.replace('#', '');
                    const matchCat = cleanDiacritics(data.category).includes(query);
                    if (!matchName && !matchLatin && !matchId && !matchCat) return false;
                }
                return true;
            },
            sortFn: (a, b, sortVal) => {
                if (sortVal === 'name-asc') return a.cleanName.localeCompare(b.cleanName);
                if (sortVal === 'name-desc') return b.cleanName.localeCompare(a.cleanName);
                if (sortVal === 'latin-asc') return a.cleanLatin.localeCompare(b.cleanLatin);
                if (sortVal === 'id-desc') return b.id - a.id;
                if (sortVal === 'id-asc') return a.id - b.id;
                return a.cleanName.localeCompare(b.cleanName);
            }
        });
    }

    // 3. Products Paginator
    if (document.getElementById('products-admin-container')) {
        window.adminProductsPaginator = new AdminPaginator({
            containerSelector: '#products-admin-container',
            listContainerSelector: '#products-grid-container',
            itemsSelector: '.product-admin-card',
            searchSelector: '#products-search-input',
            brandSelector: '#products-brand-filter',
            pageSizeSelector: '#products-pagesize-select',
            infoSelector: '#products-pagination-info',
            controlsSelector: '#products-pagination-controls',
            emptySelector: '#products-empty-msg',
            defaultPageSize: 12,
            itemName: 'produse',
            extractDataFn: (el) => ({
                id: parseInt(el.dataset.id || '0', 10),
                name: el.dataset.name || '',
                cleanName: cleanDiacritics(el.dataset.name || ''),
                brand: el.dataset.brand || '',
                code: cleanDiacritics(el.dataset.code || '')
            }),
            filterFn: (data, { query, brand }) => {
                if (brand !== 'all' && data.brand !== brand) return false;
                if (query) {
                    const matchName = data.cleanName.includes(query);
                    const matchBrand = cleanDiacritics(data.brand).includes(query);
                    const matchCode = data.code.includes(query);
                    const matchId = String(data.id) === query;
                    if (!matchName && !matchBrand && !matchCode && !matchId) return false;
                }
                return true;
            }
        });
    }

    // 4. Showcase Paginator
    if (document.getElementById('showcase-admin-container')) {
        window.adminShowcasePaginator = new AdminPaginator({
            containerSelector: '#showcase-admin-container',
            listContainerSelector: '#showcase-grid-container',
            itemsSelector: '.showcase-admin-card',
            searchSelector: '#showcase-search-input',
            sortSelector: '#showcase-sort-select',
            pageSizeSelector: '#showcase-pagesize-select',
            infoSelector: '#showcase-pagination-info',
            controlsSelector: '#showcase-pagination-controls',
            emptySelector: '#showcase-empty-msg',
            defaultPageSize: 18,
            itemName: 'imagini',
            extractDataFn: (el) => ({
                filename: el.dataset.filename || '',
                cleanFilename: cleanDiacritics(el.dataset.filename || ''),
                title: el.dataset.title || '',
                cleanTitle: cleanDiacritics(el.dataset.title || ''),
                mtime: parseFloat(el.dataset.mtime || '0')
            }),
            filterFn: (data, { query }) => {
                if (query) {
                    return data.cleanFilename.includes(query) || data.cleanTitle.includes(query);
                }
                return true;
            },
            sortFn: (a, b, sortVal) => {
                if (sortVal === 'mtime-desc') return b.mtime - a.mtime;
                if (sortVal === 'mtime-asc') return a.mtime - b.mtime;
                if (sortVal === 'title-asc') return a.cleanFilename.localeCompare(b.cleanFilename);
                return b.mtime - a.mtime;
            }
        });
    }
}

// Global triggers for table header sorting
window.triggerArticleSort = function(col) {
    if (!window.adminArticlesPaginator) return;
    const sortSelect = document.getElementById('articles-sort-select');
    if (!sortSelect) return;
    if (col === 'views') {
        sortSelect.value = sortSelect.value === 'views-desc' ? 'views-asc' : 'views-desc';
    } else if (col === 'date') {
        sortSelect.value = sortSelect.value === 'date-desc' ? 'date-asc' : 'date-desc';
    } else if (col === 'title') {
        sortSelect.value = 'title-asc';
    } else if (col === 'id') {
        sortSelect.value = sortSelect.value === 'id-desc' ? 'id-asc' : 'id-desc';
    }
    window.adminArticlesPaginator.apply();
};

window.resetArticlesFilter = function() {
    if (window.adminArticlesPaginator) window.adminArticlesPaginator.reset();
};

window.triggerPlantSort = function(col) {
    if (!window.adminPlantsPaginator) return;
    const sortSelect = document.getElementById('plants-sort-select');
    if (!sortSelect) return;
    if (col === 'name') {
        sortSelect.value = sortSelect.value === 'name-asc' ? 'name-desc' : 'name-asc';
    } else if (col === 'latin') {
        sortSelect.value = 'latin-asc';
    } else if (col === 'id') {
        sortSelect.value = sortSelect.value === 'id-desc' ? 'id-asc' : 'id-desc';
    }
    window.adminPlantsPaginator.apply();
};

window.resetPlantsFilter = function() {
    if (window.adminPlantsPaginator) window.adminPlantsPaginator.reset();
};

// Initialize after document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAdminPaginators);
} else {
    initAdminPaginators();
}
