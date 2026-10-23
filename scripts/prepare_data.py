"""Prepare the UCI Online Retail workbook for the FODS dashboard.

Reads OOXML using zipfile + lxml; no Excel GUI or external service required.
Usage: python scripts/prepare_data.py --input 'online+retail.zip'
"""
from __future__ import annotations
import argparse
import csv
import gzip
import io
import json
import os
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from lxml import etree

NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
BASE=datetime(1899,12,30)
FIELDS=['invoice','stock_code','description','quantity','date','unit_price','country','sales']


def workbook_from_path(path:Path):
    if path.suffix.lower()=='.xlsx':
        return path.read_bytes()
    with zipfile.ZipFile(path) as wrapper:
        books=[x for x in wrapper.namelist() if x.lower().endswith('.xlsx')]
        if len(books)!=1:
            raise ValueError('Expected one .xlsx in the uploaded ZIP.')
        return wrapper.read(books[0])


def shared_strings(book):
    result=[]
    with book.open('xl/sharedStrings.xml') as f:
        for _,el in etree.iterparse(f,events=('end',),tag=NS+'si'):
            result.append(''.join(el.itertext()))
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
    return result


def rows(book, strings):
    with book.open('xl/worksheets/sheet1.xml') as f:
        for _,row in etree.iterparse(f,events=('end',),tag=NS+'row'):
            vals={}
            for cell in row:
                if cell.tag != NS+'c':
                    continue
                cell_ref=cell.get('r','')
                col=''.join(x for x in cell_ref if x.isalpha())
                v=cell.find(NS+'v')
                if v is None or v.text is None:
                    continue
                s=v.text
                vals[col]=strings[int(s)] if cell.get('t')=='s' else s
            yield vals
            row.clear()
            while row.getprevious() is not None:
                del row.getparent()[0]


def main(source:Path, output:Path):
    output.mkdir(parents=True,exist_ok=True)
    data=workbook_from_path(source)
    summary=Counter()
    countries=set()
    stock_codes=set()
    invoices=set()
    min_date=max_date=None
    with zipfile.ZipFile(io.BytesIO(data)) as xlsx:
        strings=shared_strings(xlsx)
        with gzip.open(output/'sales_clean.csv.gz','wt',newline='',encoding='utf-8',compresslevel=6) as out:
            writer=csv.writer(out)
            writer.writerow(FIELDS)
            for index,row in enumerate(rows(xlsx,strings)):
                if index==0:
                    continue
                summary['original_rows']+=1
                if not row.get('G'):
                    summary['missing_customer_id']+=1
                invoice=str(row.get('A','')).strip()
                stock=str(row.get('B','')).strip()
                desc=str(row.get('C','')).strip()
                country=str(row.get('H','')).strip()
                if invoice.startswith('C'):
                    summary['cancellation_coded_rows']+=1
                    continue
                try:
                    qty=int(float(row.get('D','nan')))
                    price=float(row.get('F','nan'))
                    date=BASE+timedelta(days=float(row.get('E','nan')))
                except (ValueError,OverflowError,TypeError):
                    summary['missing_or_invalid_numeric_date']+=1
                    continue
                if qty<=0:
                    summary['nonpositive_quantity_rows']+=1
                    continue
                if price<=0:
                    summary['nonpositive_price_rows']+=1
                    continue
                if not stock or not desc or not invoice or not country:
                    summary['missing_essential_field_rows']+=1
                    continue
                writer.writerow([invoice,stock,desc,qty,date.strftime('%Y-%m-%d %H:%M:%S'),f'{price:.4f}',country, f'{qty*price:.4f}'])
                summary['included_rows']+=1
                countries.add(country)
                stock_codes.add(stock)
                invoices.add(invoice)
                iso=date.isoformat()
                min_date=min(min_date,iso) if min_date else iso
                max_date=max(max_date,iso) if max_date else iso
    report={**summary,
            'distinct_countries_clean':len(countries),
            'distinct_products_clean':len(stock_codes),
            'distinct_orders_clean':len(invoices),
            'first_date_clean':min_date,
            'last_date_clean':max_date,
            'cleaning_policy':[
                'Keep all valid positive-quantity, positive-price invoice lines with product and country fields.',
                'Exclude cancellation-coded invoices (InvoiceNo beginning with C) from positive-sales analysis.',
                'Do not discard sales records merely because CustomerID is missing.',
                'Do not automatically drop exact duplicate-looking lines, since no unique line-item identifier is provided.',
                'Sales = Quantity multiplied by UnitPrice, in GBP; it is not profit.',
            ]}
    (output/'quality_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    args=parser.parse_args()
    main(args.input,args.out)
