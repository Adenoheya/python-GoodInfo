import sqlite3
from tabulate import tabulate
import os

DATABASE_DIR = 'database'  # 資料庫目錄

def get_connection(stock_id):
    """取得資料庫連線"""
    db_name = f'{stock_id}.db'
    db_path = os.path.join(DATABASE_DIR, db_name)  # 完整路徑
    return sqlite3.connect(db_path, timeout=10.0, check_same_thread=False, isolation_level=None)

def query_all(stock_id):
    """查詢所有股利資料"""
    conn = get_connection(stock_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT dividend_distribution_period, dividend_belonging_period,
               ex_dividend_date, cash_dividend, ex_rights_date, stock_dividend
        FROM dividend_schedule
        ORDER BY dividend_distribution_period DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def get_statistics(stock_id):
    """取得股票的股利統計資訊"""
    conn = get_connection(stock_id)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as total_records,
            SUM(cash_dividend) as total_cash_dividend,
            AVG(cash_dividend) as avg_cash_dividend,
            SUM(stock_dividend) as total_stock_dividend,
            AVG(stock_dividend) as avg_stock_dividend,
            MAX(cash_dividend) as max_cash_dividend,
            MIN(cash_dividend) as min_cash_dividend
        FROM dividend_schedule
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def display_table(rows, headers=None):
    """顯示表格"""
    if not rows:
        print("✗ 沒有資料")
        return
    
    if headers is None:
        headers = ['發放期間', '所屬期間', '除息日', '現金股利', '除權日', '股票股利']
    
    # 轉換為列表以供 tabulate 使用
    data = []
    for row in rows:
        data.append(list(row))
    
    print("\n" + tabulate(data, headers=headers, tablefmt='grid', floatfmt='.2f'))

def main():
    print("\n" + "="*100)
    print("股票股利資料庫查詢工具")
    print("="*100 + "\n")
    
    # 股票代號
    stock_id = '2881'
    
    # 查詢所有資料
    print(f"【股票代號 {stock_id} 的股利資料】")
    all_data = query_all(stock_id)
    display_table(all_data)
    
    # 統計資訊
    print(f"\n【股票代號 {stock_id} 的統計資訊】")
    stats = get_statistics(stock_id)
    if stats:
        total, cash_sum, cash_avg, stock_sum, stock_avg, max_cash, min_cash = stats
        print(f"  記錄筆數:      {total}")
        print(f"  現金股利總額:  {cash_sum:.2f}")
        print(f"  現金股利平均:  {cash_avg:.2f}")
        print(f"  最高現金股利:  {max_cash:.2f}")
        print(f"  最低現金股利:  {min_cash:.2f}")
        print(f"  股票股利總額:  {stock_sum:.2f}")
        print(f"  股票股利平均:  {stock_avg:.2f}")
    
    print("\n" + "="*100)

if __name__ == '__main__':
    main()
