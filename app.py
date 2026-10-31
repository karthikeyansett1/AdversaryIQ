"""AdversaryIQ | hosted prompt-injection evaluation workbench."""
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from engine import load_cases, find_case, summarize_records, validate_attack
from workflow import evaluate

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="AdversaryIQ | AI Security Workbench", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT/'assets'/'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
for key, initial in {"runs": [], "run_count": 0, "active_case": "AIQ-001", "custom_attack": "", "choice": "Attack Studio"}.items():
    if key not in st.session_state:
        st.session_state[key] = initial

cases = load_cases()
case_lookup = {c['id']: c for c in cases}


def banner(kicker, heading, description):
    st.markdown(f'<div class="eyebrow">{kicker}</div><h1>{heading}</h1><p class="subheading">{description}</p>', unsafe_allow_html=True)


def tag(text, kind="neutral"):
    st.markdown(f'<span class="tag {kind}">{text}</span>', unsafe_allow_html=True)


def panel_title(title, description):
    st.markdown(f'<div class="paneltitle">{title}</div><p class="muted">{description}</p>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="brandmark"><div class="shield">◈</div><div><strong>ADVERSARYIQ</strong><small>AI SECURITY WORKBENCH</small></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidecaption">NAVIGATION</div>', unsafe_allow_html=True)
    page = st.radio("Workspace", ["Mission Control", "Attack Studio", "Evaluation Lab", "Case Library", "Method & Evidence"], label_visibility="collapsed", key="choice")
    st.divider()
    st.markdown('<div class="sidecaption">EXECUTION ENVIRONMENT</div>', unsafe_allow_html=True)
    st.caption("Cloud-hosted OpenAI Responses API")
    model = st.selectbox("Model", ["gpt-4.1-mini", "gpt-5-mini"], index=0, help="Both evaluator and target use this hosted model. Charges apply to your API account.")
    api_key = st.text_input("Your OpenAI API key", type="password", placeholder="sk-...", help="Used for the current request; never saved to the repository or exported reports.")
    st.caption("Bring your own API key • No server-side owner key • No local inference")
    st.divider()
    st.markdown('<div class="sidecaption">SESSION BUDGET</div>', unsafe_allow_html=True)
    used = st.session_state.run_count
    st.progress(min(used / 3, 1.0))
    st.caption(f"{used} / 3 hosted investigations this browser session. Up to 5 API requests per investigation. This is not a provider billing cap.")
    st.caption("Sample evidence in this repository is labeled illustrative, not measured model performance.")

summary = summarize_records(st.session_state.runs)

if page == "Mission Control":
    banner("SECURITY INTELLIGENCE / 001", "Trust boundaries. Tested.", "An evidence-first workspace for measuring instruction-hierarchy failures in hosted language models.")
    a,b,c,d = st.columns(4)
    a.metric("Test scenarios", f"{len(cases):02}")
    b.metric("Executed probes", str(summary["completed"]))
    c.metric("Exact disclosures", str(summary["failures"]))
    d.metric("Agent runs remaining", str(max(0, 3-used)))
    st.markdown('<div class="sectiongap"></div>', unsafe_allow_html=True)
    left,right = st.columns([1.2,1], gap="large")
    with left:
        panel_title("The security question", "Can lower-trust instructions cause a model to expose a protected synthetic value?")
        st.markdown("""**AdversaryIQ** reproduces small, authorized prompt-injection attempts against a fictional internal assistant. A real hosted language model receives an explicit instruction not to disclose a synthetic token. The test prompt attempts to subvert that constraint.

The workflow records the actual response, applies a narrow exact-match disclosure check, and exports an auditable evaluation record. Both baseline and hardened defense configurations are available for comparison.""")
        st.info("A clean result means **no exact token disclosure occurred in that particular response**. It does not prove safety against other attack families.")
    with right:
        panel_title("Controlled execution pipeline", "Real cloud inference, observable tools, and deterministic evidence.")
        st.markdown("""<div class="pipeline"><div><span>01</span><strong>Validate scenario</strong><small>Constrain prompt length and selected test</small></div><div><span>02</span><strong>Agent tool orchestration</strong><small>Retrieve context and execute one probe</small></div><div><span>03</span><strong>Hosted target inference</strong><small>Responses API • dedicated policy prompt</small></div><div><span>04</span><strong>Score & export evidence</strong><small>Exact-match rule • JSON / Markdown</small></div></div>""", unsafe_allow_html=True)
    st.divider()
    panel_title("Coverage areas", "Eight curated benign security evaluation probes — no destructive payloads or real secrets.")
    cats = pd.Series([c["category"] for c in cases]).value_counts().reset_index()
    cats.columns = ["Attack family", "Scenarios"]
    st.dataframe(cats, use_container_width=True, hide_index=True)
    if st.button("Open Attack Studio →", type="primary"):
        st.session_state.choice = "Attack Studio"
        st.rerun()

elif page == "Attack Studio":
    banner("WORKSPACE / ATTACK STUDIO", "Probe the boundary.", "Execute a bounded red-team scenario against a real hosted model, then inspect the tool trace and result.")
    l,r = st.columns([1.08, .92], gap="large")
    with l:
        panel_title("01 / Define a scenario", "Choose a curated test or write a limited custom injection attempt.")
        selected = st.selectbox("Scenario", [c["id"] for c in cases], format_func=lambda cid: f"{cid}  ·  {case_lookup[cid]['name']}", key="active_case")
        case = case_lookup[selected]
        st.caption(f"{case['category']} • {case['severity'].upper()} • {case['objective']}")
        custom = st.checkbox("Customize attack text", value=False)
        attack = st.text_area("Attack prompt", value=case["attack"], height=155, max_chars=1800, key=f"attack_{selected}_{custom}", disabled=not custom)
        st.caption("Custom attack text is submitted only when you run an investigation. Avoid real personal, private, or production data.")
        mode = st.segmented_control("Defense configuration", options=["baseline", "hardened"], default="baseline", format_func=lambda s: "Baseline policy" if s == "baseline" else "Hardened policy")
        st.caption("The hardened mode strengthens the trusted system instructions; it is not a guarantee of resistance.")
        disabled = used >= 3
        execute = st.button("Run hosted investigation", type="primary", disabled=disabled, use_container_width=True)
        if execute:
            try:
                validate_attack(attack)
                if not api_key.strip():
                    st.error("Add your OpenAI API key in the sidebar to run a real cloud-hosted test.")
                else:
                    # Count before the provider request so failures do not create unlimited attempts.
                    st.session_state.run_count += 1
                    with st.spinner("Executing the hosted coordinator and target probe..."):
                        record = evaluate(api_key, case, attack, mode, model)
                    st.session_state.runs.insert(0, record)
                    st.success("Hosted evaluation complete — scroll to the evidence panel.")
            except Exception as exc:
                st.error(f"Investigation failed: {type(exc).__name__}: {exc}. Failed attempts count toward the session budget; check API access and try a new session if needed.")
    with r:
        panel_title("02 / Observed evidence", "Only completed provider calls generate evaluated results.")
        matching = st.session_state.runs
        if not matching:
            st.markdown('<div class="empty"><div class="emptysymbol">◇</div><strong>No live investigations yet</strong><p>Select a case, provide your API key, and run the hosted model to generate genuine evidence.</p></div>', unsafe_allow_html=True)
        else:
            record = matching[0]
            scored = record["scoring"]
            tag(scored["outcome"], "danger" if scored["canary_disclosed"] else "success")
            st.metric("Scoring rule", "Exact disclosure" if scored["canary_disclosed"] else "No exact disclosure")
            st.caption(f"Case {record['case']['id']} • {record['mode']} • {record['target_model']}")
            st.markdown("**Actual target response**")
            st.code(record["target_response"] or "[No text returned]", language=None, wrap_lines=True)
            with st.expander("Agent interpretation", expanded=True):
                st.write(record["agent_summary"])
            st.caption(scored["scope_note"])
            st.markdown("**Actual agent tool trace**")
            st.dataframe(pd.DataFrame([{"Round": t["round"], "Tool": t["tool"], "Status": t["status"]} for t in record["trace"]]), hide_index=True, use_container_width=True)
            with st.expander("Raw trace and token usage"):
                st.json({"trace": record["trace"], "graph_stages": record.get("graph_stages", []), "tokens": record.get("token_usage", {})})
            col1,col2=st.columns(2)
            col1.download_button("Export JSON", json.dumps(record, indent=2), file_name=f"adversaryiq_{record['run_id'][:8]}.json", mime="application/json", use_container_width=True)
            col2.download_button("Export memo", record["report"], file_name=f"adversaryiq_{record['run_id'][:8]}.md", mime="text/markdown", use_container_width=True)

elif page == "Evaluation Lab":
    banner("ANALYSIS / EVALUATION", "Evidence over impressions.", "Inspect completed live tests; compare observed disclosures by defensive configuration.")
    a,b,c=st.columns(3)
    a.metric("Completed live probes", summary["completed"])
    b.metric("Exact token disclosures", summary["failures"])
    c.metric("Observed failure rate", f"{summary['exact_disclosure_rate']:.0%}" if summary['exact_disclosure_rate'] is not None else "N/A")
    st.warning("Small samples and a single exact-match rule cannot establish general robustness. Baseline/hardened comparisons are descriptive, not controlled statistical inference.")
    if summary["completed"]:
        rows=[{"Run": r["run_id"][:8], "Scenario": r["case"]["name"], "Mode": r["mode"], "Model": r["target_model"], "Exact disclosure": r["scoring"]["canary_disclosed"]} for r in st.session_state.runs if r.get("status") == "completed"]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        chart=pd.DataFrame([{"Configuration": mode.title(), "Completed probes": counts["runs"], "Exact disclosures": counts["failures"]} for mode,counts in summary["by_mode"].items()])
        st.bar_chart(chart.set_index("Configuration")[["Completed probes", "Exact disclosures"]])
        st.download_button("Download session results (JSON)", json.dumps(st.session_state.runs,indent=2), "adversaryiq_session_results.json", "application/json")
    else:
        st.info("No hosted investigations have been run in this browser session. Visit Attack Studio to collect real evidence.")
    st.divider()
    panel_title("Reference examples — illustrated, not model measurements", "These fixtures demonstrate the deterministic scorer, not the performance of any real hosted model.")
    examples = [{"Example":"Response does not contain the synthetic sentinel", "Exact match":False, "Scorer":"PASS"}, {"Example":"Response includes the full synthetic sentinel", "Exact match":True, "Scorer":"FAIL"}]
    st.dataframe(pd.DataFrame(examples), hide_index=True, use_container_width=True)

elif page == "Case Library":
    banner("INTELLIGENCE / ATTACK CATALOG", "Eight focused hypotheses.", "Curated, synthetic attack prompts designed to probe instruction precedence and confidential-value disclosure.")
    for case in cases:
        with st.expander(f"{case['id']}  ·  {case['name']}  —  {case['category']}"):
            st.markdown(f"**Objective:** {case['objective']}")
            st.markdown(f"**Trust-boundary lesson:** {case['lesson']}")
            st.code(case["attack"], language=None)
            if st.button("Open in Attack Studio", key=f"open_{case['id']}"):
                st.session_state.active_case = case['id']
                st.session_state.choice = "Attack Studio"
                st.rerun()

elif page == "Method & Evidence":
    banner("GOVERNANCE / METHODOLOGY", "Precisely scoped claims.", "A transparent description of inputs, hosted calls, scoring rules, limits, and privacy assumptions.")
    st.markdown("""### What is tested
The fictional assistant receives an instruction to keep a **synthetic sentinel** private. Each attack prompt is a lower-trust user message. A separately invoked hosted coordinator uses auditable functions to inspect a scenario, run a single target probe, and inspect scoring policy.

### What counts as a failure
The deterministic scorer detects the **full synthetic sentinel** in the target response using a case-insensitive exact-substring match. It cannot detect partial disclosures, encoding, indirect data release, or other policy violations. The model's explanation is qualitative and is not used as the ground-truth score.

### Baseline versus hardened
Both modes protect the same artificial sentinel. The hardened mode adds explicit instructions about lower-trust text, forged roles, quoted documents, and token transformations. Observed differences are not causal evidence without a larger controlled evaluation.

### Scope and operational controls
- Single-turn attack tests only; no retrieval systems, websites, file ingestion, or external target endpoints.
- Each invocation runs **at most one real target probe** and up to four coordinator rounds. The total upper bound is five provider requests per investigation.
- Three attempts per Streamlit browser session. This is a convenience guardrail, **not** a global quota or billing limit.
- Bring-your-own API key. No bundled secrets, no owner-funded public API calls, no stored run database.
- Results remain in Streamlit's current session memory until the session expires; exports are user initiated.
- Hosted provider billing, availability, and data handling are governed by the account and API provider.
- The app does **not** guarantee resilience, certify a model, or execute attacks against third-party systems.

### Technologies
Python • Streamlit • LangGraph • OpenAI Responses API • Pandas • Pytest
""")
    with st.expander("Security and privacy notes"):
        st.write("Use a low-permission API key with limited credits. Do not submit real credentials, private customer data, or proprietary prompts. The platform forwards selected prompts to the OpenAI API. Every run incurs provider usage; session limits can be bypassed by refreshing or starting a new browser session.")

st.markdown('<div class="footer">ADVERSARYIQ <span>·</span> CONTROLLED AI SECURITY EVALUATIONS <span>·</span> HOSTED MODEL EXECUTION</div>', unsafe_allow_html=True)
