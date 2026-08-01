const form = document.querySelector("#analysis-form");
const requirementInput = document.querySelector("#requirement");
const projectNameInput = document.querySelector("#project-name");
const analyzeButton = document.querySelector("#analyze-button");
const characterCount = document.querySelector("#character-count");
const requirementError = document.querySelector("#requirement-error");
const idleState = document.querySelector("#idle-state");
const analysisState = document.querySelector("#analysis-state");
const statusCard = document.querySelector("#status-card");
const statusTitle = document.querySelector("#status-title");
const statusSummary = document.querySelector("#status-summary");
const scoreValue = document.querySelector("#score-value");
const metadata = document.querySelector("#metadata");
const missingSection = document.querySelector("#missing-section");
const missingList = document.querySelector("#missing-list");
const questionsSection = document.querySelector("#questions-section");
const questionsList = document.querySelector("#questions-list");
const checklist = document.querySelector("#checklist");
const errorState = document.querySelector("#error-state");
const generationReason = document.querySelector("#generation-reason");
const generateButton = document.querySelector("#generate-button");
const casesPanel = document.querySelector("#cases-panel");
const casesHeading = document.querySelector("#cases-heading");
const caseVersion = document.querySelector("#case-version");
const casesList = document.querySelector("#cases-list");
const offlineBanner = document.querySelector("#offline-banner");
const fileModeBanner = document.querySelector("#file-mode-banner");
const fileMode = window.location.protocol === "file:";

const REQUIREMENT_TEMPLATE = `功能目標：[要解決什麼問題、完成什麼任務]
使用者角色：[誰會使用，是否有不同角色]
前置條件：[開始操作前必須成立的條件]
正常流程：[依序描述主要操作與系統回應]
錯誤處理：[失敗、例外或無效輸入時如何處理]
輸入限制：[必填、格式、長度或數量限制]
邊界條件：[最小值、最大值、逾時或特殊情境]
權限規則：[誰可以或不可以執行]
預期結果：[成功後畫面、資料或狀態的變化]`;

const COMPLETE_EXAMPLE = `功能目標：讓會員能以電子郵件與密碼登入並進入個人首頁。
使用者角色：已註冊且啟用的會員；管理員遵循相同登入流程。
前置條件：帳號已完成電子郵件驗證，使用者目前未登入。
正常流程：使用者輸入電子郵件與密碼，點擊登入，系統驗證成功後建立 Session。
錯誤處理：帳密無效時顯示「帳號或密碼錯誤」，不指出哪一欄錯誤；連續失敗五次鎖定十五分鐘。
輸入限制：電子郵件必填且符合格式；密碼必填，長度 8 到 64 字元。
邊界條件：密碼最少 8、最多 64 字元；Session 最多 30 分鐘未操作即失效。
權限規則：只有啟用會員可登入；停權、未驗證或已刪除帳號不可登入。
預期結果：登入成功應導向 /dashboard、更新最後登入時間並設定 HttpOnly Session cookie。`;

const workspaceId = localStorage.getItem("ai-qa-workspace-id") || crypto.randomUUID();
localStorage.setItem("ai-qa-workspace-id", workspaceId);

let currentProjectId = null;
let currentAnalysis = null;

function updateCount() {
  characterCount.textContent = `${requirementInput.value.length.toLocaleString()} / 30,000`;
  localStorage.setItem("ai-qa-draft", requirementInput.value);
}

function setLoading(isLoading, label = "分析中…") {
  analyzeButton.disabled = isLoading || !navigator.onLine;
  analyzeButton.classList.toggle("is-loading", isLoading);
  analyzeButton.querySelector(".button-label").textContent = isLoading ? label : "檢查需求完整性";
}

function syncConnectionState() {
  fileModeBanner.hidden = !fileMode;
  if (fileMode) {
    offlineBanner.hidden = true;
    analyzeButton.disabled = false;
    generateButton.disabled = true;
    generationReason.textContent = "請使用 start_ai_qa_assistant.cmd 啟動服務後再檢查需求。";
    return;
  }

  const offline = !navigator.onLine;
  offlineBanner.hidden = !offline;
  analyzeButton.disabled = offline;
  if (offline) {
    generateButton.disabled = true;
    generationReason.textContent = "目前離線；草稿已保留，恢復連線後再繼續。";
  } else if (currentAnalysis) {
    const canGenerate = currentAnalysis.readiness_state === "ready"
      && currentAnalysis.persisted
      && Boolean(currentProjectId);
    generateButton.disabled = !canGenerate;
    generationReason.textContent = canGenerate
      ? `需求 v${currentAnalysis.requirement_version} 已通過九項檢核；生成案例會綁定此版本。`
      : currentAnalysis.readiness_state === "ready"
        ? "需求已就緒，但必須先設定 Supabase DATABASE_URL 才能保存與生成。"
        : "請依澄清問題補充原需求，再重新檢查。後端也會拒絕直接生成。";
  }
}

function clearList(element) {
  element.replaceChildren();
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function definition(label, content) {
  const wrapper = document.createElement("div");
  wrapper.append(element("dt", "", label));
  const value = document.createElement("dd");
  if (Array.isArray(content)) {
    const list = document.createElement("ol");
    content.forEach((item) => list.append(element("li", "", item)));
    value.append(list);
  } else {
    value.textContent = content;
  }
  wrapper.append(value);
  return wrapper;
}

function renderCase(testCase) {
  const article = element("article", "case-card");
  const title = element("div", "case-title");
  title.append(element("span", "", testCase.case_id));
  title.append(element("span", "priority", testCase.priority));
  article.append(title, element("h3", "", testCase.scenario));

  const details = document.createElement("dl");
  details.append(
    definition("前置條件", testCase.preconditions),
    definition("步驟", testCase.steps),
    definition("測試資料", testCase.test_data),
    definition("預期結果", testCase.expected_result),
  );
  article.append(details);
  return article;
}

function showError(message, requestId) {
  errorState.hidden = false;
  errorState.textContent = requestId ? `${message}（Request ID: ${requestId}）` : message;
}

function renderAnalysis(data) {
  currentAnalysis = data;
  currentProjectId = data.project_id || currentProjectId;
  idleState.hidden = true;
  analysisState.hidden = false;
  errorState.hidden = true;

  const isReady = data.readiness_state === "ready";
  statusCard.dataset.state = data.readiness_state;
  statusTitle.textContent = isReady ? "需求已就緒" : `尚缺 ${data.missing_items.length} 項，暫不能生成`;
  statusSummary.textContent = data.summary;
  scoreValue.textContent = data.requirement_score;
  metadata.textContent = data.persisted
    ? `需求版本 v${data.requirement_version} · ${data.provider} · 已保存至 Supabase`
    : `${data.provider} · 尚未設定 Supabase，這次分析未保存`;

  clearList(missingList);
  data.missing_items.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    missingList.append(li);
  });
  missingSection.hidden = data.missing_items.length === 0;

  clearList(questionsList);
  data.clarification_questions.forEach((question) => {
    const li = document.createElement("li");
    li.textContent = question;
    questionsList.append(li);
  });
  questionsSection.hidden = data.clarification_questions.length === 0;

  clearList(checklist);
  data.checklist.forEach((item) => {
    const li = document.createElement("li");
    li.className = item.present ? "is-present" : "is-missing";
    li.textContent = `${item.present ? "已確認" : "待補充"}：${item.label}`;
    checklist.append(li);
  });

  const canGenerate = isReady && data.persisted && Boolean(data.project_id);
  generateButton.disabled = !canGenerate;
  generateButton.textContent = canGenerate ? "生成測試案例" : "尚未開放生成";
  generationReason.textContent = canGenerate
    ? `需求 v${data.requirement_version} 已通過九項檢核；生成案例會綁定此版本。`
    : isReady
      ? "需求已就緒，但必須先設定 Supabase DATABASE_URL 才能保存與生成。"
      : "請依澄清問題補充原需求，再重新檢查。後端也會拒絕直接生成。";
  statusTitle.focus();
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = data.error || {};
    throw Object.assign(new Error(error.message || "請求失敗，請稍後重試。"), {
      requestId: error.request_id || response.headers.get("X-Request-ID"),
      code: error.code,
    });
  }
  return data;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  requirementError.textContent = "";
  casesPanel.hidden = true;
  const requirement = requirementInput.value.trim();
  if (requirement.length < 5) {
    requirementError.textContent = "請至少輸入 5 個字元，讓系統有足夠內容分析。";
    requirementInput.focus();
    return;
  }

  if (fileMode) {
    idleState.hidden = true;
    analysisState.hidden = false;
    showError("目前是直接開啟 HTML，無法呼叫分析服務。請雙擊專案根目錄的 start_ai_qa_assistant.cmd 後再試一次。");
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Workspace-ID": workspaceId,
      },
      body: JSON.stringify({
        project_id: currentProjectId,
        name: projectNameInput.value.trim() || "未命名專案",
        requirement,
      }),
    });
    renderAnalysis(await parseResponse(response));
  } catch (error) {
    idleState.hidden = true;
    analysisState.hidden = false;
    showError(error.message, error.requestId);
  } finally {
    setLoading(false);
  }
});

generateButton.addEventListener("click", async () => {
  if (!currentProjectId || currentAnalysis?.readiness_state !== "ready") return;
  generateButton.disabled = true;
  generateButton.textContent = "生成中…";
  try {
    const response = await fetch(`/api/projects/${currentProjectId}/generate`, {
      method: "POST",
      headers: { "X-Workspace-ID": workspaceId },
    });
    const data = await parseResponse(response);
    clearList(casesList);
    data.test_cases.forEach((testCase) => casesList.append(renderCase(testCase)));
    caseVersion.textContent = `需求 v${data.requirement_version}`;
    casesPanel.hidden = false;
    casesHeading.focus();
  } catch (error) {
    showError(error.message, error.requestId);
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = "重新生成測試案例";
  }
});

document.querySelector("#fill-example").addEventListener("click", () => {
  projectNameInput.value = "會員登入";
  requirementInput.value = COMPLETE_EXAMPLE;
  updateCount();
  requirementInput.focus();
});

document.querySelector("#use-template").addEventListener("click", () => {
  requirementInput.value = REQUIREMENT_TEMPLATE;
  updateCount();
  requirementInput.focus();
});

requirementInput.value = localStorage.getItem("ai-qa-draft") || "";
requirementInput.addEventListener("input", updateCount);
window.addEventListener("online", syncConnectionState);
window.addEventListener("offline", syncConnectionState);
updateCount();
syncConnectionState();
