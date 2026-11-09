"use strict";
const byId = (id) => document.getElementById(id);
const money = new Intl.NumberFormat("vi-VN", {style: "currency", currency: "VND"});
let refreshSequence = 0;

async function api(path, options) {
  const response = await fetch(path, {...options, cache: "no-store"});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Cơ sở dữ liệu chưa sẵn sàng.");
  return result;
}

function renderOrders(orders) {
  const body = byId("orders");
  body.replaceChildren();
  for (const order of orders) {
    const row = document.createElement("tr");
    const values = [String(order.id).padStart(4, "0"), order.customer_alias, order.product_name, order.quantity, money.format(order.quantity * order.unit_price_vnd), order.created_at_utc.replace("T", " ").replace("Z", "")];
    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    body.append(row);
  }
  if (!orders.length) {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 6;
    cell.textContent = "Chưa có đơn hàng trong database.";
    row.append(cell);
    body.append(row);
  }
}

async function refresh() {
  const sequence = ++refreshSequence;
  byId("refresh").disabled = true;
  byId("load-error").hidden = true;
  try {
    const [health, data] = await Promise.all([api("/health"), api("/api/orders")]);
    if (sequence !== refreshSequence) return;
    byId("total").textContent = data.total;
    byId("health").textContent = health.status === "ok" ? "Đang kết nối" : "Chưa sẵn sàng";
    byId("updated").textContent = "Cập nhật " + new Date().toLocaleTimeString("vi-VN");
    renderOrders(data.orders);
  } catch (error) {
    if (sequence !== refreshSequence) return;
    byId("health").textContent = "Mất kết nối";
    byId("total").textContent = "—";
    byId("updated").textContent = "Chưa lấy được dữ liệu mới";
    byId("load-error").textContent = "Không thể tải đơn hàng. Kiểm tra dịch vụ lab và bấm Làm mới.";
    byId("load-error").hidden = false;
    byId("orders").replaceChildren();
  } finally {
    if (sequence === refreshSequence) byId("refresh").disabled = false;
  }
}

byId("refresh").addEventListener("click", refresh);
byId("order-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = byId("submit");
  const message = byId("form-message");
  button.disabled = true;
  message.hidden = true;
  try {
    const result = await api("/api/orders", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({customer_alias: byId("alias").value, product_name: byId("product").value, quantity: Number(byId("quantity").value), unit_price_vnd: Number(byId("price").value)})
    });
    message.className = "message";
    message.textContent = "Đã lưu đơn hàng #" + result.order.id + ".";
    await refresh();
  } catch (error) {
    message.className = "message error";
    message.textContent = error.message || "Chưa thể thêm đơn hàng. Hãy làm mới để kiểm tra trước khi thử lại.";
  } finally {
    message.hidden = false;
    button.disabled = false;
  }
});
refresh();
