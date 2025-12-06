import sqlite3
from bs4 import BeautifulSoup
import os
from datetime import datetime
import re

# --- 設定參數 ---
HTML_FILE = '2881_DividendSchedule.xls'  # HTML檔案名稱
DATABASE_DIR = 'database'  # 資料庫目錄

# Convert to absolute path for better WSL/Windows interop
DATABASE_DIR = os.path.abspath(DATABASE_DIR)

# 確保資料庫目錄存在
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

def extract_stock_id_from_filename(filename):
    """從檔案名稱中提取股票代號"""
    # 移除副檔名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 嘗試提取數字序列（4位數的股票代號）
    # 可能的格式: 2881.xls, 2881_DividendSchedule.xls, DividendSchedule_2881.xls 等
    match = re.search(r'(\d{4})', name_without_ext)
    
    if match:
        stock_id = match.group(1)
        return stock_id
    else:
        return None

def create_database(stock_id):
    """建立股利資料庫"""
    db_name = f'{stock_id}.db'  # 資料庫名稱根據股票代號命名
    db_path = os.path.join(DATABASE_DIR, db_name)  # 完整路徑
    
    # Use autocommit mode (isolation_level=None) and timeout to handle locks
    conn = sqlite3.connect(db_path, timeout=10.0, check_same_thread=False, isolation_level=None)
    cursor = conn.cursor()
    
    # 建立股利資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dividend_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dividend_distribution_period TEXT,      -- 股利發放期間
            dividend_belonging_period TEXT,         -- 股利所屬期間
            ex_dividend_date TEXT,                  -- 除息交易日
            cash_dividend REAL,                     -- 現金股利
            ex_rights_date TEXT,                    -- 除權交易日
            stock_dividend REAL,                    -- 股票股利
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print(f"✓ 資料庫 'database/{stock_id}.db' 已建立")
    return conn, cursor, db_path

def parse_html_table(html_file):
    """從 HTML 檔案解析表格資料"""
    if not os.path.exists(html_file):
        print(f"✗ 檔案不存在: {html_file}")
        return []
    
    print(f"正在讀取 {html_file}...")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 找到資料表
        table = soup.find('table', {'id': 'tblDetail'})
        if not table:
            print("✗ 找不到資料表")
            return []
        
        # 取得所有行
        rows = table.find_all('tr')
        print(f"找到 {len(rows)} 行資料")
        
        data = []
        # 跳過前3行表頭，從第4行開始讀取
        for row in rows[3:]:
            cells = row.find_all('td')
            if len(cells) < 18:
                continue
            
            try:
                # 提取需要的資料
                # 股票股利欄位：盈餘(cells[15]) + 公積(cells[16]) 或直接取合計(cells[17])
                stock_div_surplus = float(cells[15].get_text(strip=True)) if cells[15].get_text(strip=True) else 0
                stock_div_capital = float(cells[16].get_text(strip=True)) if cells[16].get_text(strip=True) else 0
                stock_div_total = float(cells[17].get_text(strip=True)) if cells[17].get_text(strip=True) else 0
                
                row_data = {
                    'dividend_distribution_period': cells[0].get_text(strip=True),  # 股利發放期間
                    'dividend_belonging_period': cells[1].get_text(strip=True),     # 股利所屬期間
                    'ex_dividend_date': cells[3].get_text(strip=True),              # 除息交易日
                    'cash_dividend': float(cells[12].get_text(strip=True)) if cells[12].get_text(strip=True) else 0,  # 現金股利
                    'ex_rights_date': cells[8].get_text(strip=True),                # 除權交易日
                    'stock_dividend': stock_div_total,  # 股票股利合計
                }
                data.append(row_data)
            except (ValueError, IndexError) as e:
                print(f"⚠ 跳過無效行: {e}")
                continue
        
        return data
    
    except Exception as e:
        print(f"✗ 解析 HTML 時出錯: {e}")
        return []

def get_existing_data(cursor):
    """從資料庫取得所有現存的股利資料"""
    cursor.execute('''
        SELECT dividend_distribution_period, dividend_belonging_period,
               ex_dividend_date, cash_dividend, ex_rights_date, stock_dividend
        FROM dividend_schedule
    ''')
    
    # 轉換為字典格式，以發放期間為鍵
    existing_data = {}
    for row in cursor.fetchall():
        dist_period, belong_period, ex_div_date, cash_div, ex_right_date, stock_div = row
        existing_data[dist_period] = {
            'dividend_belonging_period': belong_period,
            'ex_dividend_date': ex_div_date,
            'cash_dividend': cash_div,
            'ex_rights_date': ex_right_date,
            'stock_dividend': stock_div
        }
    
    return existing_data

def check_data_conflict(xls_data, db_data):
    """檢查 XLS 與資料庫中重複的資料是否一致
    
    返回: (new_records, conflict_records)
    - new_records: 資料庫中不存在的新資料
    - conflict_records: 發放期間相同但資料不一致的記錄
    """
    new_records = []
    conflict_records = []
    
    for xls_row in xls_data:
        dist_period = xls_row['dividend_distribution_period']
        
        if dist_period not in db_data:
            # 新資料
            new_records.append(xls_row)
        else:
            # 檢查是否一致
            db_row = db_data[dist_period]
            is_conflict = (
                xls_row['dividend_belonging_period'] != db_row['dividend_belonging_period'] or
                xls_row['ex_dividend_date'] != db_row['ex_dividend_date'] or
                xls_row['cash_dividend'] != db_row['cash_dividend'] or
                xls_row['ex_rights_date'] != db_row['ex_rights_date'] or
                xls_row['stock_dividend'] != db_row['stock_dividend']
            )
            
            if is_conflict:
                conflict_records.append({
                    'distribution_period': dist_period,
                    'xls_data': xls_row,
                    'db_data': db_row
                })
    
    return new_records, conflict_records

def display_conflicts(conflict_records):
    """顯示衝突資料"""
    if not conflict_records:
        return
    
    print("\n" + "⚠" * 50)
    print("⚠ 警告：發現資料不一致 (XLS 與資料庫內容不符)")
    print("⚠" * 50)
    
    for conflict in conflict_records:
        dist_period = conflict['distribution_period']
        xls = conflict['xls_data']
        db = conflict['db_data']
        
        print(f"\n📌 發放期間: {dist_period}")
        print("-" * 100)
        print(f"{'欄位':<15} {'XLS 檔案':<30} {'資料庫':<30} {'是否相同':<10}")
        print("-" * 100)
        
        fields = [
            ('所屬期間', xls['dividend_belonging_period'], db['dividend_belonging_period']),
            ('除息日期', xls['ex_dividend_date'], db['ex_dividend_date']),
            ('現金股利', f"{xls['cash_dividend']:.2f}", f"{db['cash_dividend']:.2f}"),
            ('除權日期', xls['ex_rights_date'], db['ex_rights_date']),
            ('股票股利', f"{xls['stock_dividend']:.2f}", f"{db['stock_dividend']:.2f}")
        ]
        
        for field_name, xls_val, db_val in fields:
            is_same = "✓ 相同" if xls_val == db_val else "✗ 不同"
            print(f"{field_name:<15} {xls_val:<30} {db_val:<30} {is_same:<10}")
    
    print("\n" + "⚠" * 50)
    print("⚠ 建議：請手動檢查並更正資料，暫不更新資料庫")
    print("⚠" * 50 + "\n")

def insert_dividend_data(cursor, conn, data):
    """將股利資料插入資料庫"""
    if not data:
        print("✗ 沒有資料可插入")
        return 0
    
    inserted_count = 0
    
    for row in data:
        try:
            cursor.execute('''
                INSERT INTO dividend_schedule 
                (dividend_distribution_period, dividend_belonging_period, 
                 ex_dividend_date, cash_dividend, ex_rights_date, stock_dividend)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                row['dividend_distribution_period'],
                row['dividend_belonging_period'],
                row['ex_dividend_date'],
                row['cash_dividend'],
                row['ex_rights_date'],
                row['stock_dividend']
            ))
            inserted_count += 1
        except sqlite3.IntegrityError as e:
            print(f"⚠ 資料已存在: {e}")
        except Exception as e:
            print(f"✗ 插入資料失敗: {e}")
    
    conn.commit()
    return inserted_count

def query_dividend_data(cursor, stock_id=None):
    """查詢股利資料"""
    cursor.execute('''
        SELECT dividend_distribution_period, dividend_belonging_period,
               ex_dividend_date, cash_dividend, ex_rights_date, stock_dividend
        FROM dividend_schedule
        ORDER BY dividend_distribution_period DESC
    ''')
    
    return cursor.fetchall()

def display_dividend_data(rows):
    """顯示股利資料"""
    if not rows:
        print("✗ 沒有資料")
        return
    
    print("\n" + "="*100)
    print(f"{'發放期間':<10} {'所屬期間':<10} {'除息日':<12} {'現金股利':<10} {'除權日':<12} {'股票股利':<10}")
    print("="*100)
    
    for row in rows:
        dist_period, belong_period, ex_div_date, cash_div, ex_right_date, stock_div = row
        print(f"{dist_period:<10} {belong_period:<10} {ex_div_date:<12} {cash_div:<10.2f} {ex_right_date:<12} {stock_div:<10.2f}")
    
    print("="*100 + "\n")

def database_has_data(cursor):
    """檢查資料庫是否有資料"""
    cursor.execute('SELECT COUNT(*) FROM dividend_schedule')
    count = cursor.fetchone()[0]
    return count > 0

def main():
    print("\n" + "="*100)
    print("股票股利資料庫管理工具")
    print("="*100 + "\n")
    
    # 從檔案名稱提取股票代號
    stock_id = extract_stock_id_from_filename(HTML_FILE)
    
    if not stock_id:
        print("✗ 錯誤：無法從檔案名稱中提取股票代號")
        print(f"  檔案名稱: {HTML_FILE}")
        print("  檔案名稱格式應包含 4 位數字的股票代號（例如：2881.xls）")
        return
    
    print(f"✓ 從檔案名稱中提取股票代號: {stock_id}")
    
    conn = None
    cursor = None
    
    try:
        # 建立資料庫
        conn, cursor, db_name = create_database(stock_id)
        
        print(f"正在處理股票代號: {stock_id}\n")
        
        # 解析 HTML 檔案
        print("【步驟 1】讀取 XLS 檔案...")
        dividend_data = parse_html_table(HTML_FILE)
        
        if not dividend_data:
            print("✗ 沒有資料可處理")
            return
        
        print(f"✓ 成功讀取 {len(dividend_data)} 筆資料\n")
        
        # 檢查資料庫是否有現存資料
        print("【步驟 2】檢查資料庫現存資料...")
        db_has_data = database_has_data(cursor)
        
        if not db_has_data:
            # 資料庫為空，直接插入所有資料
            print("✓ 資料庫為空，直接插入所有資料...\n")
            inserted_count = insert_dividend_data(cursor, conn, dividend_data)
            print(f"✓ 成功插入 {inserted_count} 筆資料\n")
            
            # 顯示插入的資料
            rows = query_dividend_data(cursor)
            print(f"【結果】已新增的股利資料 (股票代號: {stock_id}):")
            display_dividend_data(rows)
        else:
            # 資料庫有現存資料，進行衝突檢測
            print("✓ 資料庫中存在現有資料\n")
            
            print("【步驟 3】檢查資料一致性...\n")
            existing_data = get_existing_data(cursor)
            new_records, conflict_records = check_data_conflict(dividend_data, existing_data)
            
            # 顯示衝突資料（如果有）
            if conflict_records:
                display_conflicts(conflict_records)
                print(f"✗ 發現 {len(conflict_records)} 筆不一致的資料，已停止更新")
                print(f"   (發現 {len(new_records)} 筆新資料，但因衝突不插入)\n")
            else:
                # 沒有衝突，插入新資料
                if new_records:
                    print(f"✓ 未發現衝突，有 {len(new_records)} 筆新資料待插入\n")
                    inserted_count = insert_dividend_data(cursor, conn, new_records)
                    print(f"✓ 成功插入 {inserted_count} 筆新資料\n")
                    
                    # 顯示所有資料
                    rows = query_dividend_data(cursor)
                    print(f"【結果】更新後的股利資料 (股票代號: {stock_id}):")
                    display_dividend_data(rows)
                else:
                    print("✓ 資料庫資料與 XLS 檔案完全一致，無需更新\n")
                    
                    # 顯示現有資料
                    rows = query_dividend_data(cursor)
                    print(f"【結果】資料庫現有資料 (股票代號: {stock_id}):")
                    display_dividend_data(rows)
    
    finally:
        # 確保資料庫連線被正確關閉
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass
        print("✓ 資料庫操作完成")

if __name__ == '__main__':
    main()
