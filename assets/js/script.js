// This file contains JavaScript code for interactivity, including the countdown timer, form submission handling, and lightbox functionality for the gallery.

// Bloquear descarga de imágenes en hero, portada, galería y lightbox
document.addEventListener("contextmenu", e => {
  if (e.target.closest(".hero, .portada, .gallery, .lightbox") && e.target.tagName === "IMG") {
    e.preventDefault();
  }
});
document.addEventListener("dragstart", e => {
  if (e.target.closest(".hero, .portada, .gallery, .lightbox") && e.target.tagName === "IMG") {
    e.preventDefault();
  }
});

const target = new Date("2026-10-09T12:00:00");
setInterval(() => {
  const diff = target - new Date();
  if (diff < 0) return;
  document.getElementById("days").textContent = Math.floor(diff / 86400000);
  document.getElementById("hours").textContent = Math.floor(diff / 3600000) % 24;
  document.getElementById("minutes").textContent = Math.floor(diff / 60000) % 60;
  document.getElementById("seconds").textContent = Math.floor(diff / 1000) % 60;
}, 1000);

const observer = new IntersectionObserver(entries => {
  entries.forEach(e => e.isIntersecting && e.target.classList.add('visible'));
}, { threshold: .15 });
document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));



const pickRandom = (items) => {
  if (!Array.isArray(items) || items.length === 0) return null;
  if (window.crypto?.getRandomValues) {
    const buffer = new Uint32Array(1);
    window.crypto.getRandomValues(buffer);
    return items[buffer[0] % items.length];
  }
  return items[Math.floor(Math.random() * items.length)];
};

const setRandomGalleryImages = async () => {
  const gallerySection = document.getElementById("galeria");
  if (!gallerySection) return;

  let manifest;
  try {
    const res = await fetch("assets/images/fotos/manifest.json", { cache: "no-store" });
    if (!res.ok) return;
    manifest = await res.json();
  } catch {
    return;
  }

  gallerySection.querySelectorAll(".gallery-item").forEach(item => {
    const year = item.getAttribute("data-year") || item.querySelector("h3")?.textContent?.trim();
    if (!year || !manifest?.[year]) return;
    const img = item.querySelector("img");
    if (!img) return;

    const file = pickRandom(manifest[year]);
    if (!file) return;
    img.src = `assets/images/fotos/${year}/${file}`;
    img.alt = `Imagen del año ${year}`;
  });
};

const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightboxImg");
setRandomGalleryImages().finally(() => {
  document.querySelectorAll(".gallery img").forEach(img => {
    img.onclick = () => {
      lightboxImg.src = img.src;
      lightbox.style.display = "flex";
    };
  });
});
lightbox.onclick = () => lightbox.style.display = "none";

const copyIbanButton = document.getElementById("copyIban");
if (copyIbanButton) {
  copyIbanButton.onclick = async () => {
    const ibanEl = document.getElementById("iban");
    if (!ibanEl) return;
    await navigator.clipboard.writeText(ibanEl.textContent);
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = "IBAN copiado";
    toast.classList.add("show");
    window.clearTimeout(window.__toastTimer);
    window.__toastTimer = window.setTimeout(() => toast.classList.remove("show"), 1800);
  };
}