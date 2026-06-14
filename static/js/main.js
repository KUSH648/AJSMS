/* ============================================================
   AI-Powered Jewellery Shop Management System
   Main JavaScript — Utilities, UI Logic & Feature Modules
   ============================================================ */

(function () {
  'use strict';

  // ───────────────────────────────────────────────
  // 1. Theme Toggle
  // ───────────────────────────────────────────────
  window.toggleTheme = function () {
    const body = document.body;
    body.classList.toggle('light-mode');
    const mode = body.classList.contains('light-mode') ? 'light' : 'dark';
    localStorage.setItem('theme', mode);

    // Swap icon if present
    const icon = document.querySelector('#themeToggleIcon') || document.querySelector('#themeIcon');
    if (icon) {
      icon.className = mode === 'light' ? 'fas fa-sun' : 'fas fa-moon';
    }
    document.documentElement.setAttribute('data-bs-theme', mode);
    const metaTheme = document.querySelector('meta[name="theme-color"]');
    if (metaTheme) metaTheme.content = mode === 'light' ? '#F8F4EC' : '#0A0A0A';
    if (typeof updateChartTheme === 'function') updateChartTheme();
  };

  // Restore saved theme on load
  function restoreTheme() {
    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
      document.body.classList.add('light-mode');
      const icon = document.querySelector('#themeToggleIcon') || document.querySelector('#themeIcon');
      if (icon) icon.className = 'fas fa-sun';
      document.documentElement.setAttribute('data-bs-theme', 'light');
    } else {
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    }
    if (typeof updateChartTheme === 'function') updateChartTheme();
  }

  // ───────────────────────────────────────────────
  // 2. Sidebar Memory & Toggle
  // ───────────────────────────────────────────────
  function initSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.btn-toggle');
    if (!sidebar) return;

    // Restore collapsed state
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
      sidebar.classList.add('collapsed');
      document.body.classList.add('sidebar-collapsed');
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        // Mobile: toggle open class instead
        if (window.innerWidth <= 768) {
          sidebar.classList.toggle('open');
        }
      });
    }

    // Close sidebar on overlay click (mobile)
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
      overlay.addEventListener('click', function () {
        sidebar.classList.remove('open');
      });
    }
  }

  // ───────────────────────────────────────────────
  // 3. DataTables Auto-Init
  // ───────────────────────────────────────────────
  function initDataTables() {
    if (typeof $ === 'undefined' || typeof $.fn.DataTable === 'undefined') return;

    $('.data-table').each(function () {
      if ($.fn.DataTable.isDataTable(this)) return; // skip already initialized
      $(this).DataTable({
        pageLength: 25,
        responsive: true,
        order: [[0, 'asc']],
        language: {
          search: '<i class="fas fa-search"></i>',
          searchPlaceholder: 'Search records...',
          lengthMenu: 'Show _MENU_ entries',
          info: 'Showing _START_ to _END_ of _TOTAL_',
          paginate: {
            first: '<i class="fas fa-angle-double-left"></i>',
            last: '<i class="fas fa-angle-double-right"></i>',
            next: '<i class="fas fa-angle-right"></i>',
            previous: '<i class="fas fa-angle-left"></i>'
          },
          emptyTable: 'No records available'
        },
        dom: '<"d-flex justify-content-between align-items-center mb-3"lf>rt<"d-flex justify-content-between align-items-center mt-3"ip>',
        drawCallback: function () {
          // Animate rows on draw
          $(this).find('tbody tr').each(function (i) {
            $(this).css({ opacity: 0, transform: 'translateY(8px)' });
            $(this).delay(i * 30).animate({ opacity: 1 }, 200);
            this.style.transform = 'translateY(0)';
          });
        }
      });
    });
  }

  // ───────────────────────────────────────────────
  // 4. Number Formatting — Indian ₹
  // ───────────────────────────────────────────────
  window.formatINR = function (num) {
    if (num === null || num === undefined || isNaN(num)) return '₹0.00';
    num = parseFloat(num);
    const parts = num.toFixed(2).split('.');
    let intPart = parts[0];
    const decPart = parts[1];
    const isNeg = intPart.startsWith('-');
    if (isNeg) intPart = intPart.slice(1);

    // Indian grouping: last 3, then groups of 2
    if (intPart.length > 3) {
      const last3 = intPart.slice(-3);
      const remaining = intPart.slice(0, -3);
      const grouped = remaining.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
      intPart = grouped + ',' + last3;
    }
    return (isNeg ? '-' : '') + '₹' + intPart + '.' + decPart;
  };

  // ───────────────────────────────────────────────
  // 5. Chart.js Helpers (Theme-Aware)
  // ───────────────────────────────────────────────
  function getChartFontColor() {
    return document.body.classList.contains('light-mode') ? '#4B3F35' : '#E8E8F0';
  }
  function getChartGridColor() {
    return document.body.classList.contains('light-mode') ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)';
  }
  function getChartTooltipBg() {
    return document.body.classList.contains('light-mode') ? '#FFFFFF' : '#0A0A1A';
  }

  const chartDefaults = {
    fontColor: getChartFontColor(),
    gridColor: getChartGridColor(),
    palette: ['#D4AF37', '#F0D060', '#2ECC71', '#3498DB', '#E74C3C', '#9B59B6', '#1ABC9C', '#F39C12']
  };

  function baseChartOptions(title) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: chartDefaults.fontColor, font: { family: 'Inter', size: 12 }, padding: 16 }
        },
        title: {
          display: !!title,
          text: title || '',
          color: chartDefaults.fontColor,
          font: { family: 'Inter', size: 15, weight: '600' },
          padding: { bottom: 16 }
        },
        tooltip: {
          backgroundColor: getChartTooltipBg(),
          titleColor: '#D4AF37',
          bodyColor: chartDefaults.fontColor,
          borderColor: chartDefaults.gridColor,
          borderWidth: 1,
          cornerRadius: 8,
          padding: 10
        }
      }
    };
  }

  function cartesianScales() {
    return {
      x: {
        ticks: { color: chartDefaults.fontColor, font: { size: 11 } },
        grid: { color: chartDefaults.gridColor }
      },
      y: {
        ticks: { color: chartDefaults.fontColor, font: { size: 11 } },
        grid: { color: chartDefaults.gridColor }
      }
    };
  }

  // Update chart defaults when theme changes
  function updateChartTheme() {
    chartDefaults.fontColor = getChartFontColor();
    chartDefaults.gridColor = getChartGridColor();
  }

  window.createLineChart = function (canvasId, labels, datasets, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const colors = chartDefaults.palette;
    const dsFormatted = datasets.map(function (ds, i) {
      return Object.assign({
        borderColor: colors[i % colors.length],
        backgroundColor: colors[i % colors.length] + '22',
        borderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 6,
        tension: 0.4,
        fill: true
      }, ds);
    });
    return new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: dsFormatted },
      options: Object.assign(baseChartOptions(title), { scales: cartesianScales() })
    });
  };

  window.createBarChart = function (canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: chartDefaults.palette.map(function (c) { return c + 'AA'; }),
          borderColor: chartDefaults.palette,
          borderWidth: 1,
          borderRadius: 6,
          maxBarThickness: 50
        }]
      },
      options: Object.assign(baseChartOptions(title), { scales: cartesianScales() })
    });
  };

  window.createPieChart = function (canvasId, labels, data, title) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: chartDefaults.palette,
          borderColor: document.body.classList.contains('light-mode') ? '#E8DCC8' : '#1A1F2E',
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: Object.assign(baseChartOptions(title), {
        cutout: '60%',
        plugins: Object.assign(baseChartOptions(title).plugins, {
          legend: {
            position: 'bottom',
            labels: { color: chartDefaults.fontColor, padding: 14, font: { size: 12 } }
          }
        })
      })
    });
  };

  window.createPredictionChart = function (canvasId, labels, actual, predicted) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Actual',
            data: actual,
            borderColor: '#D4AF37',
            backgroundColor: 'rgba(212,175,55,0.1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true,
            pointRadius: 3
          },
          {
            label: 'Predicted',
            data: predicted,
            borderColor: '#3498DB',
            backgroundColor: 'rgba(52,152,219,0.1)',
            borderWidth: 2,
            borderDash: [6, 4],
            tension: 0.4,
            fill: true,
            pointRadius: 3
          }
        ]
      },
      options: Object.assign(baseChartOptions('Actual vs Predicted'), { scales: cartesianScales() })
    });
  };

  // ───────────────────────────────────────────────
  // 6. Billing / POS
  // ───────────────────────────────────────────────
  window.cart = [];

  window.searchItems = function (query) {
    if (!query || query.length < 2) return;
    $.getJSON('/inventory/api/search', { q: query }, function (data) {
      var list = $('#itemSearchResults');
      list.empty();
      if (!data.length) {
        list.append('<div class="p-3 text-muted">No items found</div>');
        return;
      }
      data.forEach(function (item) {
        list.append(
          '<div class="cart-item" onclick=\'addToCart(' + JSON.stringify(item).replace(/'/g, "\\'") + ')\'>' +
          '<span class="item-name">' + item.name + '</span>' +
          '<span class="item-price">' + formatINR(item.selling_price || item.price) + '</span>' +
          '</div>'
        );
      });
    }).fail(function () {
      showToast('Failed to search items', 'error');
    });
  };

  window.searchCustomers = function (query) {
    if (!query || query.length < 2) return;
    $.getJSON('/customers/api/search', { q: query }, function (data) {
      var list = $('#customerSearchResults');
      list.empty();
      data.forEach(function (c) {
        var cid = c.customer_id || c.id;
        list.append(
          '<div class="cart-item" data-id="' + cid + '" onclick="selectCustomer(' + cid + ',\'' + c.name + '\')">' +
          '<span class="item-name">' + c.name + '</span>' +
          '<span class="text-muted">' + (c.phone || '') + '</span></div>'
        );
      });
    });
  };

  window.addToCart = function (item) {
    // Normalise field names from API
    var itemId = item.item_id || item.id;
    var price  = item.selling_price || item.price || 0;
    // Check if item already in cart
    var existing = cart.find(function (c) { return (c.item_id || c.id) === itemId; });
    if (existing) {
      existing.qty = (existing.qty || 1) + 1;
    } else {
      item.item_id = itemId;
      item.price   = price;
      item.qty     = 1;
      cart.push(item);
    }
    updateCartUI();
    showToast(item.name + ' added to cart', 'success');
  };

  window.removeFromCart = function (index) {
    cart.splice(index, 1);
    updateCartUI();
  };

  window.updateCartUI = function () {
    var container = document.getElementById('cartItems');
    var subtotalEl = document.getElementById('cartSubtotal');
    var gstEl = document.getElementById('cartGST');
    var totalEl = document.getElementById('cartTotal');
    var countEl = document.getElementById('cartCount');
    if (!container) return;

    container.innerHTML = '';
    var subtotal = 0;

    if (cart.length === 0) {
      container.innerHTML = '<div class="empty-state"><i class="fas fa-shopping-cart"></i><p>Cart is empty</p></div>';
    } else {
      cart.forEach(function (item, idx) {
        var lineTotal = (item.price || 0) * (item.qty || 1);
        subtotal += lineTotal;
        container.innerHTML +=
          '<div class="cart-item">' +
          '<div class="item-name">' + item.name +
          '<br><small class="text-muted">' + formatINR(item.price) + ' × ' + item.qty + '</small></div>' +
          '<div class="item-price">' + formatINR(lineTotal) + '</div>' +
          '<span class="btn-remove" onclick="removeFromCart(' + idx + ')"><i class="fas fa-times"></i></span>' +
          '</div>';
      });
    }

    var gst = subtotal * 0.03; // 3% GST on jewellery
    var total = subtotal + gst;

    if (subtotalEl) subtotalEl.textContent = formatINR(subtotal);
    if (gstEl) gstEl.textContent = formatINR(gst);
    if (totalEl) totalEl.textContent = formatINR(total);
    if (countEl) countEl.textContent = cart.length;
  };

  window.calculateBill = function () {
    if (cart.length === 0) {
      showToast('Cart is empty!', 'warning');
      return;
    }
    $.ajax({
      url: '/billing/api/calculate',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ items: cart }),
      success: function (res) {
        if (res.subtotal !== undefined) {
          $('#cartSubtotal').text(formatINR(res.subtotal));
          $('#cartGST').text(formatINR(res.gst));
          $('#cartTotal').text(formatINR(res.total));
        }
      },
      error: function () { showToast('Calculation failed', 'error'); }
    });
  };

  window.submitBill = function () {
    if (cart.length === 0) {
      showToast('Cart is empty!', 'warning');
      return;
    }
    var payload = {
      customer_id: $('#customerId').val() || null,
      items: cart,
      payment_method: $('input[name="paymentMethod"]:checked').val() || $('.payment-option.active').data('method') || 'cash',
      discount: parseFloat($('#discount').val()) || 0,
      notes: $('#billNotes').val() || ''
    };

    $.ajax({
      url: '/billing/api/submit',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(payload),
      success: function (res) {
        showToast('Bill created successfully!', 'success');
        cart = [];
        updateCartUI();
        if (res.redirect) window.location.href = res.redirect;
        if (res.bill_id) window.location.href = '/billing/view/' + res.bill_id;
      },
      error: function (xhr) {
        var msg = xhr.responseJSON ? xhr.responseJSON.error : 'Failed to submit bill';
        showToast(msg, 'error');
      }
    });
  };

  // ───────────────────────────────────────────────
  // 7. Chatbot
  // ───────────────────────────────────────────────
  window.sendChatMessage = function () {
    var input = document.getElementById('chatInput');
    if (!input) return;
    var message = input.value.trim();
    if (!message) return;

    addChatBubble(message, 'user');
    input.value = '';
    showTypingIndicator();

    $.ajax({
      url: '/ai/api/chat',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ message: message }),
      success: function (res) {
        hideTypingIndicator();
        // Handle both {reply: 'str'} and {reply: {text: 'str'}} formats
        var reply = res.reply || res.response || 'No response received.';
        if (typeof reply === 'object') reply = reply.text || JSON.stringify(reply);
        addChatBubble(reply, 'bot');
      },
      error: function () {
        hideTypingIndicator();
        addChatBubble('Sorry, I encountered an error. Please try again.', 'bot');
      }
    });
  };

  window.addChatBubble = function (message, type) {
    var container = document.getElementById('chatMessages') || document.querySelector('.chat-messages');
    if (!container) return;

    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + type;

    var now = new Date();
    var timeStr = now.getHours().toString().padStart(2, '0') + ':' + now.getMinutes().toString().padStart(2, '0');

    // Support basic markdown-like formatting for bot responses
    var content = message;
    if (type === 'bot') {
      content = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    }

    bubble.innerHTML = content + '<span class="bubble-time">' + timeStr + '</span>';
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  };

  window.showTypingIndicator = function () {
    var container = document.getElementById('chatMessages') || document.querySelector('.chat-messages');
    if (!container) return;
    var existing = container.querySelector('.typing-indicator');
    if (existing) return;

    var indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
  };

  window.hideTypingIndicator = function () {
    var indicators = document.querySelectorAll('.typing-indicator');
    indicators.forEach(function (el) { el.remove(); });
  };

  // Enter key to send
  function initChatEnter() {
    var input = document.getElementById('chatInput');
    if (input && !input.hasAttribute('data-chat-initialized')) {
      input.setAttribute('data-chat-initialized', 'true');
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          if (typeof sendMessage === 'function' && document.querySelector('.chat-container')) {
            sendMessage();
          } else {
            sendChatMessage();
          }
        }
      });
    }
  }

  // ───────────────────────────────────────────────
  // 8. Image Recognition / Drop Zone
  // ───────────────────────────────────────────────
  window.initDropZone = function () {
    var zone = document.querySelector('.drop-zone');
    if (!zone) return;

    ['dragenter', 'dragover'].forEach(function (evt) {
      zone.addEventListener(evt, function (e) {
        e.preventDefault();
        zone.classList.add('drag-active');
      });
    });

    ['dragleave', 'drop'].forEach(function (evt) {
      zone.addEventListener(evt, function (e) {
        e.preventDefault();
        zone.classList.remove('drag-active');
      });
    });

    zone.addEventListener('drop', function (e) {
      var files = e.dataTransfer.files;
      if (files.length > 0) handleImageUpload(files[0]);
    });

    zone.addEventListener('click', function () {
      var fileInput = document.getElementById('imageFileInput') || document.createElement('input');
      if (!fileInput.id) {
        fileInput.id = 'imageFileInput';
        fileInput.type = 'file';
        fileInput.accept = 'image/*';
        fileInput.style.display = 'none';
        fileInput.addEventListener('change', function () {
          if (this.files.length > 0) handleImageUpload(this.files[0]);
        });
        document.body.appendChild(fileInput);
      }
      fileInput.click();
    });
  };

  window.handleImageUpload = function (file) {
    if (!file || !file.type.startsWith('image/')) {
      showToast('Please upload a valid image file', 'warning');
      return;
    }

    var reader = new FileReader();
    reader.onload = function (e) {
      // Show preview
      var preview = document.getElementById('imagePreview');
      if (preview) {
        preview.src = e.target.result;
        preview.style.display = 'block';
        preview.classList.add('img-preview');
      }

      // Show loading
      var resultArea = document.getElementById('recognitionResult');
      if (resultArea) {
        resultArea.innerHTML = '<div class="text-center p-4"><div class="spinner-gold"></div><p class="text-muted mt-3">Analyzing image...</p></div>';
      }

      // Send to API
      $.ajax({
        url: '/ai/api/recognize',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ image: e.target.result }),
        success: function (res) {
          displayRecognitionResult(res);
        },
        error: function () {
          if (resultArea) {
            resultArea.innerHTML = '<div class="alert alert-danger">Recognition failed. Please try again.</div>';
          }
        }
      });
    };
    reader.readAsDataURL(file);
  };

  window.displayRecognitionResult = function (result) {
    var container = document.getElementById('recognitionResult');
    if (!container) return;

    var html = '<div class="ai-result-card animate-in">';
    html += '<h5 class="text-gold mb-3"><i class="fas fa-gem me-2"></i>' + (result.category || 'Unknown') + '</h5>';

    if (result.confidence !== undefined) {
      var pct = Math.round(result.confidence * 100);
      html += '<div class="mb-2"><span class="text-secondary">Confidence</span>';
      html += '<div class="confidence-bar"><div class="fill" style="width:' + pct + '%"></div></div>';
      html += '<span class="text-gold">' + pct + '%</span></div>';
    }

    if (result.details) {
      html += '<div class="mt-3">';
      Object.keys(result.details).forEach(function (key) {
        html += '<div class="d-flex justify-content-between py-1 border-bottom" style="border-color:var(--border)!important">';
        html += '<span class="text-secondary">' + key + '</span>';
        html += '<span class="text-primary">' + result.details[key] + '</span></div>';
      });
      html += '</div>';
    }

    if (result.recommendations && result.recommendations.length) {
      html += '<div class="mt-3"><h6 class="text-secondary mb-2">Recommendations</h6>';
      result.recommendations.forEach(function (rec) {
        html += '<div class="recommendation-card mb-2">' + rec + '</div>';
      });
      html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
  };

  window.startCamera = function () {
    var video = document.getElementById('cameraFeed');
    if (!video) return;
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
      .then(function (stream) {
        video.srcObject = stream;
        video.play();
        video.style.display = 'block';
        showToast('Camera started', 'info');
      })
      .catch(function () {
        showToast('Unable to access camera', 'error');
      });
  };

  window.captureFromCamera = function () {
    var video = document.getElementById('cameraFeed');
    if (!video || !video.srcObject) {
      showToast('Camera not started', 'warning');
      return;
    }
    var canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    var dataUrl = canvas.toDataURL('image/jpeg', 0.8);

    // Show preview
    var preview = document.getElementById('imagePreview');
    if (preview) {
      preview.src = dataUrl;
      preview.style.display = 'block';
    }

    // Stop camera
    video.srcObject.getTracks().forEach(function (t) { t.stop(); });
    video.style.display = 'none';

    // Send for recognition
    $.ajax({
      url: '/ai/api/recognize',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ image: dataUrl }),
      success: function (res) { displayRecognitionResult(res); },
      error: function () { showToast('Recognition failed', 'error'); }
    });
  };

  // ───────────────────────────────────────────────
  // 9. Notification Polling
  // ───────────────────────────────────────────────
  function pollNotifications() {
    if (typeof loadNotifications === 'function') {
      setInterval(loadNotifications, 5 * 60 * 1000); // every 5 minutes
    }
  }

  // ───────────────────────────────────────────────
  // 10. Form Validation
  // ───────────────────────────────────────────────
  window.validateRequired = function (formId) {
    var form = document.getElementById(formId);
    if (!form) return true;
    var valid = true;
    var requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(function (field) {
      // Clear previous state
      field.classList.remove('is-invalid');
      var feedback = field.parentElement.querySelector('.invalid-feedback');

      if (!field.value || !field.value.trim()) {
        valid = false;
        field.classList.add('is-invalid');
        if (!feedback) {
          feedback = document.createElement('div');
          feedback.className = 'invalid-feedback';
          feedback.textContent = 'This field is required';
          field.parentElement.appendChild(feedback);
        }
      }
    });

    if (!valid) {
      showToast('Please fill in all required fields', 'warning');
      // Focus first invalid
      var firstInvalid = form.querySelector('.is-invalid');
      if (firstInvalid) firstInvalid.focus();
    }
    return valid;
  };

  // ───────────────────────────────────────────────
  // 11. Confirmation Dialogs
  // ───────────────────────────────────────────────
  window.confirmDelete = function (url, itemName) {
    var name = itemName || 'this item';
    if (confirm('Are you sure you want to delete ' + name + '? This action cannot be undone.')) {
      // Create and submit a form for POST delete
      var form = document.createElement('form');
      form.method = 'POST';
      form.action = url;
      // CSRF token
      var csrf = document.querySelector('input[name="csrf_token"]');
      if (csrf) {
        var input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = csrf.value;
        form.appendChild(input);
      }
      document.body.appendChild(form);
      form.submit();
    }
  };

  // ───────────────────────────────────────────────
  // 12. Toast Helper
  // ───────────────────────────────────────────────
  window.showToast = function (message, type) {
    type = type || 'info';
    var container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    var icons = {
      success: 'fas fa-check-circle',
      error: 'fas fa-exclamation-circle',
      danger: 'fas fa-exclamation-circle',
      warning: 'fas fa-exclamation-triangle',
      info: 'fas fa-info-circle'
    };

    var toast = document.createElement('div');
    toast.className = 'toast-item ' + type;
    toast.innerHTML = '<i class="' + (icons[type] || icons.info) + '"></i><span>' + message + '</span>';
    container.appendChild(toast);

    // Remove after animation completes (5s total)
    setTimeout(function () {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 5000);
  };

  // ───────────────────────────────────────────────
  // 13. Auto-Dismiss Flash Alerts
  // ───────────────────────────────────────────────
  function autoDismissAlerts() {
    var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function (alert) {
      setTimeout(function () {
        alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function () {
          if (alert.parentNode) alert.parentNode.removeChild(alert);
        }, 500);
      }, 5000);
    });
  }

  // ───────────────────────────────────────────────
  // 14. Date Picker Enhancement
  // ───────────────────────────────────────────────
  function enhanceDateInputs() {
    var dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function (input) {
      // Set max to today for past-only fields
      if (input.dataset.maxToday !== undefined) {
        input.max = new Date().toISOString().split('T')[0];
      }
      // Set default value to today if empty and data-default-today is set
      if (input.dataset.defaultToday !== undefined && !input.value) {
        input.value = new Date().toISOString().split('T')[0];
      }
    });
  }

  // ───────────────────────────────────────────────
  // 15. Clock Update (Topbar)
  // ───────────────────────────────────────────────
  function initClock() {
    var clockEl = document.getElementById('topbarClock') || document.querySelector('.topbar-clock');
    if (!clockEl) return;

    function update() {
      var now = new Date();
      var h = now.getHours().toString().padStart(2, '0');
      var m = now.getMinutes().toString().padStart(2, '0');
      var s = now.getSeconds().toString().padStart(2, '0');
      clockEl.textContent = h + ':' + m + ':' + s;
    }
    update();
    setInterval(update, 1000);
  }

  // ───────────────────────────────────────────────
  // 16. Animate elements on scroll / load
  // ───────────────────────────────────────────────
  function initAnimations() {
    var elements = document.querySelectorAll('.animate-in');
    if (!elements.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    elements.forEach(function (el) {
      el.style.opacity = '0';
      el.style.animationPlayState = 'paused';
      observer.observe(el);
    });
  }

  // ───────────────────────────────────────────────
  // 17. Payment Method Selector (POS)
  // ───────────────────────────────────────────────
  function initPaymentSelector() {
    var options = document.querySelectorAll('.payment-option');
    options.forEach(function (opt) {
      opt.addEventListener('click', function () {
        options.forEach(function (o) { o.classList.remove('active'); });
        this.classList.add('active');
      });
    });
  }

  // ───────────────────────────────────────────────
  // 18. Misc Utilities
  // ───────────────────────────────────────────────

  // Debounce helper for search inputs
  window.debounce = function (fn, delay) {
    var timer;
    return function () {
      var args = arguments;
      var ctx = this;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(ctx, args); }, delay || 300);
    };
  };

  // Smooth scroll to element
  window.scrollToElement = function (selector) {
    var el = document.querySelector(selector);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Copy to clipboard
  window.copyToClipboard = function (text) {
    navigator.clipboard.writeText(text).then(function () {
      showToast('Copied to clipboard!', 'success');
    }).catch(function () {
      showToast('Failed to copy', 'error');
    });
  };

  // ───────────────────────────────────────────────
  // 19. Missing Billing POS Functions
  // ───────────────────────────────────────────────

  // Customer selection for billing
  window.selectCustomer = function (cid, name) {
    var hiddenInput = document.getElementById('hidden_customer_id');
    if (hiddenInput) hiddenInput.value = cid;
    var searchInput = document.getElementById('customerSearch');
    if (searchInput) searchInput.value = name;
    var badge = document.getElementById('selectedCustomerBadge');
    if (badge) {
      badge.style.display = 'block';
      document.getElementById('badge_name').textContent = name;
      document.getElementById('badge_phone').textContent = 'Customer ID: ' + cid;
    }
    var loyaltySection = document.getElementById('loyaltySection');
    if (loyaltySection) loyaltySection.style.display = 'block';
    var results = document.getElementById('customerResults');
    if (results) results.style.display = 'none';
  };

  window.clearSelectedCustomer = function () {
    document.getElementById('hidden_customer_id').value = 0;
    document.getElementById('customerSearch').value = '';
    document.getElementById('selectedCustomerBadge').style.display = 'none';
    document.getElementById('loyaltySection').style.display = 'none';
    document.getElementById('customerResults').style.display = 'none';
  };

  // Invoice calculation (for new bill page)
  window.recalcInvoice = function () {
    var subtotalEl = document.getElementById('summary_subtotal');
    var discountAmtEl = document.getElementById('summary_discount_amt');
    var totalEl = document.getElementById('summary_total');
    if (!subtotalEl) return;
    
    var subtotal = 0;
    var rows = document.querySelectorAll('#cartItemsList tr:not(#emptyCartRow)');
    rows.forEach(function (row) {
      var totalCell = row.querySelector('.item-line-total');
      if (totalCell) subtotal += parseFloat(totalCell.getAttribute('data-total') || 0);
    });
    
    var discountPct = parseFloat(document.getElementById('discountInput') ? document.getElementById('discountInput').value : 0) || 0;
    var discountAmt = subtotal * discountPct / 100;
    var afterDiscount = subtotal - discountAmt;
    var gst = afterDiscount * 0.03;
    var grandTotal = afterDiscount + gst;
    
    subtotalEl.textContent = formatINR(subtotal);
    if (discountAmtEl) discountAmtEl.textContent = '- ' + formatINR(discountAmt);
    if (totalEl) totalEl.textContent = formatINR(grandTotal);
    
    var gstEl = document.getElementById('summary_gst');
    if (gstEl) gstEl.textContent = formatINR(gst);
  };

  // Barcode camera scanner functions
  var scannerStream = null;
  
  window.startCameraScanner = function () {
    var area = document.getElementById('cameraScannerArea');
    if (area) area.style.display = 'block';
    var video = document.getElementById('scannerVideo');
    if (!video) return;
    
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: 640, height: 480 } })
      .then(function (stream) {
        scannerStream = stream;
        video.srcObject = stream;
        video.play();
      })
      .catch(function () {
        showToast('Unable to access camera', 'error');
        if (area) area.style.display = 'none';
      });
  };

  window.captureAndScan = function () {
    var video = document.getElementById('scannerVideo');
    var canvas = document.getElementById('scannerCanvas');
    if (!video || !canvas) return;
    
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Send to barcode API
    var dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    $.ajax({
      url: '/inventory/api/scan-barcode',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ image: dataUrl }),
      success: function (res) {
        if (res.item) {
          addToCart(res.item);
          showToast('Barcode scanned: ' + res.barcode, 'success');
        } else {
          showToast('No item found for this barcode', 'warning');
        }
        stopCameraScanner();
      },
      error: function () {
        showToast('Could not decode barcode. Try again.', 'error');
      }
    });
  };

  window.stopCameraScanner = function () {
    var area = document.getElementById('cameraScannerArea');
    if (area) area.style.display = 'none';
    if (scannerStream) {
      scannerStream.getTracks().forEach(function (t) { t.stop(); });
      scannerStream = null;
    }
    var video = document.getElementById('scannerVideo');
    if (video) video.srcObject = null;
  };

  // Print invoice helper
  window.printInvoice = function () {
    window.print();
  };

  // ───────────────────────────────────────────────
  // INIT: Boot everything on DOM ready
  // ───────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    restoreTheme();
    initSidebar();
    initClock();
    initChatEnter();
    initDropZone();
    initPaymentSelector();
    autoDismissAlerts();
    enhanceDateInputs();
    initAnimations();
    pollNotifications();

    // jQuery-dependent inits
    if (typeof $ !== 'undefined') {
      $(function () {
        initDataTables();
      });
    }
  });

})();
