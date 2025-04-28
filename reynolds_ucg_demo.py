import streamlit as st
import pandas as pd
import numpy as np
from faker import Faker
from pyvis.network import Network
import tempfile, os

faker = Faker()
st.set_page_config(page_title="Reynolds Universal Customer Graph", layout="wide")

# ------------------------------ helper to build fake table ------------------
def build_partner_table(base_name: str, n=12):
    industries = ['Retail', 'Distributor', 'E-commerce', 'Wholesale']
    systems = ['SalesCRM', 'SupplyChainEDI', 'Billing', 'RetailCompliance']
    rows=[]
    for i in range(n):
        ent = f"{base_name} {faker.company_suffix()}" if i else base_name
        row = dict(
            UniversalCustomerID="UCID-"+faker.bothify(text='??##??##'),
            ParentCompany=base_name,
            LegalEntity=ent,
            HQ_Country='US',
            AnnualRevenue=np.round(np.random.uniform(200, 100000),2),   # $M
            Industry=np.random.choice(industries),
            EmployeeCount=np.random.randint(500, 30000),
        )
        for sys in systems:
            row[sys] = np.random.choice([1,0], p=[0.7,0.3])
        rows.append(row)
    df = pd.DataFrame(rows)
    return df

# ------------------------------ sidebar ------------------
st.sidebar.header("Universal Customer Demo for Reynolds Consumer Products")
partner = st.sidebar.text_input("Enter channel-partner name:",
                                value="Costco Wholesale Corporation")
n_entities = st.sidebar.slider("How many legal entities to generate:",
                               5, 20, 12)

df = build_partner_table(partner, n_entities)

# ------------------------------ tabbed UI ------------------
tab1, tab2 = st.tabs(["📊 Table View", "🌐 Network View"])

with tab1:
    st.subheader(f"Unified view for **{partner}**")
    st.caption("Bold **1** indicates that legal entity exists in that system.")
    st.dataframe(df.style
                   .format({'AnnualRevenue':'${:,.1f} M',
                            'EmployeeCount':'{:,}'})
                   .apply(lambda x: ['font-weight:bold' if v==1 else '' for v in x],
                          subset=['SalesCRM','SupplyChainEDI','Billing','RetailCompliance'])
                 , height=450)
with tab2:
    st.subheader("Interactive Universal Customer Graph")
    G = Network(height='600px', width='100%', bgcolor='#ffffff')

    uid = df['UniversalCustomerID'].iloc[0]
    G.add_node(uid, label=partner, color='#ff7f0e', size=40)

    # Define node color by Industry
    color_map = {
        'Retail': '#1f77b4',         # Blue
        'Distributor': '#2ca02c',    # Green
        'E-commerce': '#ff7f0e',     # Orange
        'Wholesale': '#9467bd',      # Purple
    }

    for _, r in df.iterrows():
        node_id = r['LegalEntity']
        label = f"{r['LegalEntity']}\\n${r['AnnualRevenue']:.0f}M"
        node_color = color_map.get(r['Industry'], '#7f7f7f')  # Default gray if unknown
        G.add_node(node_id, label=label, color=node_color, size=20)

        # Add edges with relationship label
        relationship = ""
        if r['Industry'] == 'Retail':
            relationship = "Retail Customer"
        elif r['Industry'] == 'Distributor':
            relationship = "Distributor Partner"
        elif r['Industry'] == 'E-commerce':
            relationship = "E-commerce Retailer"
        elif r['Industry'] == 'Wholesale':
            relationship = "Wholesale Supply Chain"

        G.add_edge(uid, node_id, title=relationship)

    # Write HTML manually
    with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
        G.write_html(tmpfile.name)
        tmpfile.flush()
        with open(tmpfile.name, 'r', encoding='utf-8') as f:
            html_data = f.read()
        st.components.v1.html(html_data, height=650, scrolling=True)
