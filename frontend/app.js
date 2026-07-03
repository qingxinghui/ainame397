const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { category: "宝宝起名", token: localStorage.getItem("ainame_token") || "", user: JSON.parse(localStorage.getItem("ainame_user") || "null"), threadId: "", lastNames: [] };

function list(value) { return value ? value.split(/[、,，]/).map(v => v.trim()).filter(Boolean) : []; }
function escapeHtml(value = "") { const div = document.createElement("div"); div.textContent = String(value); return div.innerHTML; }
function toast(message) { const el = $("#toast"); el.textContent = message; el.classList.add("show"); setTimeout(() => el.classList.remove("show"), 2800); }
function setLoading(loading, button = $("#namingForm .submit-button")) { button.disabled = loading; button.querySelector?.(".button-text")?.classList.toggle("hidden", loading); button.querySelector?.(".loader")?.classList.toggle("hidden", !loading); }

async function api(path, options = {}) {
  const headers = { ...(options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {}), ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}), ...options.headers };
  const response = await fetch(path, { ...options, headers });
  let data = {}; try { data = await response.json(); } catch (_) {}
  if (!response.ok) throw new Error(data.detail || data.message || `请求失败 (${response.status})`);
  return data;
}

function updateAuthUI() {
  const button = $("#authButton");
  button.textContent = state.user ? `${state.user.username} · 退出` : "登录 / 注册";
  $("#loginHint").textContent = state.user ? `已登录：${state.user.username}` : "登录后可生成并保存多轮记录";
}

$$('.category-card').forEach(button => button.addEventListener('click', () => {
  $$('.category-card').forEach(item => item.classList.remove('active'));
  button.classList.add('active'); state.category = button.dataset.category;
  $$('.category-fields').forEach(group => group.classList.add('hidden'));
  const target = state.category.includes('宝宝') || state.category === '人名' ? '#personalFields' : state.category.startsWith('商业') || state.category === '企业名' ? '#brandFields' : state.category.includes('虚拟IP') ? '#ipFields' : '#petFields';
  $(target).classList.remove('hidden');
}));

$("#useBazi").addEventListener("change", event => $("#birthFields").classList.toggle("hidden", !event.target.checked));
$("[name=industry]").addEventListener("change", event => $("#customIndustryField").classList.toggle("hidden", event.target.value !== "其他"));
$("[name=pet_type]").addEventListener("change", event => $("#customPetField").classList.toggle("hidden", event.target.value !== "其他"));
$("[name=virtual_ip_type]").addEventListener("change", event => $("#customIpField").classList.toggle("hidden", event.target.value !== "其他"));
$("#authButton").addEventListener("click", () => { if (state.user) { localStorage.removeItem("ainame_token"); localStorage.removeItem("ainame_user"); state.token = ""; state.user = null; updateAuthUI(); toast("已退出登录"); } else $("#authDialog").showModal(); });
$(".dialog-close").addEventListener("click", () => $("#authDialog").close());

$$('.auth-tabs button').forEach(button => button.addEventListener('click', () => {
  $$('.auth-tabs button').forEach(item => item.classList.remove('active')); button.classList.add('active');
  $("#loginForm").classList.toggle("hidden", button.dataset.tab !== "login");
  $("#registerForm").classList.toggle("hidden", button.dataset.tab !== "register");
  $("#authMessage").textContent = "";
}));

$("#sendCode").addEventListener("click", async () => {
  const email = $("#registerForm [name=email]").value;
  if (!email) return toast("请先填写邮箱");
  try { await api(`/auth/code?email=${encodeURIComponent(email)}`); toast("验证码已发送，请检查邮箱"); } catch (error) { $("#authMessage").textContent = error.message; }
});

$("#registerForm").addEventListener("submit", async event => {
  event.preventDefault(); const form = Object.fromEntries(new FormData(event.target));
  try { await api("/auth/register", { method: "POST", body: JSON.stringify(form) }); $("#authMessage").textContent = "注册成功，请切换到登录"; } catch (error) { $("#authMessage").textContent = error.message; }
});

$("#loginForm").addEventListener("submit", async event => {
  event.preventDefault(); const form = Object.fromEntries(new FormData(event.target));
  try {
    const data = await api("/auth/login", { method: "POST", body: JSON.stringify(form) });
    state.token = data.token; state.user = data.user; localStorage.setItem("ainame_token", data.token); localStorage.setItem("ainame_user", JSON.stringify(data.user));
    updateAuthUI(); $("#authDialog").close(); toast("登录成功，欢迎回来");
  } catch (error) { $("#authMessage").textContent = error.message; }
});

function buildPayload(form) {
  const values = Object.fromEntries(new FormData(form));
  const payload = { category: state.category, length: values.length, other: values.other, exclude: list(values.exclude) };
  if (state.category.includes("宝宝") || state.category === "人名") Object.assign(payload, { surname: values.surname, person_type: values.person_type, gender: values.person_type === "男孩" ? "男" : "女", preferred_classics: list(values.preferred_classics), use_bazi: values.use_bazi === "on", birth_info: values.use_bazi === "on" ? { birth_date: values.birth_date, birth_time: values.birth_time || null, calendar_type: "公历" } : null, other: [values.name_style, values.other].filter(Boolean).join("；") });
  if (state.category.startsWith("商业")) Object.assign(payload, { industry: values.industry === "其他" ? values.industry_custom : values.industry, competitors: list(values.competitors), brand_tone: list(values.brand_tone) });
  if (state.category.startsWith("宠物")) Object.assign(payload, { ip_type: values.pet_type === "其他" ? values.ip_type_custom : values.pet_type, personality: list(values.personality) });
  if (state.category.includes("虚拟IP")) Object.assign(payload, { ip_type: values.virtual_ip_type === "其他" ? values.virtual_ip_custom : values.virtual_ip_type, personality: list(values.ip_personality) });
  return payload;
}

$("#namingForm").addEventListener("submit", async event => {
  event.preventDefault(); if (!state.token) { $("#authDialog").showModal(); return toast("请先登录再开始推演"); }
  setLoading(true);
  try { const data = await api("/names/generate", { method: "POST", body: JSON.stringify(buildPayload(event.target)) }); state.threadId = data.thread_id; renderResults(data); }
  catch (error) { toast(error.message); } finally { setLoading(false); }
});

function detail(label, value) { return value ? `<dt>${label}</dt><dd>${escapeHtml(value)}</dd>` : ""; }
function renderResults(data) {
  state.lastNames = data.names || [];
  const strategies = (data.naming_strategy || []).map(item => `<span>${escapeHtml(item)}</span>`).join("");
  $("#reportSummary").innerHTML = `<h3>本轮命名策略</h3><p>${escapeHtml(data.report_summary || "已完成五个候选名称的综合推演。")}</p>${strategies ? `<div class="strategy-tags">${strategies}</div>` : ""}${data.disclaimer ? `<small>${escapeHtml(data.disclaimer)}</small>` : ""}`;
  $("#nameResults").innerHTML = (data.names || []).map((item, index) => {
    const citations = (item.citations || []).map(c => `<div class="citation"><b>《${escapeHtml(c.source)}》</b><p>${escapeHtml(c.original_text)}</p><small>${escapeHtml(c.interpretation)}</small></div>`).join("");
    return `<article class="name-card" data-index="${String(index + 1).padStart(2, "0")}"><h3>${escapeHtml(item.name)}</h3><p class="reference">${escapeHtml(item.reference)}</p><dl>${detail("寓意", item.moral)}${detail("音韵", item.pronunciation_analysis)}${detail("文化分析", item.cultural_analysis)}${detail("五行参考", item.five_elements_analysis)}${detail("品牌分析", item.brand_analysis)}${detail("创意亮点", item.creativity_note)}</dl>${citations}${item.domain ? `<span class="domain">${escapeHtml(item.domain)} · ${escapeHtml(item.domain_status)}</span>` : ""}<br><button class="asset-check" data-name="${encodeURIComponent(item.name)}" type="button">校验域名与数字资产</button></article>`;
  }).join("");
  $("#resultsSection").classList.remove("hidden"); $("#resultsSection").scrollIntoView({ behavior: "smooth" });
}

$("#feedbackForm").addEventListener("submit", async event => {
  event.preventDefault(); if (!state.threadId) return toast("请先完成一轮起名");
  const button = event.target.querySelector("button"); button.disabled = true;
  try { const data = await api("/names/feedback", { method: "POST", body: JSON.stringify({ thread_id: state.threadId, category: state.category, feedback: $("#feedbackText").value }) }); renderResults(data); $("#feedbackText").value = ""; toast("已根据你的意见重新推演"); }
  catch (error) { toast(error.message); } finally { button.disabled = false; }
});

updateAuthUI();

$("#assetDialogClose").addEventListener("click", () => $("#assetDialog").close());
$("#nameResults").addEventListener("click", async event => {
  const button = event.target.closest(".asset-check");
  if (!button) return;
  const name = decodeURIComponent(button.dataset.name);
  $("#assetName").textContent = `“${name}”校验报告`;
  $("#assetContent").innerHTML = "";
  $("#assetLoading").classList.remove("hidden");
  $("#assetDialog").showModal();
  try {
    const data = await api("/validation/check", { method: "POST", body: JSON.stringify({ name }) });
    const domains = data.domains.map(item => `<div class="domain-item ${item.status}"><b>${escapeHtml(item.domain)}</b><span>${escapeHtml(item.status_text)}</span></div>`).join("");
    $("#assetContent").innerHTML = `<section class="asset-section"><h3>域名可用性</h3><div class="domain-matrix">${domains || "未生成有效域名前缀"}</div></section><section class="asset-section"><h3>外部数据校验</h3><div class="risk-row"><div class="risk-card"><b>商标风险 · ${escapeHtml(data.trademark.risk_level)}</b><p>${escapeHtml(data.trademark.message)}</p></div><div class="risk-card"><b>社交媒体重名 · ${escapeHtml(data.social_media.risk_level)}</b><p>${escapeHtml(data.social_media.message)}</p></div></div></section><p class="asset-note">${escapeHtml(data.disclaimer)}</p>`;
  } catch (error) {
    $("#assetContent").innerHTML = `<p class="form-message">${escapeHtml(error.message)}</p>`;
  } finally {
    $("#assetLoading").classList.add("hidden");
  }
});

$("#pollDialogClose").addEventListener("click", () => $("#pollDialog").close());
$("#publishPoll").addEventListener("click", () => {
  if (!state.token) { $("#authDialog").showModal(); return toast("登录后才能发布投票"); }
  if (state.lastNames.length < 2) return toast("请先完成一轮起名");
  $("#pollPreview").innerHTML = state.lastNames.map(item => `<span>${escapeHtml(item.name)}</span>`).join("");
  $("#pollCreateForm").classList.remove("hidden");
  $("#pollView").classList.add("hidden");
  $("#pollDialog").showModal();
});

function renderPoll(poll) {
  const shareUrl = `${location.origin}/?poll=${poll.id}`;
  $("#pollDialogTitle").textContent = poll.title;
  $("#pollCreateForm").classList.add("hidden");
  $("#pollView").classList.remove("hidden");
  $("#pollView").innerHTML = `<p>${escapeHtml(poll.description || "选出你最喜欢的候选名字")}</p><form id="pollVoteForm">${poll.options.map(item => `<label class="poll-option"><input type="radio" name="option_id" value="${item.id}" required><span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.moral)}</small></span><span class="poll-count">${item.vote_count} 票</span></label>`).join("")}<div class="poll-share">${escapeHtml(shareUrl)}</div><div class="poll-actions"><span class="poll-total">共 ${poll.total_votes} 票</span><button class="primary-button" type="submit">投出这一票</button></div></form>`;
  $("#pollVoteForm").addEventListener("submit", async event => {
    event.preventDefault();
    if (!state.token) { $("#pollDialog").close(); $("#authDialog").showModal(); return toast("登录后才能投票"); }
    const optionId = Number(new FormData(event.target).get("option_id"));
    try { renderPoll(await api(`/community/polls/${poll.id}/vote`, { method: "POST", body: JSON.stringify({ option_id: optionId }) })); toast("投票成功"); }
    catch (error) { toast(error.message); }
  });
}

$("#pollCreateForm").addEventListener("submit", async event => {
  event.preventDefault();
  const values = Object.fromEntries(new FormData(event.target));
  const payload = { title: values.title, description: values.description, options: state.lastNames.map(item => ({ name: item.name, moral: item.moral || "" })) };
  try { renderPoll(await api("/community/polls", { method: "POST", body: JSON.stringify(payload) })); toast("投票已创建，可以复制链接分享"); }
  catch (error) { toast(error.message); }
});

const sharedPollId = new URLSearchParams(location.search).get("poll");
if (sharedPollId && /^\d+$/.test(sharedPollId)) {
  api(`/community/polls/${sharedPollId}`).then(poll => { renderPoll(poll); $("#pollDialog").showModal(); }).catch(error => toast(error.message));
}
