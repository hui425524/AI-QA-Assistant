from __future__ import annotations

from dataclasses import dataclass

from .schemas import AnalysisResult, RubricCheck, TestCaseResult


@dataclass(frozen=True)
class RubricItem:
    key: str
    label: str
    keywords: tuple[str, ...]
    question: str


RUBRIC: tuple[RubricItem, ...] = (
    RubricItem(
        "goal",
        "功能目標",
        ("功能目標", "目的", "目標", "goal", "讓使用者", "允許使用者"),
        "這個功能要解決什麼問題，成功的結果是什麼？",
    ),
    RubricItem(
        "role",
        "使用者角色",
        ("使用者角色", "角色", "管理員", "會員", "訪客", "user role", "admin"),
        "哪些使用者角色可以操作這個功能？",
    ),
    RubricItem(
        "preconditions",
        "前置條件",
        ("前置條件", "已登入", "必須先", "given", "precondition"),
        "執行功能前必須滿足哪些狀態或資料條件？",
    ),
    RubricItem(
        "happy_path",
        "正常流程",
        ("正常流程", "步驟", "點擊", "輸入後", "依序", "when", "flow"),
        "請列出使用者完成操作的正常步驟。",
    ),
    RubricItem(
        "error_handling",
        "錯誤處理",
        ("錯誤處理", "失敗時", "錯誤訊息", "無效", "invalid", "error"),
        "輸入無效或操作失敗時，系統應如何處理？",
    ),
    RubricItem(
        "input_constraints",
        "輸入限制",
        ("輸入限制", "格式", "長度", "必填", "字元", "format", "length"),
        "輸入有哪些格式、長度、必填或字元限制？",
    ),
    RubricItem(
        "boundaries",
        "邊界條件",
        ("邊界條件", "上限", "下限", "至少", "最多", "boundary", "maximum"),
        "有哪些上限、下限或臨界值需要定義？若無，請明確寫無。",
    ),
    RubricItem(
        "permissions",
        "權限規則",
        ("權限規則", "權限", "只有", "不可存取", "permission", "authorized"),
        "不同角色有哪些允許或禁止的操作？若無差異，請明確說明。",
    ),
    RubricItem(
        "expected_result",
        "預期結果",
        ("預期結果", "應顯示", "應導向", "應回傳", "expected", "result"),
        "操作成功後，畫面、資料與系統狀態應如何改變？",
    ),
)


class MockQaProvider:
    name = "mock-v1"

    def analyze(self, requirement: str) -> AnalysisResult:
        normalized = " ".join(requirement.lower().split())
        checks = [
            RubricCheck(
                key=item.key,
                label=item.label,
                present=any(keyword.lower() in normalized for keyword in item.keywords),
            )
            for item in RUBRIC
        ]
        missing_items = [check.label for check in checks if not check.present]
        questions = [
            item.question
            for item, check in zip(RUBRIC, checks, strict=True)
            if not check.present
        ][:5]
        score = round(sum(check.present for check in checks) / len(checks) * 100)
        is_complete = not missing_items
        state = "ready" if is_complete else "blocked"
        summary = (
            "九項需求資訊皆已明確，可進入測試案例生成。"
            if is_complete
            else f"尚缺 {len(missing_items)} 項資訊；系統不會猜測，請補充後重新分析。"
        )
        return AnalysisResult(
            requirement_score=score,
            readiness_state=state,
            is_complete=is_complete,
            missing_items=missing_items,
            clarification_questions=questions,
            checklist=checks,
            summary=summary,
            provider=self.name,
        )

    def generate(self, requirement: str) -> list[TestCaseResult]:
        del requirement
        return [
            TestCaseResult(
                case_id="TC001",
                scenario="使用者依正常流程完成主要操作",
                preconditions="符合需求中定義的前置條件與權限。",
                steps=["準備有效測試資料", "依需求中的正常流程操作", "觀察畫面與資料狀態"],
                test_data="一組符合格式與邊界限制的有效資料",
                expected_result="系統顯示需求中定義的成功結果，資料狀態正確。",
                priority="High",
                test_type="正常流程",
            ),
            TestCaseResult(
                case_id="TC002",
                scenario="使用者送出無效輸入",
                preconditions="使用者可進入功能，但輸入不符合需求限制。",
                steps=["輸入一組無效資料", "送出操作", "檢查錯誤訊息與資料狀態"],
                test_data="違反格式或必填規則的資料",
                expected_result="系統依需求顯示錯誤，不寫入不合法資料。",
                priority="High",
                test_type="異常流程",
            ),
            TestCaseResult(
                case_id="TC003",
                scenario="驗證邊界值與未授權操作",
                preconditions="準備需求中定義的邊界值與受限角色。",
                steps=["使用邊界資料操作", "改以無權限角色重試", "確認兩次結果"],
                test_data="上限、下限及一個無權限角色",
                expected_result="邊界行為與權限拒絕皆符合需求，且不洩漏敏感資訊。",
                priority="Medium",
                test_type="邊界值／權限",
            ),
        ]


def get_provider(mode: str) -> MockQaProvider:
    if mode != "mock":
        raise RuntimeError("Live AI provider is not implemented in Phase 1.")
    return MockQaProvider()
