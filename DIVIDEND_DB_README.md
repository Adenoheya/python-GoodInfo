# 股票股利資料庫管理工具

## 概述
這個工具集用於管理和查詢股票的股利資訊。它包含兩個主要模組：
1. **dividend_db.py** - 建立資料庫並從 HTML 檔案匯入股利資料（**自動從檔案名稱提取股票代號**）
2. **query_dividend.py** - 查詢和分析股利資料

## ✨ 新增功能

### 自動股票代號提取
- 程式現在從 XLS 檔案名稱自動提取股票代號（4位數字）
- 支援多種檔案名稱格式：
  - `2881.xls`
  - `2881_DividendSchedule.xls`
  - `DividendSchedule_2881.xls`
- 如果無法提取股票代號，程式會顯示錯誤訊息並停止執行

## 資料庫結構

### dividend_schedule 表

| 欄位名稱 | 資料型態 | 說明 |
|---------|---------|------|
| id | INTEGER | 主鍵，自動遞增 |
| dividend_distribution_period | TEXT | 股利發放期間 |
| dividend_belonging_period | TEXT | 股利所屬期間 |
| ex_dividend_date | TEXT | 除息交易日 |
| cash_dividend | REAL | 現金股利（元/股） |
| ex_rights_date | TEXT | 除權交易日 |
| stock_dividend | REAL | 股票股利（股/股） |
| created_at | TIMESTAMP | 建立時間 |
| updated_at | TIMESTAMP | 更新時間 |

## 使用方法

### 1. 建立/更新資料庫

```bash
python3 dividend_db.py
```

**功能：**
- 建立 SQLite 資料庫（dividend.db）
- 清除舊資料
- 從 DividendSchedule.xls 讀取資料
- 將資料寫入資料庫

**輸出範例：**
```
====================================================================================================
股票股利資料庫管理工具
====================================================================================================

✓ 從檔案名稱中提取股票代號: 2881
✓ 資料庫 '2881.db' 已建立
正在處理股票代號: 2881
✓ 已清除舊資料
正在讀取 2881_DividendSchedule.xls...
找到 27 行資料
✓ 成功插入 24 筆資料
```

**錯誤範例（檔案名稱不包含股票代號）：**
```
✗ 錯誤：無法從檔案名稱中提取股票代號
  檔案名稱: DividendSchedule.xls
  檔案名稱格式應包含 4 位數字的股票代號（例如：2881.xls）
```

### 2. 查詢股利資料

```bash
python3 query_dividend.py
```

**功能：**
- 顯示所有股利資料
- 查詢特定股票的股利資料
- 提供統計資訊（總額、平均值、最大值、最小值）

## 程式碼範例

### 在 Python 中使用查詢函數

```python
from query_dividend import query_by_stock, get_statistics

# 查詢特定股票的股利資料
stock_data = query_by_stock('2881')
for row in stock_data:
    print(row)

# 取得統計資訊
stats = get_statistics('2881')
total, cash_sum, cash_avg, stock_sum, stock_avg, max_cash, min_cash = stats
print(f"現金股利總額: {cash_sum}")
print(f"現金股利平均: {cash_avg}")
```

## 主要特性

✓ **SQLite 資料庫** - 輕量級且易於備份
✓ **HTML 解析** - 直接從網頁格式匯入資料
✓ **靈活查詢** - 支援多種查詢方式
✓ **統計分析** - 提供股利統計資訊
✓ **美化輸出** - 使用 tabulate 提供清晰的表格輸出

## 依賴套件

- beautifulsoup4 - HTML 解析
- tabulate - 表格顯示
- sqlite3 - 資料庫（Python 標準庫）

## 安裝依賴

```bash
pip install beautifulsoup4 tabulate
```

## 檔案列表

- `dividend_db.py` - 資料庫建立和資料匯入模組（自動提取股票代號）
- `query_dividend.py` - 資料查詢和分析模組
- `2881.db` - SQLite 資料庫檔案（名稱根據股票代號）
- `2881_DividendSchedule.xls` - 原始股利資料（HTML 格式）

## 說明

### dividend_db.py 主要函數

| 函數名稱 | 說明 |
|---------|------|
| extract_stock_id_from_filename(filename) | 從檔案名稱提取股票代號 |
| create_database(stock_id) | 建立資料庫和表 |
| parse_html_table(html_file) | 解析 HTML 檔案中的股利資料 |
| insert_dividend_data(cursor, conn, data) | 將資料插入資料庫 |
| query_dividend_data(cursor) | 查詢資料 |
| display_dividend_data(rows) | 美化顯示資料 |

### query_dividend.py 主要函數

| 函數名稱 | 說明 |
|---------|------|
| get_connection() | 取得資料庫連線 |
| query_by_stock(stock_id) | 查詢特定股票 |
| query_all() | 查詢所有資料 |
| get_statistics(stock_id) | 取得統計資訊 |
| display_table(rows, headers=None) | 美化顯示表格 |

## 注意事項

1. 資料來源檔案必須在檔案名稱中包含 4 位數字的股票代號（例如：`2881_DividendSchedule.xls`）
2. XLS 檔案實際上是 HTML 格式
3. 首次運行 `dividend_db.py` 時會自動建立資料庫
4. 資料庫名稱會根據提取的股票代號命名（例如：`2881.db`）
5. 若檔案名稱無法提取股票代號，程式會顯示錯誤並終止
6. 日期格式保持原始格式（例如 '25/07/01）

## 常見問題

### Q: 如何新增其他股票資料？
A: 將 XLS 檔案重新命名，在檔案名稱中包含股票代號。例如：`1234_DividendSchedule.xls`，然後修改 `dividend_db.py` 中的 `HTML_FILE` 變數，最後重新運行程式。

### Q: 如何清除資料庫？
A: 刪除對應的資料庫檔案（例如 `2881.db`），然後重新運行 `dividend_db.py`。

### Q: 檔案名稱中有多個 4 位數字怎麼辦？
A: 程式會提取第一個找到的 4 位數字作為股票代號。建議使用 `2881_DividendSchedule.xls` 格式，將股票代號放在前面。

### Q: 如何自訂查詢？
A: 修改 `query_dividend.py` 中的查詢 SQL，或直接使用提供的函數在您的代碼中進行查詢。

## 版本
- 版本 1.1 - 新增自動股票代號提取功能
- 版本 1.0 - 初始版本
- 最後更新：2025年12月6日
