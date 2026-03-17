---
title: "blanpa"
description: "IIoT Software Developer — Building industrial connectivity solutions with Node-RED, OPC-UA, NATS, Siemens S7, CIP/EtherNet-IP, condition monitoring, and edge-to-cloud computing."
---

<div class="home-cards">

<a href="/about/" class="home-card">
  <span class="home-card__icon">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
  </span>
  <h2>Edge to Cloud</h2>
  <p>From CAN bus and RS485 on the shop floor to NATS streams and cloud dashboards — bridging the full industrial data pipeline.</p>
</a>

<a href="/projects/" class="home-card">
  <span class="home-card__icon">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
  </span>
  <h2>Projects</h2>
  <p>Open-source Node-RED packages and industrial automation projects — from condition monitoring to protocol integration.</p>
</a>

<a href="/blog/" class="home-card">
  <span class="home-card__icon">
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
  </span>
  <h2>Blog</h2>
  <p>Articles on IIoT, Data Engineering, and MLOps — documenting my learning journey and technical deep-dives.</p>
</a>

</div>

<button class="home-contact-btn" onclick="document.getElementById('contact-modal').classList.add('is-open')" type="button">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
  <span>Get in Touch</span>
</button>

<div id="contact-modal" class="contact-modal" onclick="if(event.target===this)this.classList.remove('is-open')">
  <div class="contact-modal__inner">
    <button class="contact-modal__close" onclick="document.getElementById('contact-modal').classList.remove('is-open')" type="button" aria-label="Close">&times;</button>
    <h2>Get in Touch</h2>
    <form id="modal-contact-form" class="contact-form">
      <div class="form-group">
        <label for="modal-name">Name</label>
        <input type="text" id="modal-name" name="name" required placeholder="Your name">
      </div>
      <div class="form-group">
        <label for="modal-email">Email</label>
        <input type="email" id="modal-email" name="email" required placeholder="your@email.com">
      </div>
      <div class="form-group">
        <label for="modal-subject">Subject</label>
        <select id="modal-subject" name="subject" required>
          <option value="" disabled selected>Select a topic</option>
          <option value="Custom Node-RED Module">Custom Node-RED Module</option>
          <option value="Protocol Integration">Protocol Integration</option>
          <option value="Edge-to-Cloud Architecture">Edge-to-Cloud Architecture</option>
          <option value="Data Engineering">Data Engineering & Automation</option>
          <option value="Other">Other</option>
        </select>
      </div>
      <div class="form-group">
        <label for="modal-message">Message</label>
        <textarea id="modal-message" name="message" rows="5" required placeholder="Tell me about your project..."></textarea>
      </div>
      <input type="text" name="_gotcha" style="display:none">
      <button type="submit" class="contact-submit">Send Message</button>
      <p class="form-status" id="modal-form-status"></p>
    </form>

<script>
document.getElementById('modal-contact-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  const btn = this.querySelector('.contact-submit');
  const status = document.getElementById('modal-form-status');
  btn.disabled = true;
  btn.textContent = 'Sending...';
  status.textContent = '';
  status.className = 'form-status';
  try {
    const res = await fetch('https://formspree.io/f/mjgaaoww', {
      method: 'POST',
      body: new FormData(this),
      headers: { 'Accept': 'application/json' }
    });
    if (res.ok) {
      status.textContent = 'Message sent successfully!';
      status.classList.add('form-status--success');
      this.reset();
    } else {
      status.textContent = 'Something went wrong. Please try again.';
      status.classList.add('form-status--error');
    }
  } catch {
    status.textContent = 'Connection error. Please try again.';
    status.classList.add('form-status--error');
  }
  btn.disabled = false;
  btn.textContent = 'Send Message';
});
</script>
  </div>
</div>
