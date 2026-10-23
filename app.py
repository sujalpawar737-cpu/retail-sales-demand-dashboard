"""Retail Sales & Demand Dashboard — DS2004 FODS course project extension.

Exploration runs on real positive-sales records from the UCI Online Retail dataset.
The prediction page offers a clearly labelled supplementary regression backtest;
it does not claim to be a saved model from the team's existing Colab notebook.
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analytics import product_summary, kmeans_products, eligible_products, weekly_history, model_result

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'/'sales_clean.csv.gz'
QUALITY=ROOT/'data'/'quality_report.json'
PALETTE=['#276D60','#CE7B51','#7087A0','#AF9B70','#775B8F','#5C9B95']

st.set_page_config(page_title='Retail Sales & Demand | FODS',page_icon='🛍️',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
    .stApp { background: #F8F8F4; }
    .block-container { max-width: 1390px; padding-top: 2.1rem; padding-bottom: 3.6rem; }
    h1,h2,h3 { letter-spacing: -.025em; color: #1F2B26; }
    h1 { font-size: 2.4rem !important; }
    [data-testid="stMetric"] { background: #fff; border: 1px solid #E3E9E4;
        padding: 16px 17px; border-radius: 13px; box-shadow: 0 3px 16px rgba(17,33,22,.025); }
    [data-testid="stMetricLabel"] { font-size: .87rem; color: #647168; }
    [data-testid="stMetricValue"] { font-size: 1.72rem; letter-spacing: -.02em; }
    [data-testid="stSidebar"] { background: #EFF2EC; }
    [data-testid="stSidebar"] h2 { color: #1F2B26; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-color: #E3E9E4; }
    .tiny-kicker { display:inline-block; color:#276D60; font-size:.72rem; font-weight:750;
        text-transform: uppercase; letter-spacing:.18em; margin-bottom: .45rem; }
    .hero { padding: 4px 0 4px; }
    .hero h1 { margin: .15rem 0 .45rem; }
    .hero p { max-width: 780px; color:#68756D; font-size: 1rem; line-height:1.5; }
    .note { padding: 11px 15px; border-radius:8px; border-left:3px solid #CE7B51;
        background:#F5EFE8; color:#594F44; font-size:.9rem; margin: 8px 0 16px; }
    .section-eyebrow { font-size:.7rem; color:#69776D; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
    footer { visibility: hidden; }
</style>''',unsafe_allow_html=True)

@st.cache_data(show_spinner='Loading prepared retail data…')
def get_sales():
    if not DATA.exists():
        raise FileNotFoundError('Missing data/sales_clean.csv.gz. Run scripts/prepare_data.py first.')
    df=pd.read_csv(DATA, compression='gzip', parse_dates=['date'],
        dtype={'invoice':'string','stock_code':'string','description':'string','country':'string',
               'quantity':'int32','unit_price':'float64','sales':'float64'},
        keep_default_na=False)
    return df

@st.cache_data
def get_quality():
    return json.loads(QUALITY.read_text(encoding='utf-8'))

@st.cache_data(show_spinner=False)
def calculate_products(df):
    return product_summary(df)

@st.cache_data(show_spinner=False)
def calculate_eligible(df):
    return eligible_products(df,limit=35)


def get_filtered(df,first,last,market):
    mask=(df.date.dt.date >= first) & (df.date.dt.date <=last)
    if market!='All countries':
        mask &= df.country.eq(market)
    return df.loc[mask]


def fmt_money(v):
    return '£'+format(v,',.0f')


def clean_plot(fig,*,height=380):
    fig.update_layout(
        template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',font=dict(color='#344139',size=12),
        colorway=PALETTE,margin=dict(l=15,r=20,t=35,b=20),height=height,
        hoverlabel=dict(bgcolor='#FFFFFF',font_color='#243129'),
        legend=dict(orientation='h',yanchor='bottom',y=1.03,xanchor='left',x=0),
    )
    fig.update_xaxes(showgrid=False,zeroline=False,linecolor='#DDE5DD')
    fig.update_yaxes(showgrid=True,gridcolor='#E8ECE7',zeroline=False)
    return fig


def section_title(title,subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)


def empty_state():
    st.info('No transactions match these filters. Try another country or a wider date range.')


def download_rows(df,label='Download selected sales records'):
    cols=['date','invoice','stock_code','description','quantity','unit_price','sales','country']
    st.download_button(label,df[cols].to_csv(index=False).encode('utf-8'),
        file_name='filtered_retail_sales.csv',mime='text/csv',use_container_width=False)

try:
    sales=get_sales()
    quality=get_quality()
except Exception as e:
    st.error('The prepared dataset cannot be loaded. '+str(e))
    st.stop()

all_countries=sorted(sales.country.dropna().unique().tolist())
min_day,max_day=sales.date.min().date(),sales.date.max().date()

with st.sidebar:
    st.markdown('### RETAIL / LAB')
    st.caption('Fundamentals of Data Science · Course Project')
    st.divider()
    page=st.radio('Explore',[
        '01  Overview','02  Product & Demand','03  Prediction Lab','04  Data & Methods',
    ],label_visibility='collapsed')
    st.divider()
    st.markdown('**Explore historical sales**')
    range_value=st.date_input('Invoice period',value=(min_day,max_day),min_value=min_day,max_value=max_day)
    if isinstance(range_value,tuple) and len(range_value)==2:
        first,last=range_value
    else:
        first,last=min_day,max_day
        st.caption('Complete the date range to apply the filter.')
    market=st.selectbox('Country',['All countries']+all_countries)
    st.caption('Overview and product pages follow these filters. The prediction lab uses the complete historical data.')
    st.divider()
    st.caption('Historical period: Dec 2010–Dec 2011\n\nSource: UCI Online Retail · Currency: GBP')
    st.link_button('Dataset reference ↗','https://archive.ics.uci.edu/dataset/352/online+retail',use_container_width=True)

filtered=get_filtered(sales,first,last,market)

st.markdown('''<div class="hero"><span class="tiny-kicker">DATA SCIENCE / RETAIL OPERATIONS</span>
<h1>Retail Sales &amp; Demand</h1>
<p>Explore what sold, when demand changed, and how historical retail data can support decisions — using genuine 2010–2011 transaction records.</p></div>''',unsafe_allow_html=True)

if page.startswith('01'):
    st.markdown('<span class="section-eyebrow">01 — Business overview</span>',unsafe_allow_html=True)
    if filtered.empty:
        empty_state(); st.stop()
    revenue=filtered.sales.sum()
    orders=filtered.invoice.nunique()
    units=filtered.quantity.sum()
    products=filtered.stock_code.nunique()
    a,b,c,d=st.columns(4)
    a.metric('Recorded positive sales',fmt_money(revenue),help='Sum of positive invoice lines, including legitimate fees; NOT net profit or return-adjusted revenue.')
    b.metric('Unique invoices',f'{orders:,}')
    c.metric('Units recorded',f'{units:,}')
    d.metric('Stock codes',f'{products:,}')
    st.markdown('<div class="note">Historical gross positive-line sales, not net sales or profit. Cancellation-coded invoices and other nonpositive lines are excluded. The first and last months are incomplete.</div>',unsafe_allow_html=True)
    left,right=st.columns([1.65,1],gap='large')
    with left:
        section_title('Sales movement','Monthly sales value across the selected time window')
        monthly=filtered.groupby(filtered.date.dt.to_period('M'))['sales'].sum().reset_index()
        monthly['month']=monthly['date'].astype(str)
        fig=px.line(monthly,x='month',y='sales',markers=True,labels={'month':'Month','sales':'Sales (£)'})
        fig.update_traces(line_color=PALETTE[0],line_width=3,marker_size=7)
        fig.update_yaxes(tickprefix='£')
        st.plotly_chart(clean_plot(fig),use_container_width=True)
    with right:
        section_title('Most frequently ordered products','Distinct invoices per product (minimum 10 orders)')
        candidates=calculate_products(filtered)
        top=candidates.loc[candidates.orders>=10].sort_values('orders',ascending=False).head(9).sort_values('orders')
        if not top.empty:
            fig=px.bar(top,x='orders',y='stock_code',orientation='h',
                hover_data=['description','units','revenue'],labels={'stock_code':'Product code','orders':'Distinct invoices'})
            fig.update_traces(marker_color=PALETTE[0]);st.plotly_chart(clean_plot(fig),use_container_width=True)
        else:
            st.info('Not enough repeated product purchases in this selection.')
    left,right=st.columns(2,gap='large')
    with left:
        section_title('Markets by recorded sales','Country is the buyer country recorded in the source data')
        country=filtered.groupby('country',as_index=False).sales.sum().nlargest(9,'sales').sort_values('sales')
        fig=px.bar(country,x='sales',y='country',orientation='h',labels={'sales':'Sales (£)','country':'Country'})
        fig.update_traces(marker_color=PALETTE[2]);fig.update_xaxes(tickprefix='£')
        st.plotly_chart(clean_plot(fig,height=360),use_container_width=True)
    with right:
        section_title('Purchase activity by weekday','Number of distinct positive-sales invoices by day')
        byday=filtered.assign(weekday=filtered.date.dt.day_name())
        dow=byday.groupby('weekday').invoice.nunique().reindex(
            ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'],fill_value=0).reset_index()
        fig=px.bar(dow,x='weekday',y='invoice',labels={'weekday':'Day','invoice':'Invoices'})
        fig.update_traces(marker_color=PALETTE[1]);st.plotly_chart(clean_plot(fig,height=360),use_container_width=True)
    section_title('Interpretation','These are examples of questions to investigate, not claims made before analysing the filtered results.')
    st.write('Compare high-sales periods against high-unit periods, identify which products dominate unit volume, and check whether the most active market influences the overall trend. Always interpret partial months cautiously.')
    with st.expander('Export underlying filtered positive-sales rows'):
        download_rows(filtered)

elif page.startswith('02'):
    st.markdown('<span class="section-eyebrow">02 — Product performance</span>',unsafe_allow_html=True)
    if filtered.empty:
        empty_state(); st.stop()
    summary=calculate_products(filtered)
    if summary.empty:
        empty_state(); st.stop()
    a,b=st.columns([1.2,1])
    with a:
        section_title('Find a product','Choose a stock code and examine its recorded activity')
        summary_options=summary.sort_values('orders',ascending=False).head(250)
        options=summary_options.stock_code.astype(str).tolist()
        label_lookup={str(row.stock_code):str(row.description) for row in summary_options.itertuples()}
        chosen=st.selectbox('Product',options,format_func=lambda x:f'{x} — {label_lookup.get(x,"")[:65]}')
    with b:
        st.markdown('##### How to read this page')
        st.caption('Units are summed from transaction line items. A high unit count does not always mean high revenue: products may have different prices.')
    subset=filtered.loc[filtered.stock_code.eq(chosen)]
    if subset.empty:
        empty_state(); st.stop()
    a,b,c,d=st.columns(4)
    a.metric('Selected product units',f'{subset.quantity.sum():,}')
    b.metric('Recorded sales',fmt_money(subset.sales.sum()))
    c.metric('Invoices with product',f'{subset.invoice.nunique():,}')
    d.metric('Avg units / invoice',f'{subset.quantity.sum()/max(1,subset.invoice.nunique()):,.1f}')
    left,right=st.columns([1.5,1],gap='large')
    with left:
        section_title('Product demand over time','Monthly units sold for the selected stock code')
        monthly=subset.groupby(subset.date.dt.to_period('M')).quantity.sum().reset_index()
        monthly['month']=monthly['date'].astype(str)
        fig=px.bar(monthly,x='month',y='quantity',labels={'month':'Month','quantity':'Units'})
        fig.update_traces(marker_color=PALETTE[0]);st.plotly_chart(clean_plot(fig),use_container_width=True)
    with right:
        section_title('Units and revenue','Top products in the selected period')
        top=summary.head(12)
        fig=px.scatter(top,x='units',y='revenue',hover_name='description',hover_data=['stock_code'],
            size='orders',labels={'units':'Units','revenue':'Sales (£)','orders':'Invoices'})
        fig.update_traces(marker_color=PALETTE[1],marker_opacity=.75)
        fig.update_yaxes(tickprefix='£')
        st.plotly_chart(clean_plot(fig),use_container_width=True)
    st.divider()
    section_title('Product groups using K-means','Optional syllabus-level clustering on product-level features, not customer behaviour')
    st.caption('Features: units, revenue, number of invoices and active months. We apply log(1 + x) and standardization before K-means. Groups are exploratory; not official demand ratings.')
    if len(summary)>=6:
        grouped=kmeans_products(summary,k=3)
        fig=px.scatter(grouped.head(350),x='units',y='revenue',color='cluster',hover_name='description',
           hover_data=['stock_code','orders','active_months'],log_x=True,log_y=True,
           labels={'units':'Units sold (log scale)','revenue':'Sales (£, log scale)','cluster':'K-means group'},
           color_discrete_sequence=PALETTE)
        st.plotly_chart(clean_plot(fig,height=425),use_container_width=True)
        st.dataframe(grouped.groupby('cluster').agg(products=('stock_code','count'),
            median_units=('units','median'),median_sales_gbp=('revenue','median')).reset_index(),
            hide_index=True,use_container_width=True)
        st.caption('Group labels are intentionally neutral. Use the medians above to interpret the groups. The plot shows only the 350 highest-volume products for readability; clustering includes all filtered products. Large one-off orders can influence group assignments.')
    else:
        st.info('Choose a wider date range or market to obtain enough products for clustering.')
    with st.expander('Product summary table'):
        st.dataframe(summary[['stock_code','description','units','revenue','orders','active_months']].head(100),hide_index=True,use_container_width=True)

elif page.startswith('03'):
    st.markdown('<span class="section-eyebrow">03 — Demand prediction lab</span>',unsafe_allow_html=True)
    st.warning('This is a separate, reproducible Linear Regression demonstration built for the dashboard. Your original Colab-trained model has **not** been supplied or connected. Replace this baseline with your course-project model after matching its preprocessing and evaluation.')
    section_title('Estimate a product’s next recorded week','Historical demonstration only — forecasting late 2011, not current-year sales')
    st.caption('For consistent comparisons, modelling uses the complete positive-sales history across all countries; sidebar exploration filters do not change training data. The first and last partial weeks are excluded.')
    good=calculate_eligible(sales)
    if good.empty:
        st.info('No products meet the minimum history/transaction requirement for this demonstration.');st.stop()
    product_list=good.stock_code.astype(str).tolist()
    names={str(row.stock_code):str(row.description) for row in good.itertuples()}
    chosen=st.selectbox('Select a frequently purchased stock code',product_list,
        format_func=lambda x:f'{x} — {names[x][:65]}')
    history=weekly_history(sales,chosen)
    try:
        results=model_result(history,holdout_weeks=10)
    except ValueError as e:
        st.info(str(e));st.stop()
    scores=results['metrics']
    a,b,c,d=st.columns(4)
    a.metric('Test MAE',f"{scores['MAE']:,.1f} units")
    b.metric('Test RMSE',f"{scores['RMSE']:,.1f} units")
    c.metric('Test R²',f"{scores['R2']:.2f}")
    d.metric('4-week baseline MAE',f"{scores['Baseline MAE']:,.1f} units")
    hold=results['holdout']
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=hold.week,y=hold.actual,name='Actual',mode='lines+markers',
        line=dict(color=PALETTE[0],width=3)))
    fig.add_trace(go.Scatter(x=hold.week,y=hold.linear_regression,name='Linear Regression',mode='lines+markers',
        line=dict(color=PALETTE[1],width=2,dash='dash')))
    fig.add_trace(go.Scatter(x=hold.week,y=hold.historical_average_baseline,name='4-week average baseline',mode='lines',
        line=dict(color=PALETTE[2],width=2,dash='dot')))
    fig.update_layout(yaxis_title='Units per complete week',xaxis_title='Week beginning')
    st.plotly_chart(clean_plot(fig,height=425),use_container_width=True)
    week_label=results['next_week'].strftime('%d %b %Y')
    with st.container(border=True):
        st.markdown(f'#### Historical one-week estimate · {week_label}')
        st.metric('Estimated units',f"{results['estimate']:,.0f}")
        st.caption('The estimate is generated after refitting on all available complete weeks. No current stock or supplier data is used; this is not an inventory recommendation. Values are clipped at zero.')
    if scores['MAE']<scores['Baseline MAE']:
        st.success('On this holdout, Linear Regression has lower MAE than the simple 4-week-average baseline.')
    else:
        st.info('On this holdout, the simple 4-week-average baseline performed as well or better. The regression estimate should not be treated as a reliable operational forecast.')
    with st.expander('What does the model actually use?'):
        st.markdown('''**Inputs:** previous week units, units two weeks ago, units four weeks ago, four-week average, and sequential week index.  
**Target:** units recorded in the next complete week.  
**Training and testing:** chronological split; final 10 complete weeks used for rolling one-step-ahead backtesting.  
**Algorithm:** syllabus-level Linear Regression, evaluated with MAE, RMSE, R² and a transparent naive baseline.  
**Limitation:** only about one year of historical sales exists; a linear model may not capture promotions, seasonality, business changes or stockouts.''')
        st.dataframe(hold.round(1),hide_index=True,use_container_width=True)

else:
    st.markdown('<span class="section-eyebrow">04 — Data lineage and methodology</span>',unsafe_allow_html=True)
    section_title('From an Excel file to reproducible analysis','Transparent scope, cleaning rules, source and caveats')
    st.markdown('''The app analyzes the **UCI Online Retail** dataset: invoice-level line items from a UK-based online retailer, **1 December 2010 to 9 December 2011**. The original Excel workbook is processed once with `scripts/prepare_data.py` into a compressed, customer-ID-free dataset for the app.''')
    a,b,c,d=st.columns(4)
    a.metric('Original line items',f"{quality['original_rows']:,}")
    b.metric('Included positive-sales lines',f"{quality['included_rows']:,}")
    c.metric('Cancellation-coded',f"{quality['cancellation_coded_rows']:,}")
    d.metric('Missing customer IDs',f"{quality['missing_customer_id']:,}")
    section_title('Excluded-line reasons')
    qnames=['Cancellation coded','Nonpositive quantity','Nonpositive unit price','Invalid / missing fields']
    qvalues=[quality['cancellation_coded_rows'],quality['nonpositive_quantity_rows'],
          quality['nonpositive_price_rows'],
          quality.get('missing_essential_field_rows',0)+quality.get('missing_or_invalid_numeric_date',0)]
    chart=px.bar(x=qnames,y=qvalues,text=qvalues,labels={'x':'Outcome','y':'Line items'})
    chart.update_traces(marker_color=PALETTE[0],textposition='outside')
    st.plotly_chart(clean_plot(chart,height=345),use_container_width=True)
    st.caption('Exclusion counts use a sequential decision rule: a row is assigned only its first applicable reason. Missing customer IDs are counted separately and are not automatically excluded.')
    st.markdown('''#### Cleaning decisions
1. Keep positive-quantity invoice lines with a valid unit price, date, product and country.
2. Exclude invoice numbers beginning with **C** from the positive-sales view, because they indicate cancellations.
3. Retain valid product sales with a missing CustomerID — a customer identifier is not needed for product-demand analysis.
4. Preserve duplicate-looking lines rather than indiscriminately deleting them; the original file has no unique row identifier to prove they are duplicate transactions.
5. Compute `Recorded sales = Quantity × UnitPrice` and clearly label it **positive-line sales**, not profit or return-adjusted net revenue.
6. Exclude recognized service/fee stock codes only from **product rankings and clustering**; the overview still includes valid positive service lines.''')
    st.divider()
    section_title('Data-science concepts demonstrated')
    st.markdown('''**Collect & prepare** — structured Excel transaction data, column types, missingness, cancellations, basic filtering.  
**Engineer features** — monthly time keys, product units, number of invoices, active months, derived sales.  
**Explore & visualize** — monthly trends, top products, country comparisons, demand distributions.  
**Learn** — K-means product grouping and a separate, explicitly labelled Linear Regression backtest.  
**Evaluate** — MAE, RMSE, R², baseline comparison and honest discussion of model limitations.''')
    st.info('This publicly shareable educational dashboard intentionally does not include CustomerID. The source is historical, does not contain stock availability or procurement costs, and cannot justify claims about profit, live demand or optimal reorder quantity.')
    st.markdown('**Dataset:** [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) · **Licence:** CC BY 4.0 · **Course:** DS2004 Fundamentals of Data Science')
    with st.expander('Inspect the prepared row format'):
        st.dataframe(sales[['date','invoice','stock_code','description','quantity','unit_price','sales','country']].head(20),hide_index=True,use_container_width=True)

st.divider()
st.caption('FODS · Retail Sales Trends and Product Demand Analysis  |  Real historical dataset  |  Educational analysis, not a live commercial system')
