const state = {
  currentView: "overview",
  orderFilter: "confirmed",
  orders: [],
  menu: null,
  stats: null,
};

const viewMeta = {
  overview: {
    title: "Overview",
    subtitle: "Kitchen & order management at a glance",
  },
  orders: {
    title: "Orders",
    subtitle: "Track and update incoming customer orders",
  },
  menu: {
    title: "Menu",
    subtitle: "Add items and manage availability",
  },
};

const statusActions = {
  confirmed: [{ label: "Start Preparing", status: "preparing", type: "primary" }],
  preparing: [{ label: "Mark Ready", status: "ready", type: "primary" }],
  ready: [{ label: "Complete Order", status: "completed", type: "primary" }],
};

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

function formatMoney(amount) {
  return `$${Number(amount).toFixed(2)}`;
}

function formatTime(isoString) {
  if (!isoString) return "—";
  const date = new Date(isoString);
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function setView(view) {
  state.currentView = view;

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === view);
  });

  document.querySelectorAll(".view").forEach((section) => {
    section.classList.toggle("active", section.id === `view-${view}`);
  });

  const meta = viewMeta[view];
  document.getElementById("page-title").textContent = meta.title;
  document.getElementById("page-subtitle").textContent = meta.subtitle;
}

function renderStats() {
  const stats = state.stats;
  if (!stats) return;

  document.getElementById("restaurant-name").textContent = stats.restaurant_name;
  document.getElementById("stat-active").textContent = stats.active_orders;
  document.getElementById("stat-today").textContent = stats.today_order_count;
  document.getElementById("stat-revenue").textContent = formatMoney(stats.today_revenue);
  document.getElementById("stat-unavailable").textContent = stats.unavailable_items;
}

function renderAttention() {
  const container = document.getElementById("attention-list");
  const urgent = state.orders.filter((order) =>
    ["confirmed", "preparing", "ready"].includes(order.status)
  );

  document.getElementById("attention-count").textContent = urgent.length;

  if (!urgent.length) {
    container.innerHTML = '<div class="empty-state">No active orders right now. You\'re all caught up.</div>';
    return;
  }

  container.innerHTML = urgent
    .slice(0, 6)
    .map(
      (order) => `
        <div class="attention-item">
          <div>
            <strong>Order #${order.id}</strong>
            <p class="order-meta">${order.customer_name || "Guest"} · ${order.item_count} items · ${formatMoney(order.total_price)}</p>
          </div>
          <span class="status-pill status-${order.status}">${order.status_label}</span>
        </div>
      `
    )
    .join("");
}

function renderOrders() {
  const container = document.getElementById("orders-grid");
  const filtered = state.orderFilter
    ? state.orders.filter((order) => order.status === state.orderFilter)
    : state.orders;

  if (!filtered.length) {
    container.innerHTML = '<div class="empty-state">No orders match this filter.</div>';
    return;
  }

  container.innerHTML = filtered
    .map((order) => {
      const actions = (statusActions[order.status] || [])
        .map(
          (action) => `
            <button
              class="action-btn ${action.type}"
              data-order-id="${order.id}"
              data-status="${action.status}"
            >${action.label}</button>
          `
        )
        .join("");

      const items = order.items
        .map(
          (item) => `
            <li>
              <span>${item.quantity}x ${item.item_name}</span>
              <span>${formatMoney(item.line_total)}</span>
            </li>
          `
        )
        .join("");

      return `
        <article class="order-card">
          <div class="order-header">
            <div>
              <div class="order-id">Order #${order.id}</div>
              <p class="order-meta">${order.customer_name || "Guest"} · ${order.customer_phone || "—"}</p>
              <p class="order-meta">Placed ${formatTime(order.confirmed_at || order.created_at)}</p>
            </div>
            <span class="status-pill status-${order.status}">${order.status_label}</span>
          </div>
          <ul class="order-items">${items || "<li>No items</li>"}</ul>
          <div class="order-total">Total: ${formatMoney(order.total_price)}</div>
          <div class="order-actions">${actions}</div>
        </article>
      `;
    })
    .join("");
}

function renderCategoryOptions() {
  const select = document.getElementById("category-select");
  const categories = state.menu?.categories || [];

  select.innerHTML = categories
    .map((category) => `<option value="${category}">${category.charAt(0).toUpperCase() + category.slice(1)}</option>`)
    .join("");
}

function renderMenu() {
  const container = document.getElementById("menu-sections");
  const menu = state.menu;

  renderCategoryOptions();

  if (!menu || !menu.items.length) {
    container.innerHTML = '<div class="empty-state">No menu items found.</div>';
    return;
  }

  const grouped = {};
  menu.items.forEach((item) => {
    const category = item.category || "other";
    if (!grouped[category]) grouped[category] = [];
    grouped[category].push(item);
  });

  container.innerHTML = menu.categories
    .filter((category) => grouped[category])
    .map((category) => {
      const items = grouped[category]
        .map(
          (item) => `
            <div class="menu-item ${item.available ? "" : "unavailable"}">
              <div class="menu-item-info">
                <h5>${item.name}</h5>
                <p>${formatMoney(item.price)} · ${item.available ? "Available" : "Unavailable"}</p>
                <div class="menu-tags">
                  ${item.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
                </div>
              </div>
              <label class="toggle" title="Toggle availability">
                <input
                  type="checkbox"
                  data-item-name="${item.name}"
                  ${item.available ? "checked" : ""}
                />
                <span class="toggle-slider"></span>
              </label>
            </div>
          `
        )
        .join("");

      return `
        <section class="menu-category">
          <h4>${category.charAt(0).toUpperCase() + category.slice(1)}</h4>
          ${items}
        </section>
      `;
    })
    .join("");
}

async function loadDashboard() {
  const [stats, orders, menu] = await Promise.all([
    api("/api/dashboard/stats"),
    api("/api/dashboard/orders"),
    api("/api/dashboard/menu"),
  ]);

  state.stats = stats;
  state.orders = orders;
  state.menu = menu;

  renderStats();
  renderAttention();
  renderOrders();
  renderMenu();

  document.getElementById("last-updated").textContent =
    `Updated ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}`;
}

async function updateOrderStatus(orderId, status) {
  await api(`/api/dashboard/orders/${orderId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
  await loadDashboard();
}

async function toggleMenuItem(itemName, available) {
  await api(`/api/dashboard/menu/${encodeURIComponent(itemName)}`, {
    method: "PATCH",
    body: JSON.stringify({ available }),
  });
  await loadDashboard();
}

async function createMenuItem(formData) {
  const tags = formData
    .get("tags")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);

  await api("/api/dashboard/menu", {
    method: "POST",
    body: JSON.stringify({
      name: formData.get("name").trim(),
      price: parseFloat(formData.get("price")),
      category: formData.get("category"),
      tags,
      available: true,
    }),
  });

  await loadDashboard();
}

function bindEvents() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => setView(btn.dataset.view));
  });

  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", (event) => {
      document.querySelectorAll(".filter-btn").forEach((el) => el.classList.remove("active"));
      event.currentTarget.classList.add("active");
      state.orderFilter = event.currentTarget.dataset.status;
      renderOrders();
    });
  });

  document.getElementById("refresh-btn").addEventListener("click", loadDashboard);

  document.getElementById("orders-grid").addEventListener("click", async (event) => {
    const button = event.target.closest("[data-order-id]");
    if (!button) return;

    button.disabled = true;
    try {
      await updateOrderStatus(button.dataset.orderId, button.dataset.status);
    } catch (error) {
      alert(error.message);
      button.disabled = false;
    }
  });

  document.getElementById("menu-sections").addEventListener("change", async (event) => {
    const input = event.target.closest('input[type="checkbox"][data-item-name]');
    if (!input) return;

    try {
      await toggleMenuItem(input.dataset.itemName, input.checked);
    } catch (error) {
      alert(error.message);
      input.checked = !input.checked;
    }
  });

  document.getElementById("add-item-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const form = event.currentTarget;
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;

    try {
      await createMenuItem(new FormData(form));
      form.reset();
      renderCategoryOptions();
    } catch (error) {
      alert(error.message);
    } finally {
      submitBtn.disabled = false;
    }
  });
}

bindEvents();
loadDashboard().catch((error) => {
  document.body.innerHTML = `<div class="empty-state" style="margin:40px;">Failed to load dashboard: ${error.message}</div>`;
});

setInterval(() => {
  loadDashboard().catch(() => {});
}, 15000);
