document.addEventListener('DOMContentLoaded', () => {

    // ---- Scroll-triggered reveal animations ----
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                const el = entry.target;
                el.classList.add('revealed');
                revealObserver.unobserve(el);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.reveal').forEach((el) => {
        revealObserver.observe(el);
    });

    // ---- Hero staggered load animation ----
    document.querySelectorAll('.hero-animate').forEach((el, i) => {
        el.style.setProperty('--delay', `${i * 0.12}s`);
    });

    // ---- Carousel drag-to-scroll ----
    document.querySelectorAll('.carousel').forEach((carousel) => {
        let isDown = false;
        let hasDragged = false;
        let startX;
        let scrollLeft;
        const DRAG_THRESHOLD = 5;

        carousel.addEventListener('mousedown', (e) => {
            isDown = true;
            hasDragged = false;
            startX = e.pageX - carousel.offsetLeft;
            scrollLeft = carousel.scrollLeft;
        });

        carousel.addEventListener('mouseleave', () => {
            isDown = false;
            carousel.classList.remove('is-dragging');
        });

        carousel.addEventListener('mouseup', () => {
            isDown = false;
            carousel.classList.remove('is-dragging');
        });

        carousel.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            const x = e.pageX - carousel.offsetLeft;
            const walk = (x - startX) * 1.5;
            if (!hasDragged && Math.abs(x - startX) > DRAG_THRESHOLD) {
                hasDragged = true;
                carousel.classList.add('is-dragging');
            }
            if (hasDragged) {
                e.preventDefault();
                carousel.scrollLeft = scrollLeft - walk;
            }
        });

        carousel.addEventListener('click', (e) => {
            if (hasDragged) {
                e.preventDefault();
            }
        });
    });


});
