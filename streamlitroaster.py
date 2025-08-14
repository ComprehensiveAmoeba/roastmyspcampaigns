import streamlit as st
import pandas as pd
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="SP Campaign Roaster 🔥",
    page_icon="🔥",
    layout="wide"
)

# --- Data for Explanations ---
CAMPAIGN_TYPE_DEFINITIONS = {
    'A': {
        "Description": "The Granular Optimizer (SKAG/SPAG)",
        "Conditions": "1 Ad Group, 1 ASIN, 1 Target.",
        "Verdict": "✅ Excellent Practice for maximum control."
    },
    'B': {
        "Description": "The Mixed-Targeting Campaign",
        "Conditions": ">1 Ad Group, 1 ASIN, contains both Keywords and Product Targets.",
        "Verdict": "❌ Bad Practice, as it's hard to control budget between different strategies."
    },
    'C': {
        "Description": "The 'Kitchen Sink'",
        "Conditions": ">1 Ad Group, >1 ASIN.",
        "Verdict": "❌ Worst Practice, nearly impossible to optimize effectively."
    },
    'D': {
        "Description": "The Organized Keyword Campaign",
        "Conditions": ">1 Ad Group, 1 ASIN, Keywords only, 1 Match Type per ad group.",
        "Verdict": "✅ Excellent Practice, great for separating match types."
    },
    'E': {
        "Description": "The Complex Keyword Campaign",
        "Conditions": ">1 Ad Group, 1 ASIN, Keywords only, >1 Match Types within ad groups.",
        "Verdict": "⚠️ Okay, but can be improved by separating match types."
    },
    'F': {
        "Description": "The Product Targeting (PAT) Campaign",
        "Conditions": ">1 Ad Group, 1 ASIN, Product Targets only.",
        "Verdict": "✅ Good Practice for targeting specific products or categories."
    },
    'G': {
        "Description": "The Themed Ad Group (STAG)",
        "Conditions": "1 Ad Group, 1 ASIN, >1 Targets, all with the same match type.",
        "Verdict": "✅ Good Practice for grouping closely related keywords."
    },
    'H': {
        "Description": "The Messy Ad Group",
        "Conditions": "1 Ad Group, 1 ASIN, >1 Targets with different match types.",
        "Verdict": "⚠️ Okay, but should be cleaned up by separating match types."
    },
    'I': {
        "Description": "The Multi-ASIN Ad Group (Single Target)",
        "Conditions": "1 Ad Group, >1 ASIN, 1 Target.",
        "Verdict": "❌ Bad Practice, as keywords can't be relevant to all products."
    },
    'J': {
        "Description": "The Multi-ASIN Ad Group (Multi-Target)",
        "Conditions": "1 Ad Group, >1 ASIN, >1 Target.",
        "Verdict": "❌ Bad Practice, combining multiple issues."
    },
    'Unknown': {
        "Description": "Unknown Structure",
        "Conditions": "The structure does not fit any of the defined types.",
        "Verdict": "⚠️ Needs investigation, likely an unusual or new campaign setup."
    }
}


# --- Analysis Functions ---

def analyze_structure(df):
    """
    Analyzes the campaign structure based on the provided DataFrame.
    This function uses the exact A-J classification logic.
    Returns both the summary stats and a DataFrame with classifications per campaign.
    """
    # Ensure required columns exist, fill with empty strings if not
    required_cols = ['Campaign ID', 'Ad Group ID', 'Ad ID', 'Entity', 'Campaign Name (Informational only)', 'ASIN (Informational only)', 'Keyword Text', 'Match Type', 'Product Targeting Expression']
    for col in required_cols:
        if col not in df.columns:
            df[col] = ''

    campaign_groups = df.groupby('Campaign ID')
    classifications = {}
    structure_data = []
    total_campaigns = len(campaign_groups)

    if total_campaigns == 0:
        return {
            "totalCampaigns": 0,
            "goodStructurePercent": 0,
            "badStructurePercent": 0,
            "typeDistribution": {},
            "structure_df": pd.DataFrame()
        }

    for campaign_id, group in campaign_groups:
        campaign_name = group['Campaign Name (Informational only)'].iloc[0]
        ad_groups = group['Ad Group ID'].dropna().unique()
        ad_ids = group[group['Entity'] == 'Product Ad']['Ad ID'].dropna().unique()
        asins = group[group['Entity'] == 'Product Ad']['ASIN (Informational only)'].dropna().unique()
        
        kws = group[group['Entity'] == 'Keyword']
        kw_texts = kws['Keyword Text'].dropna().unique()
        kw_match_types = kws['Match Type'].dropna().unique()

        pt = group[group['Entity'] == 'Product Targeting']
        pt_texts = pt['Product Targeting Expression'].dropna().unique()

        ad_group_count = len(ad_groups)
        asin_count = len(asins)
        kw_count = len(kw_texts)
        pt_count = len(pt_texts)
        match_type_count = len(kw_match_types)

        type_ = 'Unknown'
        if ad_group_count == 1 and len(ad_ids) == 1:
            if kw_count + pt_count == 1: type_ = 'A'
            elif kw_count + pt_count > 1: type_ = 'G' if match_type_count <= 1 else 'H'
        elif ad_group_count == 1 and len(ad_ids) > 1:
            type_ = 'I' if kw_count + pt_count == 1 else 'J'
        elif ad_group_count > 1:
            if asin_count == 1:
                if kw_count > 0 and pt_count > 0: type_ = 'B'
                elif kw_count > 0: type_ = 'D' if match_type_count <= 1 else 'E'
                elif pt_count > 0: type_ = 'F'
            else:
                type_ = 'C'
        
        classifications[type_] = classifications.get(type_, 0) + 1
        structure_data.append({'Campaign ID': campaign_id, 'Type': type_})

    structure_df = pd.DataFrame(structure_data)
    good_types = ['A', 'D', 'F', 'G']
    good_count = structure_df[structure_df['Type'].isin(good_types)].shape[0]
    
    return {
        "totalCampaigns": total_campaigns,
        "goodStructurePercent": (good_count / total_campaigns) * 100 if total_campaigns > 0 else 0,
        "badStructurePercent": 100 - ((good_count / total_campaigns) * 100 if total_campaigns > 0 else 0),
        "typeDistribution": classifications,
        "structure_df": structure_df
    }

def analyze_automation(df):
    if 'Product Targeting Expression' not in df.columns or 'Spend' not in df.columns or 'Campaign ID' not in df.columns:
        return {"totalSpend": 0, "autoPercent": 0, "manualPercent": 0, "autoSpend": 0, "manualSpend": 0}
    auto_campaign_ids = df[df['Product Targeting Expression'].notna() & (df['Product Targeting Expression'] != '')]['Campaign ID'].unique()
    campaign_level_df = df[df['Entity'] == 'Campaign'].copy()
    campaign_level_df['Spend'] = pd.to_numeric(campaign_level_df['Spend'], errors='coerce').fillna(0)
    auto_spend = campaign_level_df[campaign_level_df['Campaign ID'].isin(auto_campaign_ids)]['Spend'].sum()
    manual_spend = campaign_level_df[~campaign_level_df['Campaign ID'].isin(auto_campaign_ids)]['Spend'].sum()
    total_spend = auto_spend + manual_spend
    return {
        "totalSpend": total_spend,
        "autoPercent": (auto_spend / total_spend) * 100 if total_spend > 0 else 0,
        "manualPercent": (manual_spend / total_spend) * 100 if total_spend > 0 else 0,
        "autoSpend": auto_spend,
        "manualSpend": manual_spend
    }

def analyze_funneling(df):
    if 'Entity' not in df.columns or 'Campaign ID' not in df.columns:
        return {"totalCampaigns": 0, "campaignsWithNegativesPercent": 0, "avgNegativesPerCampaign": 0}
    all_campaigns = df['Campaign ID'].dropna().unique()
    negative_entities = df[df['Entity'].str.contains("negative", case=False, na=False)]
    campaigns_with_negatives = negative_entities['Campaign ID'].dropna().unique()
    total_negatives = len(negative_entities)
    total_campaigns = len(all_campaigns)
    return {
        "totalCampaigns": total_campaigns,
        "campaignsWithNegativesPercent": (len(campaigns_with_negatives) / total_campaigns) * 100 if total_campaigns > 0 else 0,
        "avgNegativesPerCampaign": total_negatives / total_campaigns if total_campaigns > 0 else 0
    }

def analyze_bid_adjustments(df):
    if 'Entity' not in df.columns or 'Percentage' not in df.columns or 'Campaign ID' not in df.columns:
        return {"totalCampaigns": 0, "adjustmentUsagePercent": 0}
    all_campaigns = df['Campaign ID'].dropna().unique()
    bidding_adjustments = df[df['Entity'] == 'Bidding Adjustment'].copy()
    bidding_adjustments['Percentage'] = pd.to_numeric(bidding_adjustments['Percentage'], errors='coerce').fillna(0)
    campaigns_with_adjustments = bidding_adjustments[bidding_adjustments['Percentage'] != 0]['Campaign ID'].dropna().unique()
    total_campaigns = len(all_campaigns)
    return {
        "totalCampaigns": total_campaigns,
        "adjustmentUsagePercent": (len(campaigns_with_adjustments) / total_campaigns) * 100 if total_campaigns > 0 else 0
    }

def calculate_overall_score(analysis):
    score = 0
    score += (analysis['structure']['goodStructurePercent'] / 100) * 50
    auto_ratio = analysis['automation']['autoPercent']
    if 10 <= auto_ratio <= 30: score += 20
    elif auto_ratio < 10 or (30 < auto_ratio <= 50): score += 10
    score += (analysis['funneling']['campaignsWithNegativesPercent'] / 100) * 15
    score += (analysis['bidAdjustments']['adjustmentUsagePercent'] / 100) * 15
    return min(100, int(score))

@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- Streamlit UI ---

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    st.markdown(
        "<a href='http://www.soypat.com' target='_blank'><img src='https://assets.zyrosite.com/m5KLvqrBjzHJbZkk/soypat_logo_white_bg-A0x11BXpQ0Tr9o5B.png' width='200'></a>",
        unsafe_allow_html=True
    )

st.title("SP Campaign Roaster 🔥")
st.markdown("Upload your **Sponsored Products** bulk sheet and get roasted with brutal honesty.")

with st.expander("Instructions - Click here to see how to get your file"):
    st.markdown("""
    1.  Go to your Amazon Advertising Console.
    2.  Navigate to **Sponsored Products** -> **Bulk Operations**.
    3.  Click **Create & download a custom spreadsheet**.
    4.  Select a date range of **Last 60 days**.
    5.  Ensure the boxes are ticked as shown in the image below.
    6.  Click **Create spreadsheet for download** and upload the file once it's ready.
    """)
    st.image("https://pomoconsole.com/roasterappsettings.png", caption="Use these settings to create your bulk report.", width=300)

uploaded_file = st.file_uploader("Choose your bulk file (.xlsx or .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            xls = pd.ExcelFile(uploaded_file)
            sheet_name = "Sponsored Products Campaigns"
            if sheet_name not in xls.sheet_names:
                st.warning(f'Sheet "{sheet_name}" not found. Using the first sheet: "{xls.sheet_names[0]}".')
                sheet_name = xls.sheet_names[0]
            df = pd.read_excel(xls, sheet_name=sheet_name)

        with st.spinner("Analyzing your campaigns... Preparing the roast 🔥"):
            structure_analysis = analyze_structure(df)
            analysis_results = {
                "structure": structure_analysis,
                "automation": analyze_automation(df),
                "funneling": analyze_funneling(df),
                "bidAdjustments": analyze_bid_adjustments(df)
            }
            overall_score = calculate_overall_score(analysis_results)

            # --- Prepare Detailed Breakdown DF ---
            campaign_level_df = df[df['Entity'] == 'Campaign'].copy()
            perf_cols = ['Campaign ID', 'Campaign Name (Informational only)', 'Spend', 'Sales', 'Orders', 'Clicks', 'Impressions']
            # Ensure performance columns exist
            for col in perf_cols:
                if col not in campaign_level_df.columns:
                    campaign_level_df[col] = 0
            
            # Convert to numeric, coercing errors
            for col in ['Spend', 'Sales', 'Orders', 'Clicks', 'Impressions']:
                 campaign_level_df[col] = pd.to_numeric(campaign_level_df[col], errors='coerce').fillna(0)

            detailed_df = pd.merge(
                campaign_level_df[perf_cols],
                structure_analysis['structure_df'],
                on='Campaign ID',
                how='left'
            )
            # Calculate ACOS and ROAS
            detailed_df['ACOS'] = (detailed_df['Spend'] / detailed_df['Sales']).where(detailed_df['Sales'] > 0, 0)
            detailed_df['ROAS'] = (detailed_df['Sales'] / detailed_df['Spend']).where(detailed_df['Spend'] > 0, 0)
            
            # Reorder columns for display
            display_cols = ['Campaign Name (Informational only)', 'Type', 'Spend', 'Sales', 'ACOS', 'ROAS', 'Orders', 'Clicks', 'Impressions', 'Campaign ID']
            detailed_df = detailed_df[display_cols]


        # --- Display Results ---
        st.divider()
        st.header("Overall Account Score", anchor=False)
        
        if overall_score >= 80:
            st.success(f"**{overall_score}/100** - Excellent structure! You're running a tight ship. 👏")
        elif overall_score >= 60:
            st.warning(f"**{overall_score}/100** - A solid foundation, but key areas need optimization.")
        else:
            st.error(f"**{overall_score}/100** - Your account needs a serious structural overhaul. 🔥")
        
        st.progress(overall_score)
        st.divider()
        
        cols = st.columns(4)
        with cols[0]:
            with st.container(border=True):
                structure = analysis_results['structure']
                st.subheader("🏗️ Structure")
                st.metric(label="Good Structures", value=f"{structure['goodStructurePercent']:.1f}%", delta=f"{structure['badStructurePercent']:.1f}% Bad", delta_color="inverse")
                if structure['badStructurePercent'] > 50: st.error("Over half your campaigns have problematic structures, leaking efficiency.")
                elif structure['badStructurePercent'] > 20: st.warning("A decent foundation, but messy campaigns are holding you back.")
                else: st.success("Excellent discipline! This organization gives you maximum control.")
                
        with cols[1]:
            with st.container(border=True):
                automation = analysis_results['automation']
                st.subheader("🤖 Automation")
                st.metric(label="Auto-Targeting Spend", value=f"{automation['autoPercent']:.1f}%", help=f"${automation['autoSpend']:,.2f} of ${automation['totalSpend']:,.2f} total")
                if automation['autoPercent'] > 40: st.error("You're letting Amazon's algorithm control your budget. Use Auto for discovery, not for burning cash.")
                elif automation['autoPercent'] > 30 or (automation['autoPercent'] < 10 and automation['totalSpend'] > 0): st.warning("Your Auto spend is outside the ideal 10-30% range.")
                else: st.success("Smart balance! You're using automation as a tool, not a crutch.")

        with cols[2]:
            with st.container(border=True):
                funneling = analysis_results['funneling']
                st.subheader("🔄 Funneling")
                st.metric(label="Campaigns w/ Negatives", value=f"{funneling['campaignsWithNegativesPercent']:.1f}%", help=f"Avg. {funneling['avgNegativesPerCampaign']:.1f} negatives per campaign")
                if funneling['campaignsWithNegativesPercent'] < 50: st.error("You are bleeding money on irrelevant searches. Add negatives to your Auto/Broad campaigns.")
                elif funneling['campaignsWithNegativesPercent'] < 80: st.warning("Inconsistent negative hygiene means your campaigns are wasting spend.")
                else: st.success("Excellent funneling discipline! You know what NOT to target.")

        with cols[3]:
            with st.container(border=True):
                bids = analysis_results['bidAdjustments']
                st.subheader("📊 Bid Adjustments")
                st.metric(label="Campaigns Using Adjustments", value=f"{bids['adjustmentUsagePercent']:.1f}%")
                if bids['adjustmentUsagePercent'] < 20: st.error("A flat bid is a rookie move. Analyze placement reports and start adjusting bids!")
                elif bids['adjustmentUsagePercent'] < 60: st.warning("You're starting to optimize, but you could be more aggressive.")
                else: st.success("Excellent! This granular control separates the pros from the amateurs.")
        
        st.divider()

        # --- Detailed Breakdown Section ---
        st.header("Detailed Campaign Breakdown", anchor=False)
        st.dataframe(
            detailed_df,
            column_config={
                "Spend": st.column_config.NumberColumn(format="$%.2f"),
                "Sales": st.column_config.NumberColumn(format="$%.2f"),
                "ACOS": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "ROAS": st.column_config.NumberColumn(format="%.2fx"),
            },
            use_container_width=True
        )

        csv_data = convert_df_to_csv(detailed_df)
        st.download_button(
           label="📥 Download Classified Data",
           data=csv_data,
           file_name='campaign_roaster_analysis.csv',
           mime='text/csv',
        )

        with st.expander("See Campaign Structure Definitions"):
            table_header = "| Type | Description | Conditions | Verdict |\n|:---:|:---|:---|:---:|\n"
            table_rows = ""
            for type_code, details in CAMPAIGN_TYPE_DEFINITIONS.items():
                table_rows += f"| **{type_code}** | {details['Description']} | {details['Conditions']} | {details['Verdict']} |\n"
            st.markdown(table_header + table_rows)


    except Exception as e:
        st.error(f"An error occurred during analysis: {e}")
        st.exception(e)
