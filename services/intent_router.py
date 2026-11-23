"""Demo-mode planner: picks tools WITHOUT calling any paid API.

It is deliberately simple and explainable (great for interviews):

1. It receives the list of *discovered* tools (name, description, keywords, schema).
2. It scores every tool by how well its keywords match the user's question.
3. It extracts values from the question (period, top-N, product, email ...).
4. It fills each tool's arguments using that tool's own JSON schema.

With a Claude API key the model does all of this reasoning itself.
"""
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
          "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10}
CUSTOMER_STOPWORDS = {"search", "find", "show", "list", "me", "customer", "customers", "client", "clients",
                      "named", "called", "from", "in", "with", "the", "a", "an", "for", "details", "of", "about",
                      "all", "who", "are", "is", "lookup", "look", "up", "information", "info", "profile",
                      "by", "name", "located", "based", "get", "give", "my", "to", "retrieve"}

HELP_TEXT = """I can analyse the sales data using my tools. Try one of these:

- Analyze last month's sales
- Which product generated the highest revenue?
- Show monthly revenue
- Find the top 5 selling products
- Compare this month and last month
- Generate a PDF sales report
- Give me business growth suggestions
- Who are my top customers? / Search customers in London
- Send a summary to Slack (mock unless you configured a webhook)

Add a period such as *last month*, *this month*, *last 30 days* or *October* to any question."""


@dataclass
class PlannedStep:
    tool: str
    arguments: dict
    reason: str


@dataclass
class _Context:
    period: Optional[str] = None
    top_n: Optional[int] = None
    metric: Optional[str] = None
    product: Optional[str] = None
    email: Optional[str] = None
    customer_id: Optional[int] = None
    customer_query: Optional[str] = None
    report_format: Optional[str] = None
    dates: List[str] = field(default_factory=list)


class DemoPlanner:
    def __init__(self, product_names: Optional[List[str]] = None, reference: Optional[date] = None) -> None:
        self.product_names = product_names or []
        self.reference = reference or date.today()

    # ------------------------------------------------------------ extraction
    def extract_period(self, q: str) -> Optional[str]:
        match = re.search(r"\b(\d{4})-(\d{2})\b(?!-\d)", q)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        rules = [
            (r"last month|previous month|past month", "last_month"),
            (r"this month|current month|month to date|so far this month", "this_month"),
            (r"last 7 days|past 7 days|last week|past week|this week", "last_7_days"),
            (r"last 30 days|past 30 days|last thirty days", "last_30_days"),
            (r"last 90 days|past 90 days|last quarter|last 3 months|past 3 months|last three months", "last_90_days"),
            (r"this year|year to date|ytd", "this_year"),
            (r"last year|previous year", "last_year"),
            (r"all time|overall|since the beginning|ever\b", "all"),
        ]
        for pattern, value in rules:
            if re.search(pattern, q):
                return value
        for name, number in MONTHS.items():
            hit = re.search(rf"\b{name}\b(?:\s+(\d{{4}}))?", q)
            if hit:
                if hit.group(1):
                    year = int(hit.group(1))
                else:
                    year = self.reference.year if number <= self.reference.month else self.reference.year - 1
                return f"{year}-{number:02d}"
        return None

    @staticmethod
    def extract_top_n(q: str) -> Optional[int]:
        match = re.search(r"\b(?:top|best|worst|bottom|lowest|highest)\s+(\d+)\b", q) or re.search(r"\b(\d+)\s+(?:best|top|worst)\b", q)
        if match:
            return max(1, min(int(match.group(1)), 50))
        word = re.search(r"\b(?:top|best|worst|bottom)\s+(" + "|".join(NUMBER_WORDS) + r")\b", q)
        return NUMBER_WORDS[word.group(1)] if word else None

    def match_product(self, q: str) -> Optional[str]:
        best, best_score = None, 0
        tokens = set(re.findall(r"\w+", q))
        for name in self.product_names:
            lowered = name.lower()
            if lowered in q:
                score = 100 + len(lowered)
            else:
                words = re.findall(r"\w+", lowered)
                if len(words) >= 2 and all(w in tokens for w in words[:2]):
                    score = 10 + len(words)
                else:
                    continue
            if score > best_score:
                best, best_score = name, score
        return best

    def build_context(self, q: str) -> _Context:
        ctx = _Context(period=self.extract_period(q), top_n=self.extract_top_n(q), product=self.match_product(q))
        email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", q)
        ctx.email = email.group(0) if email else None
        cid = re.search(r"\bcustomer\s*(?:id\s*)?#?(\d+)\b", q)
        ctx.customer_id = int(cid.group(1)) if cid else None
        if re.search(r"\b(units|quantity|sold|selling)\b", q) and "revenue" not in q:
            ctx.metric = "units"
        elif "profit" in q:
            ctx.metric = "profit"
        else:
            ctx.metric = "revenue"
        if re.search(r"\bcsv\b|\bexcel\b", q):
            ctx.report_format = "csv"
        elif re.search(r"\bpdf\b", q):
            ctx.report_format = "pdf"
        ctx.dates = re.findall(r"\d{4}-\d{2}-\d{2}", q)
        words = [w for w in re.findall(r"[\w'.@-]+", q) if w not in CUSTOMER_STOPWORDS]
        ctx.customer_query = " ".join(words).strip() or None
        return ctx

    # --------------------------------------------------------------- scoring
    @staticmethod
    def score_tools(q: str, tools: List[dict]) -> List[tuple]:
        padded = f" {q} "
        scored = []
        for tool in tools:
            hits = [kw for kw in tool.get("keywords", []) if kw in padded]
            score = sum(len(kw.split()) * 2 for kw in hits)
            if score:  # small tie-breaker from the description words
                desc_words = {w for w in re.findall(r"[a-z]{5,}", tool["description"].lower())}
                score += 0.1 * len(desc_words & set(re.findall(r"[a-z]{5,}", q)))
            scored.append((score, tool, hits))
        scored.sort(key=lambda item: -item[0])
        return scored

    # ------------------------------------------------------------- arguments
    @staticmethod
    def fill_arguments(tool: dict, ctx: _Context, q: str, period_default: Optional[str] = None) -> Optional[dict]:
        """Build arguments from the tool's JSON schema. Returns None if a required value is missing."""
        props = tool["input_schema"].get("properties", {})
        required = tool["input_schema"].get("required", [])
        args: Dict[str, object] = {}
        period = ctx.period or period_default
        if "period" in props and period:
            args["period"] = period
        if "top_n" in props and ctx.top_n:
            args["top_n"] = ctx.top_n
        if "metric" in props and ctx.metric:
            args["metric"] = ctx.metric
        if "report_format" in props and ctx.report_format:
            args["report_format"] = ctx.report_format
        if "product_name" in props and ctx.product:
            args["product_name"] = ctx.product
        if "email" in props and ctx.email:
            args["email"] = ctx.email
        if "customer_id" in props and ctx.customer_id:
            args["customer_id"] = ctx.customer_id
        if "query" in props and ctx.customer_query:
            args["query"] = ctx.customer_query
        if "start_date" in props and "end_date" in props and len(ctx.dates) >= 2:
            args["start_date"], args["end_date"] = ctx.dates[0], ctx.dates[1]
            args.pop("period", None)
        if "limit" in props and tool["name"] == "get_all_sales":
            args["limit"] = ctx.top_n or 10
        if any(r not in args for r in required):
            return None
        return args

    # ----------------------------------------------------------------- plan
    def plan(self, question: str, tools: List[dict]) -> List[PlannedStep]:
        q = " ".join(question.lower().split())
        by_name = {t["name"]: t for t in tools}
        ctx = self.build_context(q)
        steps: List[PlannedStep] = []

        def add(name: str, reason: str, period_default: Optional[str] = None, extra: Optional[dict] = None) -> bool:
            tool = by_name.get(name)
            if tool is None:
                return False
            args = self.fill_arguments(tool, ctx, q, period_default)
            if args is None:
                return False
            args.update(extra or {})
            if all(s.tool != name for s in steps):
                steps.append(PlannedStep(name, args, reason))
            return True

        if re.fullmatch(r"(hi|hello|hey|help|thanks|thank you)[!. ]*", q) or "what can you do" in q:
            return []

        wants_report = bool(re.search(r"\b(pdf|report|csv)\b", q))
        wants_analysis = bool(re.search(r"\b(analy[sz]e|analysis|overview|summary|summari[sz]e|how did we do|how are we doing)\b", q))

        if "slack" in q:
            add("send_report_to_slack", "you mentioned Slack", "last_month")
        elif re.search(r"google sheet|spreadsheet|\bsheets\b", q):
            add("sync_sales_to_google_sheets", "you mentioned Google Sheets", "last_month")
        elif ctx.email and re.search(r"\bcrm\b|lead", q):
            add("get_crm_contact", "email + CRM keyword")
        elif ctx.email:
            add("get_customer_details", "an email address was given")
        elif ctx.customer_id:
            add("get_customer_details", "a customer ID was given")
        elif len(ctx.dates) >= 2 and "get_sales_by_date_range" in by_name and not wants_report:
            add("get_sales_by_date_range", "two dates were given")
        elif re.search(r"\b(compare|versus|vs)\b|difference between", q) and re.search(r"month|year|period|week", q):
            extra = {}
            if "this year" in q and "last year" in q:
                extra = {"period_a": "this_year", "period_b": "last_year"}
            add("compare_periods", "comparison keywords", extra=extra)
        elif ctx.product and not re.search(r"\b(top|best|worst)\b", q):
            add("analyze_product_performance", f"product name recognised: {ctx.product}")
        elif wants_analysis and not ctx.top_n:
            period = ctx.period or "last_month"
            add("generate_sales_summary", "analysis requested", period)
            add("find_best_selling_products", "context for the analysis", period, {"top_n": 5})
            add("create_business_insights", "insights for the analysis", period)
            if wants_report:
                add("generate_report", "report requested", period, {"report_format": ctx.report_format or "pdf"})
        elif wants_report and "export" not in q:
            add("generate_report", "report/PDF keywords", "last_month")
        elif "export" in q:
            add("export_sales_report", "export keyword", "last_month")
        elif re.search(r"suggest|recommend|growth|improve|advice|ideas|opportunit|strateg|insight", q):
            add("create_business_insights", "growth / insight keywords", ctx.period or "last_90_days")
        else:
            scored = self.score_tools(q, tools)
            if scored and scored[0][0] > 0:
                best = scored[0][0]
                for score, tool, hits in scored[:2]:
                    if score >= max(2, 0.9 * best):
                        extra = {"top_n": 3} if (tool["name"] == "find_best_selling_products" and not ctx.top_n
                                                 and re.search(r"\bwhich product|\bwhat product|\bbest product", q)) else None
                        add(tool["name"], "matched keywords: " + ", ".join(h.strip() for h in hits), extra=extra)
        for step in steps:
            if step.tool == "find_best_selling_products" and "top_n" not in step.arguments and re.search(r"\bwhich product|\bwhat product", q):
                step.arguments["top_n"] = 3
        return steps
