"""Exercise app branches with a minimal mock frontend when Streamlit isn't installed.
This catches app/data/chart exceptions; it is NOT a visual Streamlit render test.
"""
import contextlib
import importlib
import runpy
import sys
import types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class Node:
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def metric(self,*a,**k): pass
    def write(self,*a,**k): pass
    def caption(self,*a,**k): pass
    def markdown(self,*a,**k): pass
    def subheader(self,*a,**k): pass
    def info(self,*a,**k): pass

class FakeStreamlit(types.ModuleType):
    def __init__(self,page):
        super().__init__('streamlit');self.page=page;self.sidebar=Node()
        self.cache_data=self.cache
    def cache(self,*args,**kwargs):
        if args and callable(args[0]): return args[0]
        return lambda fn:fn
    def set_page_config(self,*a,**k): pass
    def markdown(self,*a,**k): pass
    def caption(self,*a,**k): pass
    def divider(self,*a,**k): pass
    def link_button(self,*a,**k): pass
    def radio(self,label,items,**k): return items[self.page]
    def date_input(self,label,value,**k): return value
    def selectbox(self,label,options,**k): return options[0]
    def columns(self,spec,*a,**k): return [Node() for _ in range(spec if isinstance(spec,int) else len(spec))]
    def metric(self,*a,**k): pass
    def plotly_chart(self,fig,*a,**k):
        assert len(fig.data)>0
    def dataframe(self,*a,**k): pass
    def subheader(self,*a,**k): pass
    def info(self,*a,**k): pass
    def warning(self,*a,**k): pass
    def success(self,*a,**k): pass
    def write(self,*a,**k): pass
    def stop(self): raise RuntimeError('st.stop was called')
    def expander(self,*a,**k): return Node()
    def container(self,*a,**k): return Node()
    def download_button(self,*a,**k): pass

for p in range(4):
    sys.modules['streamlit']=FakeStreamlit(p)
    runpy.run_path(str(ROOT/'app.py'),run_name='__main__')
    print('PASS page',p+1)
