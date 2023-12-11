import streamlit as st
import pandas as pd 
import numpy as np
import random
from datetime import date
import datetime as dt
from UI import * 
import plotly.express as px 
from streamlit_option_menu import option_menu 
from PIL import Image
import os
import pyexcel as p
import re
import io
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import time
from streamlit_extras.metric_cards import style_metric_cards
import plotly.graph_objects as go    # gauge chart
import altair as alt                 # horizontal bar chart


warnings.filterwarnings('ignore')

image = Image.open('bfc2023.png')  

st.set_page_config(page_title='DataAnalystWebApp', page_icon=image, layout='wide', initial_sidebar_state='auto')
todayDate = dt.date.today()
randomNum=(random.randint(0,10000))
st.sidebar.image(image, use_column_width=True)
# st.sidebar.markdown('<p> Contact: <a style="color: #ac41d9" href="mailto:hnamvu29@gmail.com">hnamvu29@gmail.com</a> </p>', unsafe_allow_html=True)
st.sidebar.divider()
# HIDE STREAMLIT
hide_style ='''
            <style>
               #MainMenu {visibility:hidden}
               footer {visibility:hidden}
               header {visibility:hidden}
            </style>
            '''
st.markdown(hide_style,unsafe_allow_html=True)

@st.cache_resource

def process_file(file):
    try:
        if file.name.endswith('.xlsx'):
            sheet_name = st.text_input('Your sheet name', value=None)
            header = st.slider('Your header',1,10,1,value=None)
            if sheet_name is not None or header is not None:
                df = pd.read_excel(file, sheet_name=sheet_name, header=header)
                df = df.loc[:, ~df.columns.str.match('Unnamed')]  # Remove columns like 'Unnamed'
            else:
                st.error('Sheet name not specified')
                return None
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
            df = df.loc[:, ~df.columns.str.match('Unnamed')]  # Remove columns like 'Unnamed'
        else:
            st.error("Invalid file type. Expected CSV or XLSX file.")
            return None
        return df
    except Exception as e:
        st.error(f"Error occurred: {e}")
        return None

def process_DIM_file(file):
    df = pd.read_excel(file, sheet_name='Sheet7')
    df = df.loc[:, ~df.columns.str.match('Unnamed')]
    return df

def show_reports(report1,report2):
    r1, r2 = st.columns(2)   
    r1.write(report1)
    r1.write(f'There are {report1.shape[0]} rows')
    r1.divider()
    r2.write(report2)
    r2.write(f'There are {report2.shape[0]} rows')
    r2.divider()

def process_report():
    # Upload NXT
    nxt_report = st.file_uploader("Upload Existing Import/Export report", type=["xlsx", "csv"])
    # Check if a file is uploaded
    if nxt_report is not None:
    # Process the file and get the DataFrame
        nxt = process_file(nxt_report)
        # Check if the DataFrame is not None
        if nxt is not None:
            nxt = nxt.iloc[:,1:]
            nxt.rename(columns={'Kho':'Kho nhập'},inplace=True)
            # Upload HDD
            hdd_report = st.file_uploader("Upload Shipping report", type=["xlsx", "csv"])
            # Check if a file is uploaded
            if hdd_report is not None:
            # Process the file and get the DataFrame
                hdd = process_file(hdd_report)
                # Check if the DataFrame is not None
                if hdd is not None: 
                    hdd = hdd[~hdd['Ngày cập nhật tiến độ'].str.startswith(('Total', 'Tổng'), na=False)]
                    show_reports(nxt,hdd)
                    df = pd.merge(nxt, hdd, how='outer', on=['Mã vật tư','Kho nhập'],suffixes=('_nxt','_hdd'),indicator=True)
                    both =  df[df['_merge'] == 'both']
                    left_right =  df[(df['_merge'] == 'left_only') | (df['_merge'] == 'right_only')]
                    st.write(f'There are {both.shape[0]} rows before processing the duplicated in I/E report')
                    columns_to_clean = ['Kho nhập', 'Mã vật tư','Item code ( Bravo)','Tên vật tư_nxt','ĐVT','Số lượng tồn đầu kỳ','Tổng số lượng nhập trong kỳ','Tổng số lượng xuất trong kỳ','Số lượng tồn cuối kỳ','Xuất từ Fulfill Orders','Nhập từ Receive Orders']
                    mask = both.duplicated(subset=columns_to_clean, keep='first')
                    # Update the specified columns for duplicated rows with an empty string
                    both.loc[mask, columns_to_clean] = ''
                    st.write(f'There are {both.shape[0]} rows after processing the duplicated in I/E report (the results before and after should be the same)')
                    df = pd.concat([both,left_right])
                    return df

def process_import_file(file):
    file_type = None
    try:
        if file.name.endswith('.xlsx'):
            sheet_name = st.text_input('Your sheet name', value=None)
            if sheet_name is not None:
                df = pd.read_excel(file, sheet_name=sheet_name, header=1)
                df.drop(['Unnamed: 5', 'Unnamed: 6', 'Unnamed: 8', '出口国家代码'], axis=1, inplace=True) 
                df = df.loc[:, ~df.columns.str.match('Unnamed')]
                # df = df.filter(regex='^(?!Unnamed).*')  
                file_type = 'xlsx'
            else:
                st.error('Sheet name not specified')
                return None, None

        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, header=1)
            df = df.filter(regex='^(?!Unnamed).*')  # Remove column like 'unnamed'
            df.drop(['Unnamed: 5', 'Unnamed: 6', 'Unnamed: 8', '出口国家代码'], axis=1, inplace=True) # FOR IMPORT ONLY
            # ADD 'TYPE' COLUMN 
            df.insert(6, 'Loại', '')      # IMPORT
            file_type = 'csv'
        else:
            st.error("Invalid file type. Expected CSV or XLSX file.")
            return 'Please upload the file', 'Please upload the file'
        return df, file_type
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None


def process_export_file(file):
    file_type = None
    try:
        if file.name.endswith('.xlsx'):
            sheet_name = st.text_input('Your sheet name', value=None)
            if sheet_name is not None:
                df = pd.read_excel(file, sheet_name=sheet_name, header=1)
                df = df.filter(regex='^(?!Unnamed).*')  # Remove column like 'unnamed'
                df.insert(8, 'Loại', '')      # EXPORT
                file_type = 'xlsx'
            else:
                st.error('Sheet name not specified')
                return None, None

        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, sheet_name='Sheet1', header=1)
            df = df.filter(regex='^(?!Unnamed).*')  # Remove column like 'unnamed'
            df.insert(8, 'Loại', '')      # EXPORT
            file_type = 'csv'
        else:
            st.error("Invalid file type. Expected CSV or XLSX file.")
            return 'Please upload the file', 'Please upload the file'
        return df, file_type
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None

    
def convert_df(df):
    # Create a writable file-like object in memory
    excel_buffer = io.BytesIO()
    # Save the DataFrame to the file-like object
    df.to_excel(excel_buffer, index=False)
    # Reset the buffer's position to the start for reading
    excel_buffer.seek(0)
    # Return the bytes of the Excel file
    return excel_buffer.getvalue()

def download_as_xlsx(df):
    try:
        save_name = st.text_input('Specify your file name:',value=None,placeholder='...')
        if save_name:  
            xlsx = convert_df(df)
            st.download_button(
                label="Download data as XLSX format",
                data=xlsx,
                file_name=f'{save_name}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  # Set MIME type to XLSX
            )
        else:
            st.error('File name not specified')
    except Exception as e:
        st.error(f"Error occurred: {e}")

# convert files
def convert_xls_to_xlsx(file_path):
    # Get the filename and extension
    filename, ext = os.path.splitext(file_path)
    # Create the new file name with .xlsx extension
    new_file_path = f"{filename}.xlsx"
    # Convert the .xls file to .xlsx using pyexcel
    p.save_book_as(file_name=file_path, dest_file_name=new_file_path)

# top analytics
def Analytics():
    total_record = (df['Mô_tả_sản_phẩm'].count())
    all_price_ = float(df['Đơn_giá'].sum())
    all_total = float(df['Thành_tiền'].sum())

    total1,total2,total3= st.columns(3,gap='small')
    with total1:
        st.info('Total Record', icon="🔍")
        st.metric(label = 'BFC', value= f"{total_record}")
        y_col = st.selectbox('Select y column', options=df.columns[3:], key='y_col1')
        st.info(f'{y_col} by each month', icon="🔍")
        fig1 = px.line(df, x=df['Month'], y=y_col)
        fig1.update_layout(width=300)
        st.plotly_chart(fig1)
    with total2:
        st.info('Selling Price', icon="🔍")
        st.metric(label='BFC', value=f"{all_price_:,.0f}")
        options = [col for col in df.columns if col != 'Unnamed: 0']
        value = st.selectbox('Select value column', options=options, key='value')
        name  = st.selectbox('Select name column', options=options, key='name')
        st.info(f'Relationship between {value} and {name}', icon="🔍")
        fig2 = px.pie(df, values=value, names=name)
        fig2.update_layout(width=300)
        st.plotly_chart(fig2)
    with total3:
        st.info('Expected Profit', icon="🔍")
        st.metric(label= 'BFC',value=f"{all_total:,.0f}")
        string_columns = df.select_dtypes(include=['object']).columns.tolist()
        y_col = st.selectbox('Select y column', options=string_columns, key='y_col3')
        st.info(f'{y_col} by each month', icon="🔍")
        try:
            fig3 = px.scatter(df, x=df['Month'], y=y_col, size=df['Số_lượng'])
            fig3.update_layout(width=300)
            st.plotly_chart(fig3)
        except ValueError:
            y_col = st.selectbox('Select y column (updated)', options=options[1:], key='y_col3.2')
            fig3 = px.scatter(df, x=df['Month'], y=y_col, size=df['Số_lượng'])
            fig3.update_layout(width=300)
            st.plotly_chart(fig3)
         

def Convert():
    # List of .xls files in the current directory
    xls_files = [file for file in os.listdir('.') if file.endswith('.xls')]
    # Convert each .xls file to .xlsx
    for xls_file in xls_files:
        convert_xls_to_xlsx(xls_file)


# Function to convert weight from bag to kilogram
def convert_to_kilogram(description, total, unit):
    # Check if the unit is already "Kilogram" and return the original values
    if unit.lower() in ['kg', 'kgm', 'kilogram', 'kilograms']:
        return total, unit
    if unit.lower() in ['ton','tne','ton (dry weight lg)']:     
        return total * 1000, 'Kilogram'
    # Convert 'gram' to 'Kilogram'              # UPDATE 16/10
    if unit.lower() in ['g', 'gr', 'grm', 'gram']:
        return total / 1000, 'Kilogram'
    # Search for weight information in the description
    # weight_match = re.search(r'(\d+(\.\d+)?)\s*(k?g|gr|gram|kilogram)', description, re.IGNORECASE)  # k?g = kg|g (the '?' make the 'k' optional)    # OLD VERSION - 05/09
    weight_match = re.search(r'(\d+(?:[\.,]\d+)?)\s*(k?g|gr|gram|kilogram)', description, re.IGNORECASE)
    # Use regular expression (re.search) to find the weight information in the description string.
    # The pattern: \d+(\.\d+)?          matches a number with an optional decimal point.
    # The pattern: \s*                  matches any whitespace characters (if present) between the number and the unit.
    # The pattern: (kg|g|gr|gram|kilogram) matches the unit, which can be any of the specified options (case-insensitive).
    if weight_match:
        # weight_value = float(weight_match.group(1))    # OLD VERSION - 05/09
        # weight_unit = weight_match.group(3).lower()    # OLD VERSION - 05/09
    # Replace any comma with a dot and convert to float
        weight_value = float(weight_match.group(1).replace(',', '.'))
        weight_unit = weight_match.group(2).lower()
        # Convert 'Total' and 'Unit' columns based on weight_unit
        if weight_unit.lower() in ['kg', 'kgm', 'kilogram', 'kilograms']:
            return total * weight_value, 'Kilogram'
        elif weight_unit.lower() in ['g', 'gr', 'gram']:
            return total * (weight_value / 1000), 'Kilogram'
        elif weight_unit in ['ton', 'tne']:                         # UPDATE 16/10
            return total * (weight_value * 1000), 'Kilogram'
    # If we find weight information in the description, extract the numeric value and the unit from the matched pattern.
    # If unit = "kg" "kilogram," update the 'Total' col by multiplying it with the weight value and set the 'Unit' column to "Kilogram."
    # If unit = "g" "gram,"      update the 'Total' col by multiplying it with the weight value divided by 1000 (to convert grams to kilograms) and set the 'Unit' column to "Kilogram."
    # If weight information not found, return original total and unit
    return total, unit



# SIDE BAR
with st.sidebar:
    selected = option_menu(
        menu_title='Menu', #required (default:None)
        options=['Preprocess','Merge','Analyze','Dashboard'], #required
        icons=['gear-wide-connected','subtract','clipboard-data','window-dash'], #optional -> find on Bootstrap
        menu_icon='cast', #optional
        default_index=0 #optional
    )


if selected == 'Preprocess':
    UI()
    st.divider()
    Convert()

    pre_process_type = st.sidebar.selectbox('Choose pre-processing data', ('Dried Fruit','Food Additive'),index=None,placeholder='Food Additive or Dried Fruit')

    if pre_process_type == 'Dried Fruit':
        # PROCESS FILE
        file_uploads = st.file_uploader(f'Upload your {pre_process_type} file', accept_multiple_files=True)
        dfs = {}  # Dictionary to store DataFrames
        if file_uploads is not None:
            for file_upload in file_uploads:
                df, file_type = process_export_file(file_upload)
                if df is not None:
                    filename = file_upload.name
                    dfs[filename] = df  # Store the DataFrame in the dictionary
            # Show the uploaded DataFrames
            for filename, df in dfs.items():
                # PRE-PROCESS 
                st.write(f"DataFrame before pre-processing {filename}:",df)
                df = df.iloc[:, 0:17]
                # df.rename(columns={'日期':'Time','申报号':'Mã_tờ_khai','进口商（越南语)':'Cty_nhập','进口商英文':'Cty_nhập(TA)',    # FOR IMPORT ONLY
                #                 '进口商地址越语':'Địa_chỉ','税务代码':'Mã_số_thuế','出口商':'Nhà_cung_cấp','出口商地址':'Địa_chỉ(ncc)',
                #                 '出口国':'Xuất_xứ','HS编码':'HScode','商品描述':'Sản_phẩm','数量':'Số_lượng','数量单位':'Đơn_vị',
                #                 '重量':'Cân_nặng','金额':'Thành_tiền','金额单位':'Tiền_tệ','单价':'Đơn_giá'},inplace=True)
                df.rename(columns={'日期':'Time','申报号':'Mã_tờ_khai','进口商':'Công_ty_nhập','进口商地址':'Địa_chỉ',               ## FOR EXPORT ONLY
                                '进口国代码':'Nước_nhập','出口商':'Nhà_cung_cấp','出口商ID':'Mã_số_thuế','出口国)':'Xuất_xứ',
                                'HS编码':'HScode','商品描述':'Miêu_tả_sản_phẩm','数量':'Số_lượng', '数量单位':'Đơn_vị','重量':'Khối_lượng',
                                '发票金额（美元）':'Hoá_đơn','单价':'Đơn_giá','金额单位':'Tiền_tệ','出口税额':'Thuế_xuất'},inplace=True)
                
                # ADD AND RENAME COLUMNS
                df.insert(df.columns.get_loc('Miêu_tả_sản_phẩm') + 1, 'SảnPhẩm', '')
                df.insert(df.columns.get_loc('Miêu_tả_sản_phẩm') + 1, 'PhânLoại', '')
                # df.rename(columns={'Mã_xuất_khẩu':'Mã_số_thuế'},inplace=True)
                # df['Mã_số_thuế'] = df['Mã_số_thuế'].astype(str)
                # # = df.rename(columns={'Mã_tờ_khai': 'Mã_số_thuế'}, inplace=True).astype({'Mã_số_thuế': str})

                # df = df[(df['Sản_phẩm'].str.contains('beverage|food additives|food supplement|supplement|food additive|Phụ gia thực phẩm|thực phẩm|sx thực phẩm|chế biến thực phẩm|confectionery materials', flags=re.IGNORECASE, regex=True)) 
                #         & (~df['Sản_phẩm'].str.contains('không dùng trong thực phẩm|not used in food', flags=re.IGNORECASE, regex=True))]
                # check valid row 
                df['Miêu_tả_sản_phẩm'].fillna('', inplace=True)
                st.write(f'Number of rows before filtering: {df.shape[0]}')
                df = df[(df['Miêu_tả_sản_phẩm'].str.contains('chuối|đu đủ|dứa|banana|pineapple|papaya', flags=re.IGNORECASE, regex=True))]
                st.write(f'Number of rows after filtering: {df.shape[0]}')

                df['HScode'] = df['HScode'].astype(str).apply(lambda x: '0' + x if x.startswith('8') else x)
                df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d')
                df['Day'] = df['Time'].dt.day
                df['Month'] = df['Time'].dt.month
                df['Year'] = df['Time'].dt.year
                # Get the column to be moved
                col1 = df.pop('Day')
                col2 = df.pop('Month')
                col3 = df.pop('Year')
                # Insert cols at the desired position (index 0)
                df.insert(1, 'Day', col1)
                df.insert(2, 'Month', col2)
                df.insert(3, 'Year', col3)
                df.drop(['Time'], axis=1, inplace=True)
                st.write(f"DataFrame after pre-processing and before processing {filename}:",df)
                # END PRE-PROCESS 

                # SET DATATYPES FOR COLUMNS
                df = df.astype({'Day': str, 'Month': str, 'Year': str, 'Mã_tờ_khai': int, 'Công_ty_nhập': str, 'Địa_chỉ': str,
                'Nước_nhập': str, 'Loại': str, 'Mã_số_thuế':str, 'Xuất_xứ':str, 'HScode':str, 'Miêu_tả_sản_phẩm':str, 'SảnPhẩm':str, 
                'PhânLoại':str, 'Số_lượng':float, 'Đơn_vị':str, 'Khối_lượng':float,'Hoá_đơn':float, 'Đơn_giá':float, 'Tiền_tệ':str})
                df['Số_lượng'] = df['Số_lượng'].round(2)
                df['Khối_lượng'] = df['Khối_lượng'].round(2)
                df['Hoá_đơn'] = df['Hoá_đơn'].round(2)
                df['Đơn_giá'] = df['Đơn_giá'].round(2)

                # PROCESS

                # EXPORT
                # df.loc[ df['Nhà_cung_cấp'].str.contains('CÁ NHÂN TỔ CHỨC KHÔNG CÓ MÃ SỐ THUẾ', flags=re.IGNORECASE, regex=True), 'Loại'  ] = 'Hộ Kinh Doanh Cá Thể'
                # df.loc[ df['Nhà_cung_cấp'].str.contains('DỊCH VỤ HÀNG KHÔNG| tiếp vận| dịch vụ hàng hoá', flags=re.IGNORECASE, regex=True), 'Loại'  ] = 'Xuất Uỷ Thác'
                # df.loc[ ~(df['Nhà_cung_cấp'].str.contains('CÁ NHÂN TỔ CHỨC KHÔNG CÓ MÃ SỐ THUẾ', flags=re.IGNORECASE, regex=True)) & ~(df['Nhà_cung_cấp'].str.contains('DỊCH VỤ HÀNG KHÔNG| tiếp vận| dịch vụ hàng hoá', flags=re.IGNORECASE, regex=True)), 'Loại'  ] = 'Xuất Trực Tiếp'
                # IMPORT
                df.loc[ df['Nhà_cung_cấp'].str.contains('CÁ NHÂN TỔ CHỨC KHÔNG CÓ MÃ SỐ THUẾ|KHÔNG CÓ MÃ SỐ THUẾ', flags=re.IGNORECASE, regex=True), 'Loại'  ] = 'Hộ Kinh Doanh Cá Thể'
                df.loc[ df['Nhà_cung_cấp'].str.contains('DỊCH VỤ HÀNG KHÔNG| tiếp vận| dịch vụ hàng hoá|KHACH LE SAN BAY TAN SON NHAT|KHACH LE SAN BAY QUOC TE TAN SON NHAT|KHACH LE|HANH KHACH TREN CAC CHUYEN BAY QUOC TE', flags=re.IGNORECASE, regex=True), 'Loại'  ] = 'Xuất Uỷ Thác'
                df.loc[ ~(df['Nhà_cung_cấp'].str.contains('CÁ NHÂN TỔ CHỨC KHÔNG CÓ MÃ SỐ THUẾ', flags=re.IGNORECASE, regex=True)) & ~(df['Nhà_cung_cấp'].str.contains('DỊCH VỤ HÀNG KHÔNG| tiếp vận| dịch vụ hàng hoá|KHACH LE SAN BAY TAN SON NHAT|KHACH LE SAN BAY QUOC TE TAN SON NHAT|KHACH LE|HANH KHACH TREN CAC CHUYEN BAY QUOC TE', flags=re.IGNORECASE, regex=True)), 'Loại'  ] = 'Xuất Trực Tiếp'

                # Assuming you have an exchange rate dictionary
                exchange_rates = {
                    'USD': 1.0,  # USD to USD exchange rate (always 1)
                    'AUD': 0.67, # Exchange rate for AUD to USD
                    'EUR': 1.11, # Exchange rate for EUR to USD
                    'GBP': 1.29,  # Exchange rate for GBP to USD
                    'VND':0.000042,   # Exchange rate for VND to USD
                    'CAD':0.75,       # Exchange rate for CAD to USD
                    'CHF':1.14,       # Exchange rate for CHF to USD
                    'CNY':0.14,       # Exchange rate for CNY to USD
                    'HKD':0.13,       # Exchange rate for HKD to USD
                    'JPY':0.0070      # Exchange rate for JPY to USD
                }
                # Function to convert prices to USD based on the currency
                def convert_total_to_usd(row):
                    currency = row['Tiền_tệ']
                    exchange_rate = exchange_rates.get(currency, 1.0)  # Default to 1 if currency not found
                    return row['Hoá_đơn'] * exchange_rate
                def convert_perUnit_to_usd(row):
                    currency = row['Tiền_tệ']
                    exchange_rate = exchange_rates.get(currency, 1.0)  # Default to 1 if currency not found
                    return row['Đơn_giá'] * exchange_rate
                # Apply the function to the DataFrame to convert 'Đơn_giá' to USD
                df['Hoá_đơn'] = df.apply(convert_total_to_usd, axis=1)
                df['Đơn_giá'] = df.apply(convert_perUnit_to_usd, axis=1)
                df.loc[ df['Tiền_tệ'].isin(['AUD','EUR','GBP','VND','CAD','CHF','CNY','HKD','JPY']), 'Tiền_tệ'] = 'USD'
           
                # Set the 'Sản_phẩm' column to lowercase to make the comparison case-insensitive
                df['Miêu_tả_sản_phẩm'] = df['Miêu_tả_sản_phẩm'].str.lower()
                # Fill missing values in the 'Sản_phẩm' column with an empty string
                df['Miêu_tả_sản_phẩm'].fillna('', inplace=True)

                # CHECK NULL VALUE
                # st.write(f'The number of null value in column "MST" are: {(df["Mã_số_thuế"]==0).sum()}') # for INT datatype
                # st.write(f'The number of "0" in column "Mã_số_thuế" are: {df["Mã_số_thuế"].value_counts()["0"]}') # for STR datatype

                # SẢN PHẨM
                # Find rows where the 'Sản_phẩm' column contains 'banana' or 'chuối' (case-insensitive)
                banana_rows = df[(df['Miêu_tả_sản_phẩm'].str.contains('chuối|banana|bananas', flags=re.IGNORECASE, regex=True)) & (~df['Miêu_tả_sản_phẩm'].str.contains('fruit|hoa quả|mix|mixed|includes|include|gồm', flags=re.IGNORECASE, regex=True))]
                # Set the 'SảnPhẩm' column to 'Banana' for the matching rows
                df.loc[banana_rows.index, 'SảnPhẩm'] = 'Chuối'

                # Find rows where the 'Sản_phẩm' column contains papaya (case-insensitive)
                papaya_rows = df[(df['Miêu_tả_sản_phẩm'].str.contains('đu đủ|papaya', flags=re.IGNORECASE, regex=True)) & (~df['Miêu_tả_sản_phẩm'].str.contains('fruit|hoa quả|mix|mixed|includes|include|gồm', flags=re.IGNORECASE, regex=True))]
                # Set the 'SảnPhẩm' column to 'Banana' for the matching rows
                df.loc[papaya_rows.index, 'SảnPhẩm'] = 'Đu Đủ'

                # Find rows where the 'Sản_phẩm' column contains pineapple (case-insensitive)
                pineapple_rows = df[(df['Miêu_tả_sản_phẩm'].str.contains('dứa|pineapple', flags=re.IGNORECASE, regex=True)) & (~df['Miêu_tả_sản_phẩm'].str.contains('fruit|hoa quả|mix|mixed|includes|include|gồm', flags=re.IGNORECASE, regex=True))]
                # Set the 'SảnPhẩm' column to 'Banana' for the matching rows
                df.loc[pineapple_rows.index, 'SảnPhẩm'] = 'Dứa'

                # Find rows where the 'Sản_phẩm' column contains mix (case-insensitive)
                mix_rows = df[df['Miêu_tả_sản_phẩm'].str.contains('fruit|hoa quả|mix|mixed|includes|include|gồm', flags=re.IGNORECASE, regex=True)]
                # Set the 'SảnPhẩm' column to 'Banana' for the matching rows
                df.loc[mix_rows.index, 'SảnPhẩm'] = 'Mix'

                st.write(df['SảnPhẩm'].value_counts())
                
                # PHÂN LOẠI
                # SẤY KHÔ
                saykho = df[df['Miêu_tả_sản_phẩm'].str.contains('khô', flags=re.IGNORECASE, regex=True)]
                df.loc[saykho.index, 'PhânLoại'] = 'Sấy Khô'

                # SẤY DẺO
                saydeo = df[df['Miêu_tả_sản_phẩm'].str.contains('dẻo|soft', flags=re.IGNORECASE, regex=True)]
                df.loc[saydeo.index, 'PhânLoại'] = 'Sấy Dẻo'

                # SẤY GIÒN
                saygion = df[df['Miêu_tả_sản_phẩm'].str.contains('crispy|giòn', flags=re.IGNORECASE, regex=True)]
                df.loc[saygion.index, 'PhânLoại'] = 'Sấy Giòn'

                # LEFTOVER
                leftover = df[~(df.index.isin(saykho.index) | df.index.isin(saydeo.index) | df.index.isin(saygion.index))]
                df.loc[leftover.index, 'PhânLoại'] = 'Sấy'

                # TRANSFORM THE UNIT TO KILOGRAM
                # Apply the function to update 'Total' and 'Unit' columns
                df['Số_lượng'], df['Đơn_vị'] = zip(*df.apply(lambda row: convert_to_kilogram(row['Miêu_tả_sản_phẩm'], row['Số_lượng'], row['Đơn_vị']), axis=1))
                # Make the value consistent (= Kilogram)
                df.loc[df['Đơn_vị'].isin(['Kilogram','Kilograms','KGM','Kg','kg','KILOGRAMS']),'Đơn_vị'] = 'Kilogram'

                st.write(f"DataFrame after processing {filename}:",df)
                # END PROCESS

                download_as_xlsx(df)

        if file_uploads == []:
            st.info(f"Please upload the {pre_process_type} file first.")
            

    elif pre_process_type == 'Food Additive':
        # PROCESS FILE
        file_uploads = st.file_uploader(f'Upload your {pre_process_type} file', accept_multiple_files=True)
        dfs = {}  # Dictionary to store DataFrames
        if file_uploads is not None:
            for file_upload in file_uploads:
                # df, file_type = process_import_file(file_upload)
                df, file_type = process_import_file(file_upload)
                if df is not None:
                    filename = file_upload.name
                    dfs[filename] = df  # Store the DataFrame in the dictionary
            # Show the uploaded DataFrames
            for filename, df in dfs.items():
                # PRE-PROCESS 
                st.write(f"DataFrame before pre-processing {filename}:",df)
                st.write('Total rows and columns of dataFrame before pre-processing:',df.shape)
                st.write('Column names:',df.columns)
                # df = df.iloc[:, 0:18].join(df[['海关名称']])
                # df = df.iloc[:, 0:18].join(df.iloc[:, [-6]])

                df.rename(columns={'日期':'Time','申报号':'Mã_tờ_khai','进口商（越南语)':'Công_ty_nhập','进口商英文':'Công_ty_nhập(TA)',    # FOR IMPORT ONLY
                                '进口商地址越语':'Địa_chỉ','税务代码':'Mã_số_thuế','出口商':'Nhà_cung_cấp','出口商地址':'Địa_chỉ(ncc)',
                                '出口国':'Xuất_xứ','HS编码':'HScode','商品描述':'Mô_tả_sản_phẩm','数量':'Số_lượng','数量单位':'Đơn_vị',
                                '重量':'Khối_lượng','金额':'Thành_tiền','金额单位':'Tiền_tệ','单价':'Đơn_giá','海关名称':'Cảng'},inplace=True)
                

                df['Mã_tờ_khai'].fillna('', inplace=True)
                # Function to safely convert to integer, replacing empty strings with 0
                def safe_int(x):
                    try:
                        return int(x)
                    except ValueError:
                        return 0
                # Apply the safe_int function to the 'Mã_tờ_khai' column
                df['Mã_tờ_khai'] = df['Mã_tờ_khai'].apply(safe_int)

                # CHECK VALID ROW
                # FIRST FILTERING 
                st.write(f'Number of rows before filtering: {df.shape[0]}')

                with st.expander('Filtering'):
                    clean_column = st.selectbox('What column do you need to clean?', df.columns, key='clean_column')
                    clean_thing = st.text_input('What thing do you need?', key='clean_thing')
                    df[clean_column].fillna('', inplace=True)
                    df = df[(df[clean_column].str.contains(f'{clean_thing}', flags=re.IGNORECASE, regex=True))]

                    food_additive = st.text_input('What food additives are you processing?', key='food_additive')
                    df['Mô_tả_sản_phẩm'].fillna('', inplace=True)
                    df = df[(df['Mô_tả_sản_phẩm'].str.contains(f'{food_additive}', flags=re.IGNORECASE, regex=True))]


                    # SECOND FILTERING 
                    # User input for filtering needs
                    needs = st.text_input(f'Any requirements with your food additives ? (comma-separated, e.g., no,none. Do not have -> type no/none)')     # multiple exceptions
                    # Split the input into a list of needs
                    need_list = [n.strip() for n in needs.split(',') if n.strip()]
                    # User input for filtering exceptions
                    exceptions = st.text_input(f'Any exceptions with your food additives ? (comma-separated, e.g., no,none. Do not have -> type no/none)')     # multiple exceptions
                    # Split the input into a list of exceptions
                    exception_list = [e.strip() for e in exceptions.split(',') if e.strip()]
                    # df = df[(df['Sản_phẩm'].str.contains('beverage|food additives|food supplement|supplement|food additive|flavor|Phụ gia thực phẩm|thực phẩm|sx thực phẩm|chế biến thực phẩm|confectionery materials', flags=re.IGNORECASE, regex=True)) 
                    #     & (~df['Sản_phẩm'].str.contains('không dùng trong thực phẩm|not used in food|viên nang|không chứa trong thực phẩm', flags=re.IGNORECASE, regex=True))]

                    for word1 in need_list:
                        for word2 in exception_list:
                            if word1.lower() in ['no', 'none'] and word2.lower() in ['no', 'none']:
                                df = df  # No filtering if both are 'no' or 'none'
                            elif word1.lower() in ['no', 'none']:
                                df = df[~(df['Mô_tả_sản_phẩm'].str.contains(fr'\b{word2}\b', flags=re.IGNORECASE, regex=True))]
                            elif word2.lower() in ['no', 'none']:
                                df = df[(df['Mô_tả_sản_phẩm'].str.contains(fr'\b{word1}\b', flags=re.IGNORECASE, regex=True))]
                            else:
                                pass


                st.write(f'Number of rows after filtering: {df.shape[0]}')

                df = df[df['Time'] != '日期']
                # Convert the 'Time' column to datetime
                df['Time'] = pd.to_datetime(df['Time'], format='%Y-%m-%d', errors='coerce')
                df['Day'] = df['Time'].dt.day
                df['Month'] = df['Time'].dt.month
                df['Year'] = df['Time'].dt.year
                # Get the column to be moved
                col1 = df.pop('Day')
                col2 = df.pop('Month')
                col3 = df.pop('Year')
                # Insert cols at the desired position (index 0)
                df.insert(1, 'Day', col1)
                df.insert(2, 'Month', col2)
                df.insert(3, 'Year', col3)
                df.drop(['Time'], axis=1, inplace=True)
                st.write(f"DataFrame after pre-processing and before processing {filename}:",df)
                st.write('Total rows and columns of dataFrame after pre-processing',df.shape)
                # END PRE-PROCESS 
                st.write("Column names in DataFrame:", df.columns)

                # SET DATATYPES FOR COLUMNS
                # df = df.astype({'Day': str, 'Month': str, 'Year': str, 'Mã_tờ_khai': int, 'Công_ty_nhập': str, 'Công_ty_nhập(TA)':str, 'Địa_chỉ': str,
                # 'Mã_số_thuế':str, 'Nhà_cung_cấp':str, 'Địa_chỉ(ncc)':str, 'Xuất_xứ':str, 'HScode':str, 'Sản_phẩm':str,  
                # 'Số_lượng':float, 'Đơn_vị':str, 'Khối_lượng':float,'Thành_tiền':float, 'Tiền_tệ':str, 'Đơn_giá':float, 'Cảng':str})

                # Specify the columns and their corresponding data types
                column_data_types = {'Day': str, 'Month': str, 'Year': str, 'Mã_tờ_khai': int, 'Công_ty_nhập': str, 'Công_ty_nhập(TA)': str, 'Địa_chỉ': str,
                                    'Mã_số_thuế': str, 'Nhà_cung_cấp': str, 'Địa_chỉ(ncc)': str, 'Xuất_xứ': str, 'HScode': str, 'Mô_tả_sản_phẩm': str,
                                    'Số_lượng': float, 'Đơn_vị': str, 'Khối_lượng': float, 'Thành_tiền': float, 'Tiền_tệ': str, 'Đơn_giá': float, 'Cảng': str}

                # Change the data type of specified columns
                for column, data_type in column_data_types.items():
                    if column in df.columns:
                        df[column] = df[column].astype(data_type)

                df['Số_lượng'] = df['Số_lượng'].round(2)
                df['Khối_lượng'] = df['Khối_lượng'].round(2)
                df['Thành_tiền'] = df['Thành_tiền'].round(2)
                df['Đơn_giá'] = df['Đơn_giá'].round(2)

                # TRANSFORM THE UNIT TO KILOGRAM
                # # Apply the function to update 'Total' and 'Unit' columns (ON EXISTING COLUMNS)
                # df['Số_lượng'], df['Đơn_vị'] = zip(*df.apply(lambda row: convert_to_kilogram(row['Sản_phẩm'], row['Số_lượng'], row['Đơn_vị']), axis=1))
                # # Make the value consistent (= Kilogram)
                # df.loc[df['Đơn_vị'].isin(['Kilogram','Kilograms','KGM','Kg','kg','KILOGRAMS']),'Đơn_vị'] = 'Kilogram'

                # Apply the convert_to_kilogram function to create new columns    (ON NEW COLUMNS)
                updated_values = df.apply(lambda row: pd.Series(convert_to_kilogram(row['Mô_tả_sản_phẩm'], row['Số_lượng'], row['Đơn_vị'])), axis=1)
                df['updated_Số_lượng'] = updated_values[0]
                df['updated_Đơn_vị'] = updated_values[1]
                df.loc[df['updated_Đơn_vị'].isin(['Kilogram', 'Kilograms', 'KGM', 'Kg', 'kg', 'KILOGRAMS']), 'updated_Đơn_vị'] = 'Kilogram'

                c1 = df.pop('updated_Số_lượng')
                c2 = df.pop('updated_Đơn_vị')
                df.insert(13, 'updated_Số_lượng', c1)
                df.insert(14, 'updated_Đơn_vị', c2)

                st.write(f"DataFrame after processing {filename}:",df)
                # END PROCESS

                download_as_xlsx(df)

        if file_uploads == []:
            st.info(f"Please upload the {pre_process_type} file first.")
    else:
        st.warning('Please specify your needs!')

#----------------------------------------------------------------
dfs = []
def process_file(file):
    df = pd.read_excel(file)  
    return df

if selected == 'Merge':
    UI()
    st.divider()

    # File Upload
    file_uploads = st.file_uploader('Upload your files', accept_multiple_files=True)

    # Step 1: Read each uploaded file and store the data as separate DataFrames
    if file_uploads is not None:
        for file_upload in file_uploads:
            df = process_file(file_upload)
            if df is not None:
                dfs.append(df)  # Append the DataFrame to the list
    # Step 2: Concatenate the DataFrames along the rows axis (axis=0)
    if dfs:
        combined_df = pd.concat(dfs, axis=0, ignore_index=True)
        # Step 3: Display or use the combined DataFrame as needed
        st.write("Combined DataFrame:", combined_df)
        download_as_xlsx(combined_df)
    else:
        st.info("Please upload some files first.")
#----------------------------------------------------------------

def check_and_remove_duplicates(df):
    st.write("Original DataFrame rows:", df.shape[0])
    # select the columns that need to check duplicated
    all_columns = st.toggle('Select all columns ?')
    if all_columns:
        duplicated_rows = df[df.duplicated(keep=False)]
        # Print the duplicated rows
        st.write("Number of duplicated rows:", duplicated_rows.shape[0])
        st.write("Duplicated Rows:")
        st.write(duplicated_rows)
        # Remove the duplicate rows, keeping the first occurrence
        df_no_duplicates = df.drop_duplicates(keep='first', inplace=False)

        st.write('Number of rows after removing duplicates:', df_no_duplicates.shape[0])
        st.write('Filtered DataFrame:', df_no_duplicates)
        return df_no_duplicates
    
    else:
        check_object = st.toggle('Food Additive product ?')
        if check_object:
            declaration_code = st.selectbox('Please specify the "Declaration Code column (ma to khai)"', df.columns,index=None,placeholder='Declaration Code column...')
            if declaration_code:
                df[declaration_code] = df[declaration_code].astype('str')
                # Extract the first 11 digits and the 12th digit
                df['first_11_digits'] = df[declaration_code].str[:11]
                df['12th_digit'] = df[declaration_code].str[11:]
                # Convert 12th digit to numeric for comparison
                df['12th_digit'] = pd.to_numeric(df['12th_digit'])
                selected_columns = st.multiselect('Select the columns that need to check duplicated:', df.columns,placeholder='columns to check...')
                array = np.array(selected_columns)
                list_selected_columns = array.tolist()
                if list_selected_columns: 
                    list_selected_columns.append('first_11_digits')
                    duplicated_rows = df[df.duplicated(subset=list_selected_columns, keep=False)]
                    st.write("Duplicated rows:", duplicated_rows.shape[0])
                    st.write(duplicated_rows)
                    # Check for duplicates based on the first 11 digits
                    df_no_duplicates = df.sort_values('12th_digit').drop_duplicates(subset=list_selected_columns, keep='last')
                    st.write('Number of rows after removing duplicates:', df_no_duplicates.shape[0])
                    st.write('Filtered DataFrame:', df_no_duplicates)
                    return df_no_duplicates
                else: 
                    duplicated_rows = df[df.duplicated(subset=['first_11_digits'], keep=False)]
                    st.write("Duplicated rows:", duplicated_rows.shape[0])
                    st.write(duplicated_rows)
                    # Check for duplicates based on the first 11 digits
                    df_no_duplicates = df.sort_values('12th_digit').drop_duplicates(subset=['first_11_digits'], keep='last')
                    st.write('Number of rows after removing duplicates:', df_no_duplicates.shape[0])
                    st.write('Filtered DataFrame:', df_no_duplicates)
                    return df_no_duplicates
            
            else:
                st.warning('The process cannot be executed if there is no "Declaration Code"')

        else:
            selected_columns = st.multiselect('Select the columns that need to check duplicated:', df.columns,placeholder='columns to check...')
            if selected_columns:
                duplicated_rows = df[df.duplicated(subset=selected_columns, keep=False)]
                st.write("Duplicated rows:", duplicated_rows.shape[0])
                st.write(duplicated_rows)
                # Remove the duplicate rows, keeping the first occurrence
                df_no_duplicates = df.drop_duplicates(subset=selected_columns, keep='first', inplace=False)

                st.write('Number of rows after removing duplicates:', df_no_duplicates.shape[0])
                st.write('Filtered DataFrame:', df_no_duplicates)
                return df_no_duplicates
            else:
                st.warning("No columns selected. Please select at least one column.")


# ------------UPDATE 03/11/2023------------
def extract_words_after_keyword(df, column_name, keyword_list, specified_list=[]):
    new_column_name = 'Brand'
    df[new_column_name] = None

    df_copy = df[column_name].copy()  # Create a copy of the column

    for index in df_copy.index:
        description = df_copy[index]
        description_lower = description.lower()  # Convert to lowercase for processing
        # keyword_found = False
        for keyword in keyword_list:
            keyword_lower = keyword.lower()  # Convert each keyword to lowercase
            pattern = r'{}[^a-zA-Z]*[ ]*([^,.;]+)'.format(re.escape(keyword_lower))
            matches = re.findall(pattern, description_lower, re.IGNORECASE)
            if matches:
                for match in matches:
                    words = match.split()
                    filtered_words = []
                    for word in words:
                        if word[-1] in [',', '.', ';']:
                            word = word[:-1]  # Remove the last character if it's a dot, comma, or semi-colon
                        # Check if the word contains numbers/date
                        if re.match(r'^\d+([.,]?\d*)?$', word) or re.match(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', word) or word.lower() in specified_list or any(char.isdigit() for char in word):
                            continue
                        # Check if the word contains only alphabets
                        if not word.isalpha():
                            continue
                        filtered_words.append(word)
                    extracted_word = filtered_words[0] if filtered_words else None
                    if extracted_word and extracted_word not in specified_list:
                        df.at[index, new_column_name] = extracted_word
                        # keyword_found = True
                        break
            # if keyword_found:
            #     break
            if df.at[index, new_column_name]:
                break

        # if not keyword_found:
        #     for word in description_lower.split():
        #         if word in keyword_list and word not in specified_list:
        #             df.at[index, new_column_name] = description_lower.split()[description_lower.split().index(word) + 1]
        #             break

    return df

# ------------UPDATE 03/11/2023------------
# def extract_words_after_keyword(df, column_name, keyword_list, specified_list=[]):
#     new_column_name = 'Brand'
#     df[new_column_name] = None

#     for index, description in enumerate(df[column_name]):
#         if pd.notnull(description):
#             description_lower = description.lower()
#             for keyword in keyword_list:
#                 keyword_lower = keyword.lower()
#                 pattern = re.compile(r'{}[^a-zA-Z]*[ ]*([^,.;]+)'.format(re.escape(keyword_lower)), re.IGNORECASE)
#                 matches = re.findall(pattern, description_lower)
#                 if matches:
#                     for match in matches:
#                         words = match.split()
#                         filtered_words = []
#                         for word in words:
#                             if word[-1] in [',', '.', ';']:
#                                 word = word[:-1]  # Remove the last character if it's a dot, comma, or semi-colon
#                             # Check if the word contains numbers/date
#                             if re.match(r'^\d+([.,]?\d*)?$', word) or re.match(r'\d{1,2}[./-]\d{1,2}[./-]\d{2,4}', word) or word.lower() in specified_list or any(char.isdigit() for char in word):
#                                 continue
#                             # Check if the word contains only alphabets
#                             if not word.isalpha():
#                                 continue
#                             filtered_words.append(word)
#                         extracted_word = filtered_words[0] if filtered_words else None
#                         if extracted_word and extracted_word not in specified_list:
#                             df.at[index, new_column_name] = extracted_word
#                             break
#                 if df.at[index, new_column_name]:
#                     break
#     return df

def show_dim_fact(dim_df,fact_df):
    dim, fact = st.columns(2)   
    dim.write('Your DIM dataframe:')
    dim.write(dim_df)
    dim.write(f'There are {dim_df.shape[0]} rows in your DIM table')
    dim.divider()
    fact.write('Your FACT dataframe:')
    fact.write(fact_df)
    fact.write(f'There are {fact_df.shape[0]} rows in your FACT table')
    fact.divider()

def show_info_column(df):
    column = st.selectbox('Which column do you want to inspect ?',df.columns)
    if column:
        c1,c2 = st.columns([1,2],gap='medium')
        column_nullvalue = df[(df[column].isnull()) | (df[column] == 0) | (pd.isna(df[column])) | (df[column] == 'nan')]
        c1.write(f'There are {df[column].shape[0] - column_nullvalue.shape[0]} found value(s) and {column_nullvalue.shape[0]} null value(s) in {column} column')
        c2.write(df[column].value_counts())

def adjust_column_position(df, old_column_name, new_column_name):
    market_class_check = st.toggle('Market Classification Position ?')
    if market_class_check:
        index_col = st.slider(f'Select the position of "{new_column_name}" column', 0, len(df.columns)-1,key='new_index_col')
        old_col = df.pop(old_column_name)
        df.insert(index_col, new_column_name, old_col)
        st.write(f'Dataframe with new position of {new_column_name} column', df)
    else:
        try:
            index_col = st.slider(f'Select the position of "{new_column_name}" column', 0, len(df.columns),key='new_index_col')
            old_col = df.pop(old_column_name)
            df.insert(index_col, new_column_name, old_col)
            st.write(f'Dataframe with new position of {new_column_name} column', df)
        except IndexError as e:
            st.error(f"Index Error occurred: {e}")

def create_validation_column(df, filtered_on_column, exception_words):
    df['Validation'] = 'Yes'  # Set the default value for the Validation column to 'Yes'
    for word in exception_words:
        mask = df[filtered_on_column].str.contains(word, case=False, na=False)  # Check if the word exists in the description
        df.loc[mask, 'Validation'] = 'No'  # Set the Validation column to 'No' where the word is found
    return df

def add_sum_row(df):
    columns_to_sum = st.multiselect('Choose column(s) to sum', df.columns)
    sum_values = df[columns_to_sum].sum()
    # Creating a sum row
    sum_df = pd.DataFrame([sum_values], columns=columns_to_sum, index=['Total'])
    # Concatenating the sum row to the original DataFrame
    df_with_sum = pd.concat([df, sum_df])
    return df_with_sum

def numerical_highlight_cell_rules(df, column, conditions):
    def apply_color(val):
        for condition, color in conditions.items():
            if condition(val):
                return f'background-color: {color}'
        return ''
    return df.style.applymap(apply_color, subset=[column])

def categorical_highlight_cell_rules(df, column, conditions):
    def apply_color(val):
        for condition, color in conditions.items():
            if condition(val):
                return f'background-color: {color}'
        return ''
    return df.style.applymap(apply_color, subset=[column])


# function for year-month-1
def get_month(x):
    return dt.datetime(x.year,x.month,1) # get year, month and 1st day

# create a date element function to get a series for subtraction
def get_date_elements(df, column):
  day = df[column].dt.day
  month = df[column].dt.month
  year = df[column].dt.year
  return day, month, year

# -----------SELECT COLUMN VALUES------------------
# def set_rules_create_new_column(df):
#     num_rules = st.number_input('Select the number of rules:', min_value=1, step=1)
#     column = st.selectbox('Choose the column to set rules on', df.columns)
#     if num_rules:
#         for i in range(num_rules):
#             selected_values = st.multiselect(f'Select values for rule {i + 1}', df[column].unique())
#             value = st.text_input(f'Enter the value for rule {i + 1}:')

#             if selected_values and value:
#                 df[f'{column}_rule_{i + 1}'] = df[column].apply(lambda x: value if x in selected_values else None)
#             else:
#                 st.error('Please specify the selected values and the value for the rule.')

#         st.write('New columns added with rules:', df.columns)
#         st.write('DataFrame with new columns:', df)
#     else:
#         st.error('Please specify the number of rules.')

# ---------SELECT COLUMN VALUES + CHECK CONTAINED VALUES------------------
def set_rules_create_new_column(df):
    num_rules = st.number_input('Select the number of rules:', min_value=1, step=1)
    column = st.selectbox('Choose the column to set rules on', df.columns)
    check_contains = st.checkbox('Check if values contain the input word')
    if num_rules:
        for i in range(num_rules):
            value = st.text_input(f'Enter the value for rule {i + 1}:')
            if check_contains:
                input_word = st.text_input(f'Enter the word to check in values for rule {i + 1}:')
            else:
                selected_values = st.multiselect(f'Select values for rule {i + 1}', df[column].unique())

            if value and (not check_contains or (check_contains and input_word)):
                if check_contains and input_word:
                    df[f'{column}_rule_{i + 1}'] = df[column].apply(lambda x: value if input_word in str(x) else None)
                else:
                    df[f'{column}_rule_{i + 1}'] = df[column].apply(lambda x: value if x in selected_values else None)
            else:
                st.error('Please specify the value for the rule.')

        st.write('New columns added with rules:', df.columns)
        st.write('DataFrame with new columns:', df)
    else:
        st.error('Please specify the number of rules.')


if selected == 'Analyze':
    UI()
    st.divider()

    process_type = st.sidebar.selectbox('What type of processing/analyzing data do you need ?', ('Add Brand column',
                                                                                                 'Add Market Classification column',
                                                                                                 'Add Validation column',
                                                                                                 'Check duplicated row(s)',
                                                                                                 'EDA',
                                                                                                 'Visualize the dataset',
                                                                                                 'Filter by requirements',
                                                                                                 'Add Excel row(s)',
                                                                                                 'Report Management',
                                                                                                 'Pivot Table',
                                                                                                 'Cohort Analysis',
                                                                                                 'RFM Analysis',
                                                                                                 'Add Rules column(s)'))

    if process_type == 'Filter by requirements':
        # Upload a file
        file_upload = st.file_uploader("Upload a file (XLSX or CSV)", type=["xlsx", "csv"])

        # Check if a file is uploaded
        if file_upload is not None:
            # Process the file and get the DataFrame
            df = process_file(file_upload)
            # Check if the DataFrame is not None
            if df is not None:
                # Clean and reconstruct selected columns
                string_columns = df.select_dtypes(include=['object']).columns.tolist()
                for col in df.columns:
                    if col in string_columns:
                        df[col] = df[col].apply(lambda x: re.sub(r'(\W)', r' \1 ', str(x)))
                # Display cleaned DataFrame
                st.write(df)

                # Adding value and exception words with DataFrame manipulation
                with st.expander(f'Filtering in details for choosed column'):
                    col = st.selectbox('Select column for filtering', string_columns,index=None,placeholder='...',key='filter_col')
                    if col:
                        df[col].fillna('', inplace=True)
                        value = st.text_input(f'What things do you need in {col} ?')
                        exceptions = st.text_input(f'Any exceptions with your things in {col} ? (comma-separated, e.g., no,none. Do not have -> type no/none)')  # multiple exceptions
                        exception_list = [e.strip() for e in exceptions.split(',') if e.strip()]
                        add_value_col = st.toggle(f'Add {value} as a new column?')

                        if (value or exceptions) or (value and exceptions):
                            if add_value_col:
                                if value and (exceptions is None or exception.lower() not in ['no', 'none'] for exception in exceptions):
                                    df['Product'] = ''
                                    df.loc[df[col].str.contains(value, case=False), 'Product'] = value
                                    # df['Product'] = df[col].apply(lambda x: value if re.search(value, x, re.IGNORECASE) else '')
                                    df_contain_value = df[df['Product'] == value]
                                    st.write(f'We have found: {df_contain_value.shape[0]} rows that fit your requirements!')
                                    adjust_column_position(df,'Product','Product')

                                else:
                                    st.error('Cannot handle condition: no specified value')
                            else:
                                if value:           # no exception
                                    df = df[df[col].str.contains(value, flags=re.IGNORECASE, regex=True)]
                                    st.write(f'We have found: {df.shape[0]} rows that fit your requirements!')
                                    st.write(df) 

                                elif exceptions:    # no value 
                                    for exception in exception_list:
                                        if exception.lower() not in ['no', 'none']:
                                            df = df[~df[col].str.contains(fr'\b{exception}\b', flags=re.IGNORECASE, regex=True)]
                                        else: 
                                            st.warning('Cannot handle condition: no value & no exception')
                                    st.write(f'We have found: {df.shape[0]} rows that fit your requirements!')
                                    st.write(df) 

                                elif value and exceptions:
                                    for exception in exception_list:
                                        if exception.lower() not in ['no', 'none']:
                                            df = df[(df[col].str.contains(value, flags=re.IGNORECASE, regex=True)) & (~df[col].str.contains(fr'\b{exception}\b', flags=re.IGNORECASE, regex=True))]
                                        else:
                                            df = df[df[col].str.contains(value, flags=re.IGNORECASE, regex=True)]
                                    st.write(f'We have found: {df.shape[0]} rows that fit your requirements!')
                                    st.write(df) 
                                else:
                                    st.warning('Cannot handle condition: no value & no exception')    
                                
                            download_as_xlsx(df)
                        else:
                            st.warning('Cannot handle condition: no choosed value and/or exceptions')             
                    else:
                        st.warning('Cannot handle condition: no choosed column')             


                with st.expander(f'Check our statistics with your dataframe'):
                    stats_col = st.selectbox('Select column for filtering', string_columns, index=None, placeholder='...', key='stats_col')
                    c1, c2 = st.columns(2, gap='medium')

                    if stats_col: 
                        with c1:
                            st.write('Check number of each value in column:', df[stats_col].value_counts())
                        with c2:
                            st.write('Check null value in column:', df[stats_col].value_counts().isnull().sum())
                            st.write('Check number of unique values in column:', df[stats_col].nunique())
                    else:
                        with c1:
                            st.write('Check null value in column:', df.isnull().sum())
                        with c2:
                            st.write('Check the statistics of the dataframe', df.describe())
                            st.write('Check the shape of the dataframe', df.shape)


                with st.expander('We plan to embed these common statistical commands below'):
                        statistics = '''
                        Some common commands for performing statistical analysis with a Pandas DataFrame:  
                        
                            Descriptive Statistics:

                            df.describe(): Provides summary statistics for numeric columns.
                            df.mean(): Computes the mean for each numeric column.
                            df.median(): Computes the median for each numeric column.
                            df.std(): Computes the standard deviation for each numeric column.
                            df.min(): Computes the minimum value for each numeric column.
                            df.max(): Computes the maximum value for each numeric column.
                            Frequency Counts:

                            df['column'].value_counts(): Counts the frequency of unique values in a specific column.
                            df.groupby('column')['another_column'].count(): Counts occurrences based on grouping.
                            Correlation and Covariance:

                            df.corr(): Computes the correlation matrix for all numeric columns.
                            df.cov(): Computes the covariance matrix for all numeric columns.
                            Filtering and Aggregation:

                            df[df['column'] > value]: Filters rows based on a condition.
                            df.groupby('column').agg({'other_column': 'mean'}): Aggregates data based on grouping.
                            Quantiles:

                            df.quantile(q=0.25): Computes the 25th percentile for numeric columns.
                            df.quantile(q=[0.25, 0.75]): Computes multiple quantiles.
                            Histograms and Plots:

                            df['column'].hist(): Generates a histogram for a specific column.
                            df.plot(kind='box'): Creates a box plot.
                            Skewness and Kurtosis:

                            df.skew(): Computes the skewness of numeric columns.
                            df.kurtosis(): Computes the kurtosis of numeric columns.
                            Sampling:

                            df.sample(n=5): Randomly samples n rows from the DataFrame.
                            df.sample(frac=0.25): Randomly samples a fraction of rows.
                            Correlation Heatmap:

                            You can use libraries like Seaborn to create correlation heatmaps.
                            Cross-tabulation:

                            pd.crosstab(df['column1'], df['column2']): Generates a cross-tabulation table.
                            Missing Data:

                            df.isnull(): Checks for missing values in the DataFrame.
                            df.dropna(): Removes rows with missing values.
                            df.fillna(value): Fills missing values with a specified value.
                            Percentile Rank:

                            df.rank(pct=True): Computes the percentile rank of values.
                            Resampling (for Time Series Data):

                            df.resample('D').sum(): Resamples time series data at daily frequency and aggregates it.'''
                        st.markdown(statistics)


    if process_type == 'Visualize the dataset':
        st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)
        fl = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])
        if fl is not None:
            filename = fl.name
            st.write(filename)
            
            # Check the file type and read accordingly
            if filename.endswith('.csv') or filename.endswith('.txt'):
                df = pd.read_csv(fl, encoding="utf-8", delimiter=',')  # Modify delimiter if needed
            elif filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(fl)  # No need to specify encoding for Excel files
        else:
            os.chdir(r"/Users/vuhainam/Documents/PROJECT_DA/BFC/ProcessData/FullProcess")
            df = pd.read_excel("Fruit.xlsx")  # No need to specify encoding for Excel files

        col1, col2 = st.columns((2))
        df["Date"] = pd.to_datetime(df["Date"])

        # Getting the min and max date 
        startDate = pd.to_datetime(df["Date"]).min()
        endDate = pd.to_datetime(df["Date"]).max()

        with col1:
            date1 = pd.to_datetime(st.date_input("Start Date", startDate))

        with col2:
            date2 = pd.to_datetime(st.date_input("End Date", endDate))

        df = df[(df["Date"] >= date1) & (df["Date"] <= date2)].copy()

        st.sidebar.header("Choose your filter: ")
        # Filter as 'Nước nhập'
        import_country = st.sidebar.multiselect("Pick your Country", df["Nước_nhập"].unique())
        if not import_country:
            df2 = df.copy()
        else:
            df2 = df[df["Nước_nhập"].isin(import_country)]

        # Filter as 'Nhà cung cấp'
        exporter = st.sidebar.multiselect("Pick the Exporter", df2["Nhà_cung_cấp"].unique())
        if not exporter:
            df3 = df2.copy()
        else:
            df3 = df2[df2["Nhà_cung_cấp"].isin(exporter)]

        # Filter as 'Loại xuất'
        type_export = st.sidebar.multiselect("Pick the Type",df3["Loại"].unique())


        # Filter the data based on Import Country, Exporter and Export Type
        if not import_country and not exporter and not type_export:
            filtered_df = df
        elif not import_country and not exporter:
            filtered_df = df[df["Loại"].isin(type_export)]
        elif not exporter and not type_export:
            filtered_df = df[df["Nước_nhập"].isin(import_country)]
        elif import_country and exporter:
            filtered_df = df3[df["Nhà_cung_cấp"].isin(exporter) & df3["Nước_nhập"].isin(import_country)]
        elif import_country and type_export:
            filtered_df = df3[df["Nước_nhập"].isin(import_country) & df3["Loại"].isin(type_export)]
        elif exporter and type_export:
            filtered_df = df3[df["Nhà_cung_cấp"].isin(exporter) & df3["Loại"].isin(type_export)]
        elif exporter:
            filtered_df = df3[df3["Nhà_cung_cấp"].isin(exporter)]
        else:
            filtered_df = df3[df3["Nhà_cung_cấp"].isin(exporter) & df3["Nước_nhập"].isin(import_country) & df3["Loại"].isin(type_export)]

        product = filtered_df.groupby(by = ["Product"], as_index = False)["Thành_tiền"].sum()

        with col1:
            st.subheader("Sales by Product")
            fig = px.bar(product, x = "Product", y = "Thành_tiền", text = ['${:,.2f}'.format(x) for x in product["Thành_tiền"]],
                        template = "seaborn")
            st.plotly_chart(fig,use_container_width=True, height = 200)

        # HECTOR ADD
        # Add a slider to allow the user to select the top N HS codes
        n_hscode = st.slider("Select Top HS Codes", 1, len(filtered_df['HScode'].unique()), 3)
        # Filter the DataFrame to select the top N HS codes
        top_hscode = filtered_df[filtered_df['HScode'].isin(filtered_df['HScode'].unique()[:n_hscode])]

        # EXPLAIN CODE
        # filtered_df['HScode'].unique()[:n_hscode] = array of HSCODE
        # filtered_df['HScode'].isin(filtered_df['HScode'].unique()[:n_hscode]) = series with boolean values (true->get,false->skip)
        # filtered_df[filtered_df['HScode'].isin(filtered_df['HScode'].unique()[:n_hscode])] = dataframe with a filtered condition

        with col2:
            st.subheader("Sales by HScode")
            fig = px.pie(top_hscode, values="Thành_tiền", names="HScode", hole=0.5)
            fig.update_traces(text=top_hscode["HScode"], textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        cl1, cl2 = st.columns((2))
        with cl1:
            with st.expander("View Product Data"):
                st.write(product.style.background_gradient(cmap="Blues"))
                csv = product.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data", data = csv, file_name = "Product.csv", mime = "text/csv",
                                    help = 'Click here to download the data as a CSV file')

        with cl2:
            with st.expander("View Country-HScode Data"):
                country = filtered_df.groupby(by = ["Nước_nhập",'HScode'], as_index = False)["Thành_tiền"].sum()
                st.write(country.style.background_gradient(cmap="Oranges"))
                csv = country.to_csv(index = False).encode('utf-8')
                st.download_button("Download Data", data = csv, file_name = "Country-HScode.csv", mime = "text/csv",
                                help = 'Click here to download the data as a CSV file')
                
        filtered_df["month_year"] = filtered_df["Date"].dt.to_period("M")
        st.subheader('Time Series Analysis')

        linechart = pd.DataFrame(filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y : %b"))["Thành_tiền"].sum()).reset_index()
        fig2 = px.line(linechart, x = "month_year", y="Thành_tiền", labels = {"Thành_tiền": "Amount"},height=500, width = 1000,template="gridon")
        st.plotly_chart(fig2,use_container_width=True)

        with st.expander("View TimeSeries Data"):
            st.write(linechart.T.style.background_gradient(cmap="Blues"))
            csv = linechart.to_csv(index=False).encode("utf-8")
            st.download_button('Download Data', data = csv, file_name = "TimeSeries.csv", mime ='text/csv')

        # Create a treem based on Region, category, sub-Category
        st.subheader("Hierarchical view of Product using TreeMap")
        filtered_df = filtered_df.dropna(subset=["Product", "PhânLoại", "Nước_nhập"])
        fig3 = px.treemap(filtered_df, path = ["Product","PhânLoại","Nước_nhập"], values = "Thành_tiền",hover_data = ["Thành_tiền"],
                        color = "Nước_nhập")
        fig3.update_layout(width = 800, height = 650)
        st.plotly_chart(fig3, use_container_width=True)

        chart1, chart2 = st.columns((2))
        with chart1:
            st.subheader('Sales by Export Type')
            fig = px.pie(filtered_df, values = "Thành_tiền", names = "Loại", template = "plotly_dark")
            fig.update_traces(text = filtered_df["Loại"], textposition = "inside")
            st.plotly_chart(fig,use_container_width=True)

        with chart2:
            st.subheader('Sales by Product')
            fig = px.pie(filtered_df, values = "Thành_tiền", names = "Product", template = "gridon")
            fig.update_traces(text = filtered_df["Product"], textposition = "inside")
            st.plotly_chart(fig,use_container_width=True)

        import plotly.figure_factory as ff
        with st.expander(":point_right: Summary :point_left:"):
            st.markdown("Correlation between key features")
            df_sample = df[0:5][["Nước_nhập","Nhà_cung_cấp","Product","PhânLoại","Số_lượng","Đơn_vị","Thành_tiền","Tiền_tệ"]]
            fig = ff.create_table(df_sample, colorscale = "Cividis")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("Monthly sales of product")
            filtered_df["month"] = filtered_df["Date"].dt.month_name()
            sub_category_Year = pd.pivot_table(data = filtered_df, values = "Thành_tiền", index = ["PhânLoại"],columns = "month")
            st.write(sub_category_Year.style.background_gradient(cmap="Blues"))

        # Create a scatter plot
        data1 = px.scatter(filtered_df, x = "Đơn_giá", y = "Thành_tiền", size = "Số_lượng")
        data1['layout'].update(title="Relationship between Hoá_đơn and Số_lượng using Scatter Plot.",
                            titlefont = dict(size=20),xaxis = dict(title="Hoá_đơn",titlefont=dict(size=19)),
                            yaxis = dict(title = "Số_lượng", titlefont = dict(size=19)))
        st.plotly_chart(data1,use_container_width=True)

        with st.expander("View Data"):
            st.write(filtered_df.iloc[:500,1:20:2].style.background_gradient(cmap="Oranges"))

        # Download orginal DataSet
        csv = df.to_csv(index = False).encode('utf-8')
        st.download_button('Download Data', data = csv, file_name = "Data.csv",mime = "text/csv")


    if process_type == 'EDA':
        # Upload a file
        file_upload = st.file_uploader("Upload a file (XLSX or CSV)", type=["xlsx", "csv"])
        # Check if a file is uploaded
        if file_upload is not None:
        # Process the file and get the DataFrame
            df = process_file(file_upload)
            # Check if the DataFrame is not None
            if df is not None:
                c1,c2 = st.columns(2,gap='medium')
                if c1.checkbox("Show Shape", key="show_shape"):
                    c1.write(df.shape)
                if c1.checkbox("Show Columns data types", key="show_datatype"):
                    c1.write(df.dtypes)
                if c1.checkbox("Show Columns", key='show_columns'):
                    c1.write(df.columns)
                if c2.checkbox("Summary", key='show_summary'):
                    c2.write(df.describe())
                if c2.checkbox("Show Selected Columns", key='show_selected_column'):
                    selected_columns = c2.multiselect("Select Columns", df.columns)
                    new_df = df[selected_columns]
                    c2.dataframe(new_df)
                if c2.checkbox("Show Value Counts", key='show_value_count'):
                    c2.write(df.iloc[:, -1].value_counts())


    if process_type == 'Check duplicated row(s)':
        # Upload a file
        file_upload = st.file_uploader("Upload a file (XLSX or CSV)", type=["xlsx", "csv"])
        # Check if a file is uploaded
        if file_upload is not None:
        # Process the file and get the DataFrame
            df = process_file(file_upload)
            # Check if the DataFrame is not None
            if df is not None:
                df_no_duplicates = check_and_remove_duplicates(df)
                if df_no_duplicates is not None:
                    download_as_xlsx(df_no_duplicates)
                else:
                    st.warning('Please fill out the requirements above')


    if process_type == 'Add Market Classification column':
        # Upload DIM
        dim_file = st.file_uploader("Upload DIM database/table", type=["xlsx", "csv"])
        # Check if a file is uploaded
        if dim_file is not None:
        # Process the file and get the DataFrame
            dim_df = process_DIM_file(dim_file)
            # Check if the DataFrame is not None
            if dim_df is not None:
                # Upload FACT
                fact_file = st.file_uploader("Upload FACT database/table", type=["xlsx", "csv"])
                # Check if a file is uploaded
                if fact_file is not None:
                # Process the file and get the DataFrame
                    fact_df = process_file(fact_file)
                    # Check if the DataFrame is not None
                    if fact_df is not None: 
                        show_dim_fact(dim_df,fact_df)

                        dim_cols = st.multiselect('Select DIM columns for joining', dim_df.columns) 
                        fact_cols = st.multiselect('Select FACT columns for joining', fact_df.columns) 
                        all_columns = st.toggle('Select all columns ?')                            
                        how_choices = ['left','right','inner','outer','cross']
                        how_merge = st.selectbox('How methods:',how_choices,key='how',index=None,placeholder='Method to merge...')
                        on_merge = st.selectbox('Merging on column:',dim_cols,key='on',index=None,placeholder='Merge on column...')

                        if on_merge and how_merge:
                            if all_columns is None:

                                # if isinstance(fact_cols, pd.DataFrame) and on_merge in fact_cols.columns:  # Check if fact_cols is a dataframe -> IS NOT
                                sub_fact_df = fact_df[fact_cols]          # Create a DataFrame from selected columns in fact_df
                                # sub_fact_df = pd.DataFrame(fact_cols)   # Converts the list of column names to a DataFrame where the column names become rows in the DataFrame                                 
                                if on_merge in sub_fact_df.columns:                                             
                                    if how_merge == 'cross':
                                        # fact_merge = pd.merge(fact_df, dim_df[dim_cols],on=f'{on_merge}',how=f'{how_merge}')
                                        fact_merge = pd.merge(fact_df, dim_df, how=how_merge)

                                        with st.expander('Position'):
                                            adjust_column_position(fact_merge, 'MarketClassification', 'Cross_MarketClassification')
                                        with st.expander('Check column value'):
                                            st.write(show_info_column(fact_merge))
                                            '''
                                            The 'None' value is displayed because the function show_info_column does not have a return statement. 
                                            When a function in Python does not explicitly return anything, it implicitly returns None.
                                            '''
                                        download_as_xlsx(fact_merge)
                                        
                                    else:
                                        # fact_merge = pd.merge(fact_df, dim_df[dim_cols],on=f'{on_merge}',how=f'{how_merge}')
                                        fact_merge = pd.merge(fact_df, dim_df, on=on_merge, how=how_merge)

                                        with st.expander('Position'):
                                            adjust_column_position(fact_merge, 'MarketClassification', f'{how_merge}_MarketClassification')
                                        with st.expander('Check column value'):
                                            show_info_column(fact_merge)        # NO MORE 'NONE' DISPLAYING

                                        download_as_xlsx(fact_merge)
                                else: 
                                    st.warning('There is no column matching between DIM and FACT!')

                            else:                       
                                if on_merge in fact_df.columns:                                             
                                    if how_merge == 'cross':
                                        fact_merge = pd.merge(fact_df, dim_df, how=how_merge)

                                        with st.expander('Position'):
                                            adjust_column_position(fact_merge, 'MarketClassification', 'Cross_MarketClassification')
                                        with st.expander('Check column value'):
                                            show_info_column(fact_merge)

                                        download_as_xlsx(fact_merge)
                                    else:
                                        fact_merge = pd.merge(fact_df, dim_df, on=on_merge, how=how_merge)

                                        with st.expander('Position'):
                                            adjust_column_position(fact_merge, 'MarketClassification', f'{how_merge}_MarketClassification')
                                        with st.expander('Check column value'):
                                            show_info_column(fact_merge)

                                        download_as_xlsx(fact_merge)
                                else: 
                                    st.warning('There is no column matching between DIM and FACT!')

                        else:
                            st.info('Please specify parameters for merging process.')



    if process_type == 'Add Brand column':
        # Upload a file
        file_upload = st.file_uploader("Upload a file (XLSX or CSV)", type=["xlsx", "csv"])
        # Check if a file is uploaded
        if file_upload is not None:
        # Process the file and get the DataFrame
            df = process_file(file_upload)
            # Check if the DataFrame is not None
            if df is not None:
                st.write('Your uploaded dataframe:',df)

                numerical_cols = df.select_dtypes(include=['int64','float']).columns.tolist()
                categorical_cols = list(set(df.columns) - set(numerical_cols))
                description_col = st.selectbox('Please specify the description column:',categorical_cols,index=None,placeholder='...')

                st.markdown(
                    '''
                    :red[Some commonly key words:] <b> nha sx, nhà sản xuất, nhà sx, nsx, nha cung cap, nhà cung cấp, ncc, brand, hiệu, hieu, manufacturer, manufacturers, producer, publisher, hang, hang sx, hsx, hãng sx, hãng sản xuất, hang san xuat </b>

                    :blue[Some commonly exception words:] <i> tháng, month, months, hsd, new, january, february, march, april, may, june, july, august, september, october, november, december,
                    jan, feb, mar, jun, jul, aug, sep, oct, nov, dec </i>
                    '''
                ,unsafe_allow_html=True)

                keyword = st.text_input(f'Any keywords with the brands in {description_col} ? (comma-separated, e.g., manufacturer,nsx,...)')  # multiple keywords
                keyword_list = [e.strip() for e in keyword.split(',') if e.strip()]

                specified = st.text_input(f'Any exceptions with the brands in {description_col} ? (comma-separated, e.g., no,none. Do not have -> type no/none)')  # multiple exceptions
                specified_list = [e.strip() for e in specified.split(',') if e.strip()]

                if keyword_list and specified_list:
                    for word in specified_list:
                        if word.lower() in ['no', 'none']:
                            result_df = extract_words_after_keyword(df, 'Mô_tả_sản_phẩm', keyword_list, specified_list)
                            st.write('Dataframe with Brand column (having keyword but no exception)', result_df)
                            brand_null = result_df[result_df['Brand'].isnull()].shape[0]
                            st.write(f'Number of brands found are: {result_df.shape[0] - brand_null} out of {result_df.shape[0]} rows')

                            # index_brand_col = st.slider(f'Select the position of "Brand" column', 0, len(result_df.columns))
                            # old_brand_col = result_df.pop('Brand')
                            # result_df.insert(index_brand_col, 'Brand', old_brand_col)
                            # st.write('Dataframe with new position of Brand column (having keyword but no exception)',result_df)
                            with st.expander('Having keyword but no exception'):
                                adjust_column_position(result_df, 'Brand', 'Brand')
                            with st.expander('Check column value'):
                                show_info_column(result_df)

                            download_as_xlsx(result_df)
                            break

                        else:
                            result_df = extract_words_after_keyword(df, 'Mô_tả_sản_phẩm', keyword_list, specified_list)
                            st.write('Dataframe with Brand column (having both keyword and exception)',result_df)
                            brand_null = result_df[result_df['Brand'].isnull()].shape[0]
                            st.write(f'Number of brands found are: {result_df.shape[0] - brand_null} out of {result_df.shape[0]} rows')

                            with st.expander('Having both keyword and exception'):
                                adjust_column_position(result_df, 'Brand', 'Brand')
                            with st.expander('Check column value'):
                                show_info_column(result_df)

                            download_as_xlsx(result_df)
                            break

                elif keyword_list:
                    st.info('Please specify an exception')
                else:
                    st.warning('Please specify a keyword')



    if process_type == 'Add Validation column':
        # Upload a file
        file_upload = st.file_uploader("Upload a file (XLSX or CSV)", type=["xlsx", "csv"])

        # Check if a file is uploaded
        if file_upload is not None:
                # Process the file and get the DataFrame
                df = process_file(file_upload)
                # Check if the DataFrame is not None
                if df is not None:
                    # Clean and reconstruct selected columns
                    string_columns = df.select_dtypes(include=['object']).columns.tolist()
                    for col in df.columns:
                        if col in string_columns:
                            df[col] = df[col].apply(lambda x: re.sub(r'(\W)', r' \1 ', str(x)))
                    # Display cleaned DataFrame
                    st.write('Original dataframe',df)         

                    # Adding necessary and exception words with DataFrame manipulation
                    with st.expander('Add Yes/No validation'):
                        # Select a column for filtering
                        cate_cols = st.selectbox('Select categorical column for filtering', string_columns) 

                        yesno = st.text_input(f'Not a valid {cate_cols} row ? (comma-separated)')  # multiple exceptions
                        yesno_list = [e.strip() for e in yesno.split(',') if e.strip()]

                        # Check if the selected column exists in the DataFrame
                        if cate_cols in df.columns:
                            df[cate_cols].fillna('', inplace=True)
                            df = create_validation_column(df, cate_cols, yesno_list)
                            no = df[df['Validation'] == 'No']
                            st.write(f'{no.shape[0]} values are found with the provided words')
                            adjust_column_position(df,'Validation','Validation')
                            show_info_column(df)

                    download_as_xlsx(df)


   
