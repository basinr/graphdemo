import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
from pyvis.network import Network
import tempfile, os
import random

"""Streamlit app — demo of Reynolds Universal Customer Graph
• Upstream systems limited to: SalesCRM, PartnerCRM, Contracts, Billing, Support
"""
ƒ
faker = Faker()
st.set_page_config(page_title="Reynolds Universal Customer Graph", layout="wide")

# ------------------------------------------------------------------
# 0️⃣  Demo company metadata (static)
# ------------------------------------------------------------------
company_info = {
    "Company Name": "GlobalTech Solutions",
    "Description": (
        "GlobalTech Solutions is a multinational corporation specializing "
        "in consumer products and advanced materials innovation."
    ),
    "Annual Revenue": "$25B",
    "Industry": "Consumer Goods",
    "Employee Count": "60,000",
    "Headquarters": "Chicago, Illinois, USA",
    "Total Spend with Reynolds": "$125M",
}

# ------------------------------------------------------------------
# 1️⃣  Helper – build mock legal‑entity table limited to 5 sources
# ------------------------------------------------------------------

def build_partner_table(base_name: str, n: int = 12) -> pd.DataFrame:
    """Generate fake partner hierarchy restricted to the five allowed systems."""

    industries = ["Retail", "Distributor", "E-commerce", "Wholesale"]
    systems = ["SalesCRM", "PartnerCRM", "Contracts", "Billing", "Support"]

    rows = []
    for i in range(n):
        ent = f"{base_name} {faker.company_suffix()}" if i else base_name
        row = dict(
            UniversalCustomerID="UCID-" + faker.bothify(text="??##??##"),
            ParentCompany=base_name,
            LegalEntity=ent,
            HQ_Country="US",
            AnnualRevenue=np.round(np.random.uniform(200, 100_000), 2),  # $M
            Industry=np.random.choice(industries),
            EmployeeCount=np.random.randint(500, 30_000),
        )
        # Flag presence of this legal entity in each source system
        for sys in systems:
            row[sys] = np.random.choice([1, 0], p=[0.7, 0.3])
        rows.append(row)
    return pd.DataFrame(rows)

# ------------------------------------------------------------------
# 2️⃣  Sidebar controls
# ------------------------------------------------------------------

st.sidebar.header("Universal Customer Demo for Reynolds Consumer Products")
partner = st.sidebar.text_input(
    "Enter channel-partner name:", value="Costco Wholesale Corporation"
)
n_entities = st.sidebar.slider("How many legal entities to generate:", 5, 20, 12)

# ------------------------------------------------------------------
# 3️⃣  Generate mock data
# ------------------------------------------------------------------

df = build_partner_table(partner, n_entities)

# ------------------------------------------------------------------
# 4️⃣  Executive overview card (top section)
# ------------------------------------------------------------------

with st.container():
    st.markdown(
        f"""
        <div style="
            background-color: #f9f9f9;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
        ">
            <h2 style="color: #333333; margin-bottom: 0.5rem;">{company_info['Company Name']} Overview</h2>
            <p style="color: #666666; font-size: 1.1rem; margin-top: 0px;">{company_info['Description']}</p>
            <div style="display: flex; flex-wrap: wrap; margin-top: 1.5rem;">
                <div style="flex: 1; min-width: 200px; margin-bottom: 1rem;">
                    <strong>Annual Revenue:</strong><br>{company_info['Annual Revenue']}
                </div>
                <div style="flex: 1; min-width: 200px; margin-bottom: 1rem;">
                    <strong>Employee Count:</strong><br>{company_info['Employee Count']}
                </div>
                <div style="flex: 1; min-width: 200px; margin-bottom: 1rem;">
                    <strong>Industry:</strong><br>{company_info['Industry']}
                </div>
                <div style="flex: 1; min-width: 200px; margin-bottom: 1rem;">
                    <strong>Headquarters:</strong><br>{company_info['Headquarters']}
                </div>
            </div>
            <div style="margin-top: 1.5rem; padding: 1rem; background-color: #e0f7fa; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0; color: #007c91;">Total Spend with Reynolds: {company_info['Total Spend with Reynolds']}</h3>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ------------------------------------------------------------------
# 5️⃣  Tabbed UI – Table & Network views
# ------------------------------------------------------------------

tab1, tab2 = st.tabs(["📊 Table View", "🌐 Network View"])

with tab1:
    st.subheader(f"Unified view for **{partner}**")
    st.caption(
        "Bold **1** below indicates that the legal entity exists in that upstream system."
    )

    source_cols = ["SalesCRM", "PartnerCRM", "Contracts", "Billing", "Support"]

    st.dataframe(
        df.style
        .format({"AnnualRevenue": "${:,.1f} M", "EmployeeCount": "{:,}"})
        .apply(
            lambda x: ["font-weight:bold" if v == 1 else "" for v in x],
            subset=source_cols,
        ),
        height=450,
    )

with tab2:
    st.subheader("Interactive Universal Customer Graph")

    G = Network(
        height="900px", width="100%", bgcolor="#ffffff", notebook=False, directed=False
    )
    G.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=250)

    uid = df["UniversalCustomerID"].iloc[0]
    G.add_node(uid, label=partner, color="#ff7f0e", size=60, shape="ellipse", font={"size": 20})

    # Node color by Industry
    color_map = {
        "Retail": "#1f77b4",
        "Distributor": "#2ca02c",
        "E-commerce": "#ff7f0e",
        "Wholesale": "#9467bd",
    }

    for _, r in df.iterrows():
        node_id = r["LegalEntity"]
        label = f"{r['LegalEntity']}\\n${r['AnnualRevenue']:.0f}M"
        node_color = color_map.get(r["Industry"], "#7f7f7f")
        G.add_node(
            node_id,
            label=label,
            color=node_color,
            size=30,
            group=r["Industry"],
            font={"size": 16},
        )

        relationship = {
            "Retail": "Retail",
            "Distributor": "Distributor",
            "E-commerce": "E-Comm",
            "Wholesale": "Wholesale",
        }.get(r["Industry"], "Partner")

        G.add_edge(uid, node_id, label=relationship, font={"size": 10})

        # Child entities
        for _ in range(random.randint(1, 2)):
            child_name = f"{r['LegalEntity']} - {faker.company_suffix()}"
            G.add_node(child_name, label=child_name, color=node_color, size=18, font={"size": 12})
            G.add_edge(node_id, child_name, label="Division", font={"size": 8})

    # Tiny floating legend
    legend_html = """
    <div style="position: fixed; top: 100px; right: 50px; width: 180px; background-color: white; border: solid 1px #ccc; padding: 10px; z-index:9999; font-size:14px;">
      <b>Legend</b><br>
      <span style="color:#1f77b4;">⬤</span> Retail<br>
      <span style="color:#2ca02c;">⬤</span> Distributor<br>
      <span style="color:#ff7f0e;">⬤</span> E-commerce<br>
      <span style="color:#9467bd;">⬤</span> Wholesale<br>
    </div>
    """

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        G.write_html(tmpfile.name)
        tmpfile.flush()
        with open(tmpfile.name, "r", encoding="utf-8") as f:
            html_data = f.read()

    html_with_legend = html_data.replace("<body>", f"<body>{legend_html}")
    st.components.v1.html(html_with_legend, height=900, scrolling=True)
