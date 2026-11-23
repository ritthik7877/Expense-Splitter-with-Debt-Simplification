(() => {
  const tokenKey = "splitsmart.access";
  const refreshKey = "splitsmart.refresh";
  const accessToken = () => localStorage.getItem(tokenKey);

  function showMessage(message, isError = false) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = `alert position-fixed bottom-0 end-0 m-3 shadow ${isError ? "alert-danger" : "alert-success"}`;
    window.setTimeout(() => toast.classList.add("d-none"), 4000);
  }

  async function api(url, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (accessToken()) headers.Authorization = `Bearer ${accessToken()}`;
    const response = await fetch(url, { ...options, headers });
    const body = response.status === 204 ? null : await response.json();
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem(tokenKey);
        localStorage.removeItem(refreshKey);
        if (!["/login/", "/register/"].includes(location.pathname)) location.href = "/login/";
      }
      const detail = body && (body.detail || JSON.stringify(body));
      throw new Error(detail || `Request failed (${response.status})`);
    }
    return body;
  }

  function requireLogin() {
    if (!accessToken()) location.href = "/login/";
  }

  const authForm = document.getElementById("auth-form");
  if (authForm) {
    authForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(authForm));
      try {
        if (authForm.dataset.mode === "register") {
          await api("/api/auth/register/", { method: "POST", body: JSON.stringify(values) });
          showMessage("Account created. Sign in to continue.");
          window.setTimeout(() => { location.href = "/login/"; }, 800);
          return;
        }
        const tokens = await api("/api/auth/login/", { method: "POST", body: JSON.stringify(values) });
        localStorage.setItem(tokenKey, tokens.access);
        localStorage.setItem(refreshKey, tokens.refresh);
        location.href = "/dashboard/";
      } catch (error) {
        showMessage(error.message, true);
      }
    });
  }

  const groupsList = document.getElementById("groups-list");
  if (groupsList) {
    requireLogin();
    document.getElementById("logout-button").addEventListener("click", () => {
      localStorage.removeItem(tokenKey);
      localStorage.removeItem(refreshKey);
      location.href = "/login/";
    });
    const form = document.getElementById("group-form");
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        const group = await api("/api/groups/", {
          method: "POST",
          body: JSON.stringify({ name: new FormData(form).get("name") }),
        });
        location.href = `/groups/${group.id}/`;
      } catch (error) {
        showMessage(error.message, true);
      }
    });
    api("/api/groups/").then((groups) => {
      groupsList.replaceChildren();
      if (!groups.length) groupsList.innerHTML = '<p class="text-muted">No groups yet. Create one above to get started.</p>';
      groups.forEach((group) => {
        const column = document.createElement("div");
        column.className = "col-md-6 col-lg-4";
        const card = document.createElement("a");
        card.className = "card card-body shadow-sm h-100 text-decoration-none";
        card.href = `/groups/${group.id}/`;
        const title = document.createElement("strong");
        title.textContent = group.name;
        const count = document.createElement("span");
        count.className = "text-muted small mt-1";
        count.textContent = `${group.members.length} members`;
        card.append(title, count);
        column.append(card);
        groupsList.append(column);
      });
    }).catch((error) => showMessage(error.message, true));
  }

  const groupRoot = document.getElementById("group-root");
  if (groupRoot) {
    requireLogin();
    const groupId = groupRoot.dataset.groupId;
    const apiBase = `/api/groups/${groupId}/`;
    let members = [];
    const amountField = (member, type) => {
      const wrapper = document.createElement("label");
      wrapper.className = "row align-items-center g-2 mb-2";
      const name = document.createElement("span");
      name.className = "col-5";
      name.textContent = member.username;
      const input = document.createElement("input");
      input.className = "form-control col";
      input.type = "number";
      input.min = "0";
      input.step = "0.01";
      input.name = `split-${member.id}`;
      input.dataset.userId = member.id;
      input.placeholder = type === "EXACT" ? "Amount" : "%";
      input.required = true;
      wrapper.append(name, input);
      return wrapper;
    };
    const updateSplitFields = () => {
      const type = document.getElementById("split-type").value;
      const container = document.getElementById("split-fields");
      container.replaceChildren();
      if (type !== "EQUAL") members.forEach((member) => container.append(amountField(member, type)));
    };
    const renderExpense = (expense) => {
      const item = document.createElement("div");
      item.className = "list-group-item px-0";
      const heading = document.createElement("div");
      heading.className = "d-flex justify-content-between";
      const description = document.createElement("strong");
      description.textContent = expense.description;
      const total = document.createElement("span");
      total.textContent = `$${expense.amount}`;
      heading.append(description, total);
      const detail = document.createElement("small");
      detail.className = "text-muted";
      const payer = members.find((member) => member.id === expense.paid_by);
      detail.textContent = `Paid by ${payer ? payer.username : "member"} · ${expense.split_type}`;
      item.append(heading, detail);
      return item;
    };
    const loadExpenses = async () => {
      const list = document.getElementById("expenses-list");
      const expenses = await api(`${apiBase}expenses/`);
      list.replaceChildren();
      if (!expenses.length) list.textContent = "No expenses yet.";
      expenses.forEach((expense) => list.append(renderExpense(expense)));
    };
    const loadBalances = async () => {
      const balances = await api(`${apiBase}balances/`);
      const list = document.getElementById("balances-list");
      list.replaceChildren();
      balances.forEach((balance) => {
        const row = document.createElement("div");
        row.className = "d-flex justify-content-between py-1";
        const user = document.createElement("span");
        user.textContent = balance.username;
        const amount = document.createElement("strong");
        const value = Number(balance.balance);
        amount.textContent = `${value < 0 ? "-" : "+"}$${Math.abs(value).toFixed(2)}`;
        amount.className = value < 0 ? "balance-negative" : "balance-positive";
        row.append(user, amount);
        list.append(row);
      });
    };
    const fillMembers = (group) => {
      members = group.members;
      document.getElementById("group-name").textContent = group.name;
      const list = document.getElementById("members-list");
      const selects = [document.getElementById("paid-by"), ...document.querySelectorAll("#settle-form select")];
      list.replaceChildren();
      members.forEach((member) => {
        const badge = document.createElement("span");
        badge.className = "badge text-bg-light border me-1 mb-1";
        badge.textContent = `${member.username} (#${member.id})`;
        list.append(badge);
      });
      selects.forEach((select) => {
        select.replaceChildren();
        members.forEach((member) => {
          const option = document.createElement("option");
          option.value = member.id;
          option.textContent = member.username;
          select.append(option);
        });
      });
      updateSplitFields();
    };
    api(apiBase).then(fillMembers)
      .then(() => Promise.all([loadExpenses(), loadBalances()]))
      .catch((error) => showMessage(error.message, true));
    document.getElementById("split-type").addEventListener("change", updateSplitFields);
    document.getElementById("expense-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const values = Object.fromEntries(new FormData(form));
      const splits = members.map((member) => {
        const value = values[`split-${member.id}`];
        if (value === undefined) return null;
        return document.getElementById("split-type").value === "EXACT"
          ? { user_id: member.id, amount: value }
          : { user_id: member.id, percentage: value };
      }).filter(Boolean);
      const payload = {
        description: values.description,
        amount: values.amount,
        paid_by_id: Number(values.paid_by_id),
        split_type: values.split_type,
      };
      if (splits.length) payload.splits = splits;
      try {
        await api(`${apiBase}expenses/`, { method: "POST", body: JSON.stringify(payload) });
        form.reset();
        updateSplitFields();
        await Promise.all([loadExpenses(), loadBalances()]);
        showMessage("Expense added.");
      } catch (error) {
        showMessage(error.message, true);
      }
    });
    document.getElementById("simplify-button").addEventListener("click", async () => {
      try {
        const plan = await api(`${apiBase}simplify/`);
        const list = document.getElementById("plan-list");
        list.replaceChildren();
        if (!plan.length) {
          list.textContent = "Everyone is settled up.";
          return;
        }
        plan.forEach((transfer) => {
          const item = document.createElement("p");
          item.className = "mb-2";
          item.textContent = `${transfer.from_username} pays ${transfer.to_username} $${transfer.amount}`;
          list.append(item);
        });
      } catch (error) {
        showMessage(error.message, true);
      }
    });
    document.getElementById("member-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      try {
        await api(`${apiBase}add-member/`, {
          method: "POST",
          body: JSON.stringify({ user_id: Number(new FormData(form).get("user_id")) }),
        });
        location.reload();
      } catch (error) {
        showMessage(error.message, true);
      }
    });
    document.getElementById("settle-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      try {
        await api(`${apiBase}settle/`, {
          method: "POST",
          body: JSON.stringify({
            from_user_id: Number(values.from_user_id),
            to_user_id: Number(values.to_user_id),
            amount: values.amount,
          }),
        });
        event.currentTarget.reset();
        await loadBalances();
        showMessage("Payment recorded.");
      } catch (error) {
        showMessage(error.message, true);
      }
    });
  }
})();
