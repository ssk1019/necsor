# coding=UTF-8
import pandas as pd
import requests
import io


def scrape_and_merge_stock_data(urls):
    """
    從給定的 URL 列表中爬取表格資料，並根據股票代號合併它們。

    Args:
        urls (list): 包含目標網頁 URL 的列表。

    Returns:
        pandas.DataFrame: 一個包含所有合併後資料的 DataFrame。
    """
    all_dataframes = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print("開始爬取資料...")
    for i, url in enumerate(urls):
        try:
            print(f"正在處理第 {i + 1}/{len(urls)} 個網址: {url}")
            # 1. 發送網路請求取得網頁內容
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 如果請求失敗 (e.g., 404, 500)，會拋出例外

            # 2. 使用 pandas 直接讀取網頁上的表格
            # pandas.read_html 會回傳一個包含所有表格的 list of DataFrame
            # 我們要找的是 id='example' 的那個表格
            # 使用 io.StringIO 是為了讓 pandas 能正確處理 response.text 的編碼
            tables = pd.read_html(io.StringIO(response.text), attrs={'id': 'example'})

            if tables:
                # 將第一欄的欄位名稱統一設為 '股票代號'，方便後續合併
                df = tables[0]
                df.rename(columns={df.columns[0]: '股票代號'}, inplace=True)
                all_dataframes.append(df)
            else:
                print(f"警告：在 {url} 中找不到 id='example' 的表格。")

        except requests.exceptions.RequestException as e:
            print(f"錯誤：無法取得網址 {url} 的內容。錯誤訊息: {e}")
        except Exception as e:
            print(f"處理 {url} 時發生未預期的錯誤: {e}")

    if not all_dataframes:
        print("沒有成功爬取到任何資料。")
        return pd.DataFrame()

    print("\n資料爬取完成，開始進行合併...")
    # 3. 合併所有從各網頁抓下來的 DataFrame
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    # 4. 根據 '股票代號' 進行分組，並將同代號的資料合併
    #    - groupby('股票代號') 將相同股票代號的資料列分在同一組
    #    - .first() 會保留每一欄位在該組中第一個出現的非空值
    #      這完美符合您的需求：將不同頁面的欄位資訊合併到同一筆股票資料中
    merged_df = combined_df.groupby('股票代號').first()

    # ==================== 新增的程式碼區塊開始 ====================
    # 根據您的需求，重新排列欄位順序
    print("重新排列欄位順序...")
    try:
        # 定義要移到最前面的欄位列表 (股票代號是 index，會自動放在第一位)
        front_columns = [
            '公司', '股價', '資本額(億)', '產業類型', '發行市場', '成交量', '本益比',
            '2年平均本益比', '4年平均本益比', '6年平均本益比', '9年平均本益比',
            '股價淨值比', '(月)累積營收年增率(%)', '(月-1)累積營收年增率(%)',
            '(月-2)累積營收年增率(%)'
        ]

        # 取得所有現存的欄位
        all_columns = merged_df.columns.tolist()

        # 篩選出剩餘的欄位 (從 all_columns 中移除 front_columns)
        remaining_columns = [col for col in all_columns if col not in front_columns]

        # 組成新的欄位順序
        new_column_order = front_columns + remaining_columns

        # 重新索引 DataFrame
        merged_df = merged_df[new_column_order]
        print("欄位順序排列完成。")
    except Exception as e:
        print(f"警告：欄位重排時發生未預期的錯誤: {e}。將使用原始順序。")
    # ==================== 新增的程式碼區塊結束 ====================

    print("資料合併完成！")
    return merged_df


if __name__ == '__main__':
    list_urls = [
        'https://stock.wespai.com/p/42327',
        'https://stock.wespai.com/p/42307',
        'https://stock.wespai.com/p/42302',
        'https://stock.wespai.com/p/42305',
        'https://stock.wespai.com/p/42177',
        'https://stock.wespai.com/p/42179',
    ]

    final_data = scrape_and_merge_stock_data(list_urls)

    if not final_data.empty:
        # ==================== 新增功能：產生超連結 ====================
        # 1. 將 '股票代號' 從 index 變回一般的欄位
        #    因為 groupby 操作後，'股票代號' 會變成 DataFrame 的索引 (index)
        final_data.reset_index(inplace=True)

        # 2. 定義超連結的基礎 URL 格式
        base_url = "https://www.wantgoo.com/stock/{}/technical-chart"

        # 3. 使用 .apply() 和 lambda 函式，將 '股票代號' 欄位中的每個代號轉換成超連結公式
        #    =HYPERLINK("網址", "顯示的文字") 是試算表軟體的公式
        final_data['股票代號'] = final_data['股票代號'].apply(
            lambda ticker: f'=HYPERLINK("{base_url.format(ticker)}", "{ticker}")'
        )
        # ============================================================

        # 5. 將最終結果儲存為 CSV 檔案
        output_filename = 'merged_stock_data.csv'
        # 使用 encoding='utf-8-sig' 確保 Excel 開啟 CSV 檔時不會有中文亂碼問題
        final_data.to_csv(output_filename, encoding='utf-8-sig', index=False) # 加上 index=False 避免多出一欄索引

        print(f"\n成功將合併後的資料儲存至 {output_filename}")
        print("\n最終資料預覽 (股票代號欄位已包含超連結公式)：")
        print(final_data.head())